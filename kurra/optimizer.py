"""Plan generation.

Method (deterministic, no ML in the decision path):
  1. Whole-unit assignment (existing fields) with OR-Tools CP-SAT — minimises share deviation.
  2. Strip transfer to close the remaining gaps (cuts only where needed to meet the share).
  3. For the free land: weighted recursive bisection (Even–Paz style, generalised to unequal
     entitlements and quality-weighted value). Cut angle is scanned for the most compact result.
Possession / family-settlement polygons are locked first and deducted from each party's share.
"""
from __future__ import annotations
import math
import random
from dataclasses import dataclass
from datetime import datetime
from shapely.geometry import Point, LineString
from shapely.affinity import translate
from shapely.ops import unary_union

from .geometry import (clean, cut_by_value, iso_ratio, n_parts, road_angle_deg, value_of)


@dataclass
class Party:
    id: str
    name: str
    share: float                 # fraction of the plot, sums to 1 across parties
    anchor: tuple | None = None  # preferred location (x, y) — a proposal, not a right
    locked: object | None = None # possession / settlement geometry already allotted


# ---------------------------------------------------------------- bisection ----
def _cost(g) -> float:
    return iso_ratio(g) + 4.0 * max(n_parts(g) - 1, 0)


def _bisect(free, items, zones, angles):
    """items: list of (party_id, weight, anchor_xy). Returns {party_id: geometry}."""
    if len(items) == 1:
        return {items[0][0]: free}
    total_w = sum(w for _, w, _ in items)
    best = None
    for th in angles:
        n = (math.cos(math.radians(th)), math.sin(math.radians(th)))
        order = sorted(items, key=lambda it: n[0] * it[2][0] + n[1] * it[2][1])
        k = min(range(1, len(order)),
                key=lambda j: abs(sum(w for _, w, _ in order[:j]) - total_w / 2))
        wl = sum(w for _, w, _ in order[:k])
        left, right = cut_by_value(free, th, wl / total_w, zones)
        if left.is_empty or right.is_empty:
            continue
        c = _cost(left) + _cost(right)
        if best is None or c < best[0]:
            best = (c, order[:k], order[k:], left, right)
    if best is None:  # degenerate geometry: hand everything to the first party
        out = {items[0][0]: free}
        out.update({i[0]: clean(free.buffer(0).intersection(free).buffer(0)) for i in items[1:]})
        return out
    _, lo, hi, left, right = best
    out = _bisect(left, lo, zones, angles)
    out.update(_bisect(right, hi, zones, angles))
    return out


# ---------------------------------------------------------- whole-unit CP-SAT ----
def assign_units(unit_values: dict, targets: dict, scale: int = 1000, seconds: float = 10.0, seed: int = 7):
    """Assign each existing field (unit) wholly to one party, minimising MAX relative deviation."""
    from ortools.sat.python import cp_model
    m = cp_model.CpModel()
    U, P = list(unit_values), list(targets)
    x = {(u, p): m.NewBoolVar(f"x_{u}_{p}") for u in U for p in P}
    for u in U:
        m.AddExactlyOne(x[u, p] for p in P)
    big = int(round(sum(unit_values.values()) * scale)) + 1
    devs = []
    max_dev = m.NewIntVar(0, big, "max_dev")

    for p in P:
        got = sum(int(round(unit_values[u] * scale)) * x[u, p] for u in U)
        tgt = int(round(targets[p] * scale))
        d = m.NewIntVar(0, big, f"d_{p}")
        m.Add(got - tgt <= d)
        m.Add(tgt - got <= d)
        m.Add(d <= max_dev)
        devs.append(d)

    # Primary objective: minimise max deviation; secondary tie-breaker: sum of deviations
    m.Minimize(max_dev * 1000 + sum(devs))

    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = seconds
    s.parameters.num_workers = 4
    s.parameters.random_seed = seed
    status = s.Solve(m)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("CP-SAT found no whole-unit assignment")
    return {u: next(p for p in P if s.Value(x[u, p])) for u in U}



def _rebalance(lots, targets, zones, angles, tol_rel=0.005, max_iter=60):
    """Close residual gaps by cutting a strip from a surplus party's piece next to the deficit party."""
    for _ in range(max_iter):
        val = {p: value_of(g, zones) for p, g in lots.items()}
        gap = {p: val[p] - targets[p] for p in lots}
        s = max(gap, key=gap.get)
        d = min(gap, key=gap.get)
        amount = min(gap[s], -gap[d])
        if amount <= tol_rel * max(targets[d], 1e-9) or gap[s] <= 0 or gap[d] >= 0:
            break
        src_parts = list(lots[s].geoms) if hasattr(lots[s], "geoms") else [lots[s]]
        dest = lots[d] if not lots[d].is_empty else None
        ref = dest.centroid if dest is not None else lots[s].centroid
        piece = min(src_parts, key=lambda g: g.distance(ref))
        pv = value_of(piece, zones)
        if amount >= pv * 0.999:                       # move the whole piece
            move, keep = piece, None
        else:
            best = None
            for th in angles:
                sub, rest = cut_by_value(piece, th, amount / pv, zones)
                if sub.is_empty or rest.is_empty:
                    continue
                near = sub.distance(dest) if dest is not None else sub.distance(ref)
                c = _cost(sub) + _cost(rest) + 3.0 * near / math.sqrt(max(sub.area, 1.0))
                if best is None or c < best[0]:
                    best = (c, sub, rest)
            if best is None:
                break
            _, move, keep = best
        rest_s = [g for g in src_parts if g is not piece]
        if keep is not None:
            rest_s.append(keep)
        lots[s] = clean(unary_union(rest_s)) if rest_s else clean(lots[s].difference(move))
        lots[d] = clean(unary_union([lots[d], move])) if not lots[d].is_empty else move
    return lots


