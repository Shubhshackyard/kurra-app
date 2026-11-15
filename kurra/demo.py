"""Demo parcel in Jalaun / Auraiya so the app can also run offline."""
import math
import pandas as pd
from pathlib import Path
from shapely.geometry import Polygon, LineString, box
from shapely.affinity import scale, translate

ORIGIN = (346750.0, 2876330.0)


def demo_plot(area_sqm: float = 2750.0):
    p = Polygon([(0, 0), (26, 0), (25, 146), (1, 148)])
    p = scale(p, math.sqrt(area_sqm / p.area), math.sqrt(area_sqm / p.area), origin=(0, 0))
    return translate(p, *ORIGIN)


def demo_layers(plot):
    minx, miny, maxx, maxy = plot.bounds
    # road runs along the plot's south edge (two lowest vertices), extended both ways
    pts = sorted(list(plot.exterior.coords)[:-1], key=lambda c: c[1])[:2]
    (x1, y1), (x2, y2) = sorted(pts)
    ux, uy = x2 - x1, y2 - y1
    L = math.hypot(ux, uy)
    ux, uy = ux / L, uy / L
    road = LineString([(x1 - 20 * ux, y1 - 20 * uy - 0.2), (x2 + 20 * ux, y2 + 20 * uy - 0.2)])
    low = box(minx - 5, miny + 0.62 * (maxy - miny), maxx + 5, maxy + 5)   # inferior, low-lying north
    zones = [(low.intersection(plot.buffer(1)), 0.8)]
    return road, zones


def demo_entitlements():
    jalaun_csv = Path(__file__).parent.parent / "data" / "entitlements_plot2_khata54_jalaun.csv"
    if jalaun_csv.exists():
        return pd.read_csv(jalaun_csv)
    return pd.read_csv(Path(__file__).parent.parent / "data" / "entitlements_plot352_khata279.csv")
