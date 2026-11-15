import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
import pandas as pd
from kurra import demo
from kurra.config import Tolerances
from kurra.optimizer import Party, generate_plan, assign_units
from kurra.rules import evaluate
from shapely.geometry import box


def _parties():
    d = demo.demo_entitlements()
    tot = d.entitlement_sqm.sum()
    return [Party(str(i), r.name, r.entitlement_sqm / tot) for i, r in enumerate(d.itertuples())]


def test_all_strategies_hit_shares():
    plot = demo.demo_plot()
    road, zones = demo.demo_layers(plot)
    P = _parties()
    for strat in ("compact", "frontage", "road_parallel"):
        lots, _ = generate_plan(plot, P, zones, strat, road)
        res = {r.code: r for r in evaluate(lots, P, plot, zones, road)}
        assert res["a"].status == "green", (strat, res["a"].metric)
        assert abs(sum(g.area for g in lots.values()) - plot.area) < 1e-3


def test_whole_fields_then_rebalance():
    plot = box(0, 0, 60, 60)
    units = {f"f{i}": box(10 * i, 0, 10 * i + 10, 60) for i in range(6)}
    P = [Party("a", "A", 0.5), Party("b", "B", 0.3), Party("c", "C", 0.2)]
    lots, _ = generate_plan(plot, P, [], "compact", None, units)
    res = {r.code: r for r in evaluate(lots, P, plot, [], None, None, None, units)}
    assert res["a"].status == "green", res["a"].metric


def test_cpsat():
    a = assign_units({"x": 50, "y": 30, "z": 20}, {"p": 50, "q": 50})
    assert sorted(a.values()) == ["p", "q", "q"] or sorted(a.values()) == ["p", "p", "q"]
