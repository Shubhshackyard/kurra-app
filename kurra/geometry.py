"""Geometry primitives. All areas/lengths are in metres (projected CRS)."""
from __future__ import annotations
import math
import numpy as np
import shapely
from shapely.geometry import Polygon, MultiPolygon, GeometryCollection, LineString
from shapely.ops import unary_union


def clean(g):
    """Keep only polygonal parts, repair, drop dust."""
    if g is None or g.is_empty:
        return Polygon()
    if not g.is_valid:
        g = shapely.make_valid(g)
    g = g.buffer(0)
    if isinstance(g, GeometryCollection) and not isinstance(g, (Polygon, MultiPolygon)):
        polys = [x for x in g.geoms if isinstance(x, (Polygon, MultiPolygon)) and x.area > 1e-6]
        g = unary_union(polys) if polys else Polygon()
    if isinstance(g, MultiPolygon):
        parts = [p for p in g.geoms if p.area > 1e-4]
        g = unary_union(parts) if parts else Polygon()
    return g


def n_parts(g) -> int:
    if g.is_empty:
        return 0
    return len(g.geoms) if hasattr(g, "geoms") else 1


def iso_ratio(g) -> float:
    """perimeter^2 / (4*pi*area). 1.0 = circle, ~1.27 = square, large = ragged/sliver."""
    if g.is_empty or g.area <= 0:
        return float("inf")
    return g.length ** 2 / (4 * math.pi * g.area)


def polsby_popper(g) -> float:
    r = iso_ratio(g)
    return 0.0 if math.isinf(r) else 1.0 / r


def min_width(g) -> float:
    """Short side of the minimum rotated rectangle (a robust proxy for lot width)."""
    if g.is_empty:
        return 0.0
    rect = g.minimum_rotated_rectangle
    if rect.geom_type != "Polygon":
        return 0.0
    xs, ys = rect.exterior.coords.xy
    sides = [math.hypot(xs[i + 1] - xs[i], ys[i + 1] - ys[i]) for i in range(2)]
    return min(sides)


def value_of(g, zones) -> float:
    """Quality-weighted area. zones = [(polygon, multiplier), ...] in priority order;
    land outside every zone has multiplier 1.0."""
    if g.is_empty:
        return 0.0
    if not g.is_valid:
        g = clean(g)
    total, rest = 0.0, g
    for z, m in zones:
        if rest.is_empty:
            break
        part = rest.intersection(z)
        if not part.is_empty:
            total += part.area * m
            rest = rest.difference(z)
    return total + (0.0 if rest.is_empty else rest.area)


def half_plane_piece(g, theta_deg: float, t: float):
    """g ∩ {p : n·p <= t}, with n = (cos θ, sin θ). Geometry must be in local coordinates."""
    th = math.radians(theta_deg)
    n = (math.cos(th), math.sin(th))
    d = (-n[1], n[0])
    minx, miny, maxx, maxy = g.bounds
    R = 4 * max(maxx - minx, maxy - miny, 1.0) + abs(t) + 10
    p0 = (n[0] * t, n[1] * t)
    pts = [
        (p0[0] + d[0] * R, p0[1] + d[1] * R),
        (p0[0] - d[0] * R, p0[1] - d[1] * R),
        (p0[0] - d[0] * R - n[0] * 2 * R, p0[1] - d[1] * R - n[1] * 2 * R),
        (p0[0] + d[0] * R - n[0] * 2 * R, p0[1] + d[1] * R - n[1] * 2 * R),
    ]
    return clean(g.intersection(Polygon(pts)))


def cut_by_value(g, theta_deg: float, fraction: float, zones, iters: int = 42):
    """Cut g with a straight line (normal at theta) so the 'left' piece holds `fraction`
    of g's quality-weighted value. Returns (left, right). Monotone -> bisection."""
    th = math.radians(theta_deg)
    n = np.array([math.cos(th), math.sin(th)])
    coords = shapely.get_coordinates(g)
    proj = coords @ n
    lo, hi = float(proj.min()), float(proj.max())
    target = fraction * value_of(g, zones)
    for _ in range(iters):
        mid = (lo + hi) / 2
        if value_of(half_plane_piece(g, theta_deg, mid), zones) < target:
            lo = mid
        else:
            hi = mid
    t = (lo + hi) / 2
    left = half_plane_piece(g, theta_deg, t)
    right = clean(g.difference(left))
    return left, right


def is_connected(g) -> bool:
    """Hard connectivity check: verifies lot is a single continuous polygon."""
    if g is None or g.is_empty:
        return False
    if g.geom_type == "Polygon":
        return True
    if g.geom_type == "MultiPolygon":
        # Only true if there is exactly 1 significant part (rest is microscopic numerical dust)
        sig_parts = [p for p in g.geoms if p.area > 0.05]
        return len(sig_parts) == 1
    return False


def overlap_percentage(g1, g2) -> float:
    """Compute percentage possession/scheme overlap between two geometries."""
    if g1 is None or g2 is None or g1.is_empty or g2.is_empty:
        return 0.0
    inter = g1.intersection(g2)
    base = min(g1.area, g2.area)
    if base <= 0:
        return 0.0
    return round((inter.area / base) * 100.0, 2)


def aspect_ratio(g) -> float:
    """Compute length to width aspect ratio of minimum rotated bounding box."""
    if g.is_empty:
        return 1.0
    rect = g.minimum_rotated_rectangle
    if rect.geom_type != "Polygon":
        return 1.0
    xs, ys = rect.exterior.coords.xy
    sides = [math.hypot(xs[i + 1] - xs[i], ys[i + 1] - ys[i]) for i in range(2)]
    w = min(sides)
    l = max(sides)
    return round(l / max(w, 1e-6), 2)


def road_angle_deg(road, plot) -> float | None:
    """Direction (degrees) of the road segment nearest to the plot."""
    if road is None or road.is_empty:
        return None
    # Convert Polygon / MultiPolygon to boundaries if parcel geometry is passed
    if hasattr(road, "geom_type") and road.geom_type in ("Polygon", "MultiPolygon"):
        road = road.boundary
    lines = list(road.geoms) if hasattr(road, "geoms") else [road]
    best, best_d = None, 1e18
    for ln in lines:
        if not hasattr(ln, "coords"):
            continue
        c = list(ln.coords)
        for a, b in zip(c[:-1], c[1:]):
            seg = LineString([a, b])
            dist = seg.distance(plot)
            if dist < best_d:
                best_d, best = dist, (a, b)
    if best is None:
        return None
    (x1, y1), (x2, y2) = best
    return math.degrees(math.atan2(y2 - y1, x2 - x1)) % 360

