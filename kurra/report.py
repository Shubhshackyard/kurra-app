"""Hindi kurra pack (draft). Deterministic templates — no generative text in the compliance path."""
from __future__ import annotations
import json
from datetime import date, timedelta
import pandas as pd
from shapely.geometry import mapping
from shapely.ops import transform

from .config import PROJECTED_EPSG
from .geometry import value_of
from .rules import ICON

STATUS_HI = {"green": "अनुपालित", "amber": "आंशिक", "red": "अनुपालित नहीं", "na": "लागू नहीं / डेटा नहीं"}


def lots_table(lots, parties, plot, zones=()):
    zones = list(zones)
    tv = value_of(plot, zones)
    rows = []
    for p in parties:
        g = lots[p.id]
        rows.append({"हिस्सेदार": p.name, "देय अंश (%)": round(p.share * 100, 3),
                     "देय क्षेत्रफल (वर्गमी)": round(p.share * plot.area, 2),
                     "आवंटित क्षेत्रफल (वर्गमी)": round(g.area, 2),
                     "आवंटित मूल्य अंश (%)": round(100 * value_of(g, zones) / tv, 3),
                     "भाग (संख्या)": len(g.geoms) if hasattr(g, "geoms") else 1})
    return pd.DataFrame(rows)


def kurra_markdown(meta: dict, table: pd.DataFrame, results, plan_name: str,
                   order_date: date | str | None = None) -> str:
    if isinstance(order_date, str):
        try:
            order_date = date.fromisoformat(order_date)
        except Exception:
            order_date = None
    due = (order_date + timedelta(days=30)).strftime("%d-%m-%Y") if order_date else "—"
    L = [f"# कुर्रा (लॉट आवंटन) प्रारूप — नियम 109(5)",
         f"**जनपद:** {meta['district']}  |  **तहसील:** {meta['tehsil']}  |  **ग्राम:** {meta['village']}  |  **गाटा संख्या:** {meta['plot']}",
         f"**क्षेत्रफल (मानचित्र):** {meta['area_sqm']:.2f} वर्गमी  |  **प्रस्तावित योजना:** {plan_name}",
         f"**आदेश की तिथि:** {order_date.strftime('%d-%m-%Y') if order_date else '—'}  |  **लेखपाल रिपोर्ट की अंतिम तिथि (एक माह):** {due}", "",
         "## आवंटन तालिका", table.to_markdown(index=False), "",
         "## नियम-वार अनुपालन", "| खंड | विषय | स्थिति | मापन |", "|---|---|---|---|"]
    for r in results:
        L.append(f"| {r.code} | {r.name_hi} | {ICON[r.status]} {STATUS_HI[r.status]} | {r.metric} |")
    L += ["", "> यह सह-खातेदारों/ऐप द्वारा तैयार **प्रारूप प्रस्ताव** है। कुर्रा का अंतिम अनुमोदन "
          "लेखपाल/राजस्व न्यायालय द्वारा स्थल-सत्यापन के पश्चात ही होगा।",
          "", "**सहमति हस्ताक्षर (OTP/eSign):** ______________________"]
    return "\n".join(L)


def lots_geojson(lots, parties, to_wgs84: bool = True) -> str:
    tf = None
    if to_wgs84:
        try:
            from pyproj import Transformer
            t = Transformer.from_crs(PROJECTED_EPSG, 4326, always_xy=True)
            tf = lambda g: transform(t.transform, g)  # noqa: E731
        except Exception:
            tf = None
    feats = [{"type": "Feature", "properties": {"party": p.name, "share": p.share,
              "area_sqm": round(lots[p.id].area, 3)},
              "geometry": mapping(tf(lots[p.id]) if tf else lots[p.id])} for p in parties]
    return json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False)