# ------------------------------------------------------------------ driver ----
def _shift(g, dx, dy):
    return translate(g, dx, dy) if g is not None and not g.is_empty else g


def generate_plan(plot, parties, zones=(), strategy="compact", road=None,
                  units=None, seed=0, shared_path_width: float | None = None):
    """Return (lots: {party_id: geometry}, meta). Geometries stay in the input CRS."""
    zones = list(zones)
    c = plot.centroid
    dx, dy = -c.x, -c.y
    P = _shift(plot, dx, dy)
    Z = [(_shift(z, dx, dy), m) for z, m in zones]
    R = _shift(road, dx, dy) if road is not None else None

    # Handle Optional Shared Pathway (साझा रास्ता)
    shared_path_poly = None
    if shared_path_width and shared_path_width > 0 and R is not None and not R.is_empty:
        # Buffer road towards plot centroid to carve pathway
        road_touch = P.intersection(R.buffer(1.0))
        if not road_touch.is_empty:
            path_line = LineString([road_touch.centroid, P.centroid])
            shared_path_poly = clean(path_line.buffer(shared_path_width / 2.0).intersection(P))
            if not shared_path_poly.is_empty:
                P = clean(P.difference(shared_path_poly))

    total_v = value_of(P, Z)
    targets = {p.id: p.share * total_v for p in parties}

    # strategy -> cut angles
    ra = road_angle_deg(R, P) if R is not None else None
    if strategy == "frontage" and ra is not None:
        angles = [ra % 360, (ra + 180) % 360]       # cut lines ⟂ road: every lot touches the road
    elif strategy == "road_parallel" and ra is not None:
        angles = [(ra + 90) % 360, (ra + 270) % 360]  # cut lines ∥ road: stacked rows
    else:
        angles = list(range(0, 360, 15))

    rng = random.Random(seed)
    ext = max(P.bounds[2] - P.bounds[0], P.bounds[3] - P.bounds[1])

    locked = {}
    for p in parties:
        if p.locked is not None and not p.locked.is_empty:
            locked[p.id] = clean(_shift(p.locked, dx, dy).intersection(P))
    free = clean(P.difference(unary_union(list(locked.values())))) if locked else P

    # 1-2. whole fields first
    lots = {}
    if units:
        U = {}
        for uid, g in units.items():
            piece = clean(_shift(g, dx, dy).intersection(free))
            if piece.area > 1e-3:
                U[uid] = piece
        rem = {p.id: max(targets[p.id] - value_of(locked.get(p.id, free.buffer(0).difference(free)), Z), 0.0)
               for p in parties}
        assign = assign_units({u: value_of(g, Z) for u, g in U.items()}, rem, seed=seed)
        for p in parties:
            mine = [U[u] for u, q in assign.items() if q == p.id]
            lots[p.id] = clean(unary_union(mine)) if mine else clean(P.difference(P))
        leftover = clean(free.difference(unary_union(list(U.values())))) if U else free
        lots = _rebalance(lots, rem, Z, angles)
        if not leftover.is_empty and leftover.area > 1.0:   # unassigned land outside fields
            lots[parties[0].id] = clean(unary_union([lots[parties[0].id], leftover]))
            lots = _rebalance(lots, rem, Z, angles)
    else:
        items = []
        for p in parties:
            need = max(targets[p.id] - value_of(locked.get(p.id, P.difference(P)), Z), 0.0)
            if need <= 1e-6:
                continue
            if p.anchor is not None:
                a = (p.anchor[0] + dx, p.anchor[1] + dy)
            elif p.id in locked and not locked[p.id].is_empty:
                a = (locked[p.id].centroid.x, locked[p.id].centroid.y)
            else:
                a = (rng.uniform(-0.3, 0.3) * ext, rng.uniform(-0.3, 0.3) * ext)
            items.append((p.id, need, a))
        lots = _bisect(free, items, Z, angles) if items else {}
        for p in parties:
            lots.setdefault(p.id, P.difference(P))

    for pid, g in locked.items():
        lots[pid] = clean(unary_union([lots[pid], g]))
    # shifting back to ~1e6-magnitude UTM coordinates can leave float-noise self-intersections
    lots = {pid: clean(_shift(g, -dx, -dy)) for pid, g in lots.items()}

    unsh_path = clean(_shift(shared_path_poly, -dx, -dy)) if shared_path_poly else None

    provenance = {
        "engine_version": "2.0.0",
        "strategy": strategy,
        "seed": seed,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "angles": angles,
        "shared_pathway": {
            "enabled": unsh_path is not None,
            "width_m": shared_path_width if unsh_path else 0.0,
            "area_sqm": unsh_path.area if unsh_path else 0.0,
            "notice": "साझा रास्ता (Needs court direction / party consent)" if unsh_path else ""
        },
        "parties_inputs": [{"id": p.id, "name": p.name, "share": p.share} for p in parties]
    }
    if unsh_path is not None:
        lots["_shared_pathway"] = unsh_path

    return lots, provenance

