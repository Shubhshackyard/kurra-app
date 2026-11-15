import io
import json
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from shapely.geometry import shape, Point, box
from shapely.ops import unary_union

from kurra.village_map import generate_village_map_html
from kurra.workflow import CadastralWorkflow

from kurra import demo, report
from kurra.bhunaksha import BhunakshaClient, BhunakshaError, find_geometry
from kurra.config import DEFAULT_LOCATION, Tolerances
from kurra.geometry import clean
from kurra.optimizer import Party, generate_plan
from kurra.records import parse_orders, reconcile
from kurra.rules import ICON, evaluate, rank_key

st.set_page_config(page_title="Kurra planner — Rule 109(5)", layout="wide")
st.title("Kurra planner — draft lot allotment under Rule 109(5)")
st.caption("Proposals only: approval stays with the Lekhpal / revenue court. "
           "Compliance is computed deterministically; no AI decides it.")

S = st.session_state
loc = DEFAULT_LOCATION

# ------------------------------------------------------------------ sidebar ----
with st.sidebar:
    st.header("1 · Select parcel")
    st.text_input("District", f"{loc['district'][0]} {loc['district'][1]}", disabled=True)
    st.text_input("Tehsil", f"{loc['tehsil'][0]} {loc['tehsil'][1]}", disabled=True)
    st.text_input("Village", f"{loc['village'][0]} {loc['village'][1]}", disabled=True)
    plot_no = st.text_input("Plot no.", loc["plot"])
    record_area = st.number_input("Record area (sq m) — from khatauni", 0.0, 1e7, float(S.get("record_area", 2750.0)), 1.0)
    source = st.radio("Geometry source", [
        "🛰️ UP भू-नक्शा WMS व GIS (गाँव 151769 - Official)",
        "Demo (synthetic)",
        "Upload GeoJSON"
    ])
    if source.startswith("🛰️"):
        curr_gis = loc["village"][0]
        wf_key = f"wf_{curr_gis}_{plot_no}"
        if wf_key not in S:
            with st.spinner(f"गाटा {plot_no} भू-नक्शा WMS व भू-सर्वेक्षण डेटा लोड हो रहा है..."):
                wf = CadastralWorkflow(gis_code=curr_gis, plot_no=str(plot_no))
                try:
                    wf.fetch_plot_assets(dpi=300)
                    wf.analyze_plot()
                except Exception:
                    pass
                S[wf_key] = wf
        wf = S[wf_key]
        if wf and wf.plot_geom and not wf.plot_geom.is_empty:
            S.plot = clean(wf.plot_geom)
            S.giscode = curr_gis
            S.road = wf.roads_geom
            if wf.record_area_sqm:
                S.record_area = float(wf.record_area_sqm)
            S.wf = wf
        S.src = "wms_gis"
    elif source == "Upload GeoJSON":
        up = st.file_uploader("Plot polygon (projected metres, e.g. EPSG:32644)", type=["geojson", "json"])
        if up:
            S.plot = clean(find_geometry(json.load(up)))
            S.road, S.zones = None, []
        S.src = "upload"
    else:
        if S.get("src") != "demo" or "plot" not in S:
            S.plot = demo.demo_plot(record_area)
            S.road, S.zones = demo.demo_layers(S.plot)
        S.src = "demo"
    st.header("Tolerances")
    tol = Tolerances(
        share_tol=st.slider("Share tolerance (a)", 0.0, 0.10, 0.02, 0.005),
        min_width_m=st.slider("Min lot width (m)", 1.0, 15.0, 4.0, 0.5),
        min_compactness=st.slider("Compactness threshold (b)", 0.1, 0.8, 0.35, 0.05),
        frontage_tol=st.slider("Frontage tolerance (f)", 0.1, 1.0, 0.35, 0.05))

if "plot" not in S or S.plot is None or S.plot.is_empty:
    st.info("Choose a geometry source in the sidebar.")
    st.stop()
plot = S.plot
roads, zones = S.get("road"), S.get("zones", [])


def fig_of(lots=None, parties=None, show_context=True):
    f = go.Figure()

    def add(g, name, fill, line="#222", w=1.5, opacity=0.7, dash=None):
        for part in (g.geoms if hasattr(g, "geoms") else [g]):
            if part.is_empty:
                continue
            x, y = part.exterior.xy
            line_dict = dict(color=line, width=w)
            if dash:
                line_dict["dash"] = dash
            f.add_trace(go.Scatter(x=list(x), y=list(y), mode="lines", fill="toself", name=name,
                                   fillcolor=fill, line=line_dict, opacity=opacity,
                                   hoverinfo="name", showlegend=False))

    # 1. Nearby village cadastral plots (context)
    if show_context:
        village_file = Path(__file__).parent / "data" / "jalaun_151769" / "all_plots_151769_utm.geojson"
        if village_file.exists():
            try:
                with open(village_file, encoding="utf-8") as jf:
                    vdata = json.load(jf)
                for feat in vdata.get("features", []):
                    p_no = str(feat["properties"].get("plot_no", ""))
                    if p_no == str(plot_no):
                        continue
                    p_poly = shape(feat["geometry"])
                    if p_poly.distance(plot) < 130.0:
                        dx = p_poly.bounds[2] - p_poly.bounds[0]
                        dy = p_poly.bounds[3] - p_poly.bounds[1]
                        if not feat["properties"].get("is_exact_polygon", True) and (dx > 300 or dy > 300):
                            continue
                        lc = feat["properties"].get("land_class", "")
                        is_path = "मार्ग" in lc or "रास्ता" in lc or "सड़क" in lc
                        is_water = "नाली" in lc or "तालाब" in lc
                        if is_path:
                            fill_col, line_col, lw = "rgba(234, 88, 12, 0.15)", "#ea580c", 1.4
                        elif is_water:
                            fill_col, line_col, lw = "rgba(2, 132, 199, 0.15)", "#0284c7", 1.4
                        else:
                            fill_col, line_col, lw = "rgba(148, 163, 184, 0.08)", "#94a3b8", 1.0
                        add(p_poly, f"गाटा {p_no} ({lc})", fill_col, line_col, lw, 0.65)
                        cp = p_poly.representative_point()
                        label_col = "#ea580c" if is_path else ("#0284c7" if is_water else "#64748b")
                        f.add_annotation(x=cp.x, y=cp.y, text=p_no, showarrow=False,
                                         font=dict(color=label_col, size=10))
            except Exception:
                pass

    # 2. Main target plot
    # Official Cadastral Bounding Box (dashed envelope reference)
    p_minx, p_miny, p_maxx, p_maxy = plot.bounds
    add(box(p_minx, p_miny, p_maxx, p_maxy), f"गाटा {plot_no} सीमा बॉक्स (BBox)",
        "rgba(0,0,0,0)", "#3b82f6", 1.2, 0.65, dash="dot")

    if lots is None:
        add(plot, f"गाटा {plot_no}", "rgba(59, 130, 246, 0.25)", "#2563eb", 3.0, 1.0)
        c = plot.representative_point()
        f.add_annotation(
            x=c.x, y=c.y,
            text=f"<b>गाटा {plot_no}</b><br>{plot.area:,.1f} m²",
            showarrow=False,
            font=dict(color="#1e3a8a", size=13),
            bgcolor="rgba(255, 255, 255, 0.95)",
            bordercolor="#2563eb",
            borderwidth=1.5,
            borderpad=6
        )
    else:
        add(plot, f"गाटा {plot_no}", "rgba(0,0,0,0)", "#0f172a", 3.0, 1.0)

    # 3. Quality Zones
    for z, m in zones:
        add(z.intersection(plot), f"गुणवत्ता ×{m}", "rgba(217, 119, 6, 0.25)", "#d97706", 1.5, 0.8)

    # 4. Lots (Partitioned)
    if lots:
        pal = ["#3b82f6", "#f97316", "#10b981", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6", "#f59e0b",
               "#6366f1", "#84cc16", "#06b6d4", "#a855f7", "#64748b"]
        for i, p in enumerate(parties):
            add(lots[p.id], f"{p.name} — {lots[p.id].area:,.1f} m²", pal[i % len(pal)], "#ffffff", 2.0, 0.85)
            c = lots[p.id].representative_point()
            f.add_annotation(x=c.x, y=c.y, text=f"<b>{i + 1}</b>", showarrow=False,
                             font=dict(color="#ffffff", size=12), bgcolor="rgba(15, 23, 42, 0.65)",
                             borderpad=4)

    # 5. Roads
    if roads is not None and not roads.is_empty:
        road_lines = []
        for r_part in (roads.geoms if hasattr(roads, "geoms") else [roads]):
            if r_part.is_empty:
                continue
            if r_part.geom_type in ("LineString", "LinearRing"):
                road_lines.append(r_part)
            elif r_part.geom_type == "Polygon":
                road_lines.append(r_part.exterior)
                road_lines.extend(r_part.interiors)
            elif hasattr(r_part, "boundary"):
                b = r_part.boundary
                if hasattr(b, "geoms"):
                    road_lines.extend([sub for sub in b.geoms if not sub.is_empty])
                elif not b.is_empty:
                    road_lines.append(b)

        for ln in road_lines:
            if hasattr(ln, "xy"):
                x, y = ln.xy
                f.add_trace(go.Scatter(x=list(x), y=list(y), mode="lines",
                                       line=dict(color="#dc2626", width=4),
                                       name="रास्ता / सड़क (Road)", showlegend=False))

    # Padded bounds for auto-fit view
    minx, miny, maxx, maxy = plot.bounds
    dx, dy = max(maxx - minx, 15.0), max(maxy - miny, 15.0)
    pad_x = max(dx * 0.35, 25.0)
    pad_y = max(dy * 0.35, 25.0)

    f.update_xaxes(
        range=[minx - pad_x, maxx + pad_x],
        title=dict(text="Easting (m, UTM Zone 44N)", font=dict(size=11)),
        showgrid=True, gridcolor="rgba(148, 163, 184, 0.2)",
        zeroline=False, tickformat="d"
    )
    f.update_yaxes(
        range=[miny - pad_y, maxy + pad_y],
        scaleanchor="x", scaleratio=1,
        title=dict(text="Northing (m, UTM Zone 44N)", font=dict(size=11)),
        showgrid=True, gridcolor="rgba(148, 163, 184, 0.2)",
        zeroline=False, tickformat="d"
    )
    f.update_layout(
        height=540,
        margin=dict(l=55, r=30, t=30, b=50),
        hovermode="closest",
        plot_bgcolor="rgba(248, 250, 252, 0.8)"
    )
    return f


t1, t2, t3, t4, t5 = st.tabs(["2 · Reconcile", "3 · Entitlements & ground truth", "4 · Auto-propose",
                              "5 · Compare & edit", "6 · Kurra pack"])

# ---------------------------------------------------------------- reconcile ----
with t1:
    curr_gis = S.get("giscode", loc["village"][0])
    st.subheader(f"🛰️ गाटा {plot_no} बुद्धिमान WMS व भू-सर्वेक्षण विश्लेषण (GIS Code: {curr_gis})")
    wf = S.get("wf")
    if not wf or str(wf.plot_no) != str(plot_no):
        with st.spinner("UP भू-नक्शा WMS सर्वर से अल्ट्रा-हाई रेजोल्यूशन मैप व दिशा-माप लोड हो रहे हैं..."):
            wf = CadastralWorkflow(gis_code=curr_gis, plot_no=str(plot_no))
            try:
                wf.fetch_plot_assets(dpi=300)
                wf.analyze_plot()
                S.wf = wf
            except Exception as e:
                st.error(f"विश्लेषण में त्रुटि: {e}")

    analysis = wf.analyze_plot() if (wf and wf.plot_geom) else None
    options = wf.suggest_partition_options() if analysis else []

    if analysis:
        # 1. Ultra-HD WMS Tiles (Isolated Highlight + Bird's Eye Surroundings View)
        st.markdown("#### 🖼️ 1. अल्ट्रा-हाई डेफिनिशन WMS सैटेलाइट व भू-नक्शा दृश्य (300 DPI)")
        w1, w2 = st.columns(2)
        if wf.isolated_wms_path and wf.isolated_wms_path.exists():
            w1.image(str(wf.isolated_wms_path), caption=f"गाटा {plot_no} पृथक सर्वेक्षण दृश्य (Isolated Highlight - WMS 300 DPI)", use_container_width=True)
        if wf.birdseye_wms_path and wf.birdseye_wms_path.exists():
            w2.image(str(wf.birdseye_wms_path), caption=f"गाटा {plot_no} विहंगम दृश्य (Bird's Eye Surroundings View - WMS 300 DPI)", use_container_width=True)

        # 2. Directional Dimensions & Surroundings HUD
        st.markdown("#### 📐 2. दिशा-आधारित सीमा माप व संदर्भ (Directional Boundary Dimensions)")
        dims = analysis["directional_dimensions"]
        dm1, dm2, dm3, dm4 = st.columns(4)
        dm1.metric("⬆️ उत्तर सीमा (North)", f"{dims['north_boundary_length_meters']} m")
        dm2.metric("⬇️ दक्षिण सीमा (South)", f"{dims['south_boundary_length_meters']} m")
        dm3.metric("➡️ पूर्व सीमा (East)", f"{dims['east_boundary_length_meters']} m")
        dm4.metric("⬅️ पश्चिम सीमा (West)", f"{dims['west_boundary_length_meters']} m")

        b1, b2, b3 = st.columns(3)
        b1.info(f"**आयाम (Bounding Box):** {dims['bbox_width_ew_meters']} m (पूर्व-पश्चिम) × {dims['bbox_height_ns_meters']} m (उत्तर-दक्षिण)")
        b2.info(f"**पहलू अनुपात (Aspect Ratio):** {dims['aspect_ratio']} : 1 ({dims['orientation']})")
        recon = analysis["area_reconciliation"]
        b3.info(f"**क्षेत्रफल सामंजस्य:** नक्शा {recon['surveyed_map_area_sqm']:,.1f} m² vs अभिलेख {recon['khatauni_record_area_sqm']:,.1f} m² ({recon['area_difference_percent']:+.2f}%)")

        # Surroundings Table
        surr = analysis["surroundings"]
        st.markdown("**🧭 चारों दिशाओं के समीपवर्ती गाटा (Adjacent Cadastral Neighbors):**")
        sm1, sm2, sm3, sm4 = st.columns(4)
        sm1.write(f"**उत्तर (North):**\n" + ("\n".join([f"- {x}" for x in surr['North']]) if surr['North'] else "- खुला क्षेत्र"))
        sm2.write(f"**दक्षिण (South):**\n" + ("\n".join([f"- {x}" for x in surr['South']]) if surr['South'] else "- खुला क्षेत्र"))
        sm3.write(f"**पूर्व (East):**\n" + ("\n".join([f"- {x}" for x in surr['East']]) if surr['East'] else "- खुला क्षेत्र"))
        sm4.write(f"**पश्चिम (West):**\n" + ("\n".join([f"- {x}" for x in surr['West']]) if surr['West'] else "- खुला क्षेत्र"))

        if analysis["touching_pathways"]:
            st.success(f"🛣️ **संपर्क मार्ग:** {', '.join(analysis['touching_pathways'])} — धारा 109(5)(f) के अनुसार सभी सह-खातेदारों को सीधा संपर्क मार्ग दिया जाएगा।")

        # 3. Ownership & Co-sharers Table
        st.markdown(f"#### 👥 3. सह-खातेदार विवरण ({analysis['owners_count']} खातेदार · खाता सं. {wf.khata_no or '—'})")
        owner_rows = [{"क्र.सं.": i+1, "खातेदार का नाम": o, "वैधानिक अंश": f"{100/len(analysis['co_sharers']):.2f}%", "हकदारी (m²)": f"{recon['surveyed_map_area_sqm']/len(analysis['co_sharers']):,.1f}"} for i, o in enumerate(analysis['co_sharers'])]
        st.dataframe(pd.DataFrame(owner_rows), use_container_width=True, hide_index=True)

        # 4. Statutory Partition Proposals (Rule 109(5))
        st.markdown("#### ⚖️ 4. धारा 109(5) नियमानुसार प्रस्तावित कुर्रा विभाजन विकल्प (Statutory Partition Options)")
        for opt in options:
            with st.expander(f"📌 {opt['title']}", expanded=True):
                st.caption(opt['description'])
                col_a, col_b = st.columns([3, 2])
                col_a.dataframe(pd.DataFrame(opt['allotments']), use_container_width=True, hide_index=True)
                with col_b:
                    st.write("**सत्यापन स्कोरकार्ड (Audit Scorecard):**")
                    for r in opt['statutory_compliance_audit']:
                        icon = "✅" if r['status'] == "GREEN" else ("⚠️" if r['status'] == "AMBER" else "❌")
                        st.write(f"{icon} **{r['rule_code']} · {r['rule_name']}** — {r['metric']}")
    st.subheader("Paste khatauni 'Order Description' text")
    txt = st.text_area("Hindi text from Bhulekh", height=160, key="orders_txt")
    if txt.strip():
        df = parse_orders(txt)
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.json(reconcile(df, record_area, plot.area))
            if (df.kind == "court_purchase").any():
                st.warning("The record shows purchases by the District & Sessions Court. Confirm who the "
                           "CURRENT co-owners are before planning any partition.")

# ------------------------------------------------------------- entitlements ----
with t2:
    st.write("Entitlements (sq m, from deeds / khatauni). Shares are normalised to the plot. "
             "'Preferred side' is a proposal only (e.g. adjoining land the person owns).")
    wf = S.get("wf")
    khatauni_owners = wf.owners if (wf and wf.owners) else []

    if "ent" not in S or S.get("ent_plot") != str(plot_no):
        if khatauni_owners and S.get("src") == "wms_gis":
            eq_area = plot.area / len(khatauni_owners)
            d = pd.DataFrame([{"name": o, "entitlement_sqm": round(eq_area, 2), "preferred_side": "—"} for o in khatauni_owners])
        else:
            d = demo.demo_entitlements()[["name", "entitlement_sqm"]].copy()
            d["preferred_side"] = "—"
        S.ent = d
        S.ent_plot = str(plot_no)

    c_sync, _ = st.columns([3, 2])
    if khatauni_owners and c_sync.button("🔄 खतौनी सह-खातेदारों से लोड करें (Sync with Khatauni)", help="वर्तमान गाटा के खतौनी सह-खातेदारों के अनुसार अंश तालिका रीसेट करें"):
        eq_area = plot.area / len(khatauni_owners)
        S.ent = pd.DataFrame([{"name": o, "entitlement_sqm": round(eq_area, 2), "preferred_side": "—"} for o in khatauni_owners])
        S.ent_plot = str(plot_no)
        st.rerun()

    S.ent = st.data_editor(
        S.ent, num_rows="dynamic", use_container_width=True,
        column_config={"preferred_side": st.column_config.SelectboxColumn(
            options=["—", "N", "S", "E", "W", "NE", "NW", "SE", "SW"])})
    sm = S.ent.entitlement_sqm.sum()
    st.caption(f"Sum of entitlements {sm:,.2f} sq m vs plot {plot.area:,.2f} sq m "
               f"({100*(sm-plot.area)/plot.area:+.2f}%). Shares are scaled pro-rata.")
    
    if wf and wf.touching_roads:
        st.success(f"🛣️ **गाँव भू-नक्शा संपर्क मार्ग (Auto-detected Pathways):** {', '.join(wf.touching_roads)} — चक मार्ग लेयर स्वतः सम्बद्ध है।")

    st.subheader("Ground-truth layers (GeoJSON, same CRS as the plot)")
    cc = st.columns(3)
    r_up = cc[0].file_uploader("Road centre-line(s)", type=["geojson", "json"], key="r")
    z_up = cc[1].file_uploader("Quality zones (property: multiplier)", type=["geojson", "json"], key="z")
    u_up = cc[2].file_uploader("Existing fields (property: id)", type=["geojson", "json"], key="u")
    if r_up:
        S.road = unary_union([shape(f["geometry"]) for f in json.load(r_up)["features"]])
    if z_up:
        S.zones = [(shape(f["geometry"]), float(f["properties"].get("multiplier", 1)))
                   for f in json.load(z_up)["features"]]
    S.units = ({str(f["properties"].get("id", i)): clean(shape(f["geometry"]))
                for i, f in enumerate(json.load(u_up)["features"])} if u_up else S.get("units"))
    st.caption("Possession / family-settlement polygons: attach to a party via Party.locked "
               "(see kurra/optimizer.py); UI upload is on the roadmap.")


def build_parties():
    ent = S.ent.dropna(subset=["name", "entitlement_sqm"])
    tot = ent.entitlement_sqm.sum()
    minx, miny, maxx, maxy = plot.bounds
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    dirs = {"N": (0, 1), "S": (0, -1), "E": (1, 0), "W": (-1, 0), "NE": (1, 1), "NW": (-1, 1),
            "SE": (1, -1), "SW": (-1, -1)}
    out = []
    for i, r in enumerate(ent.itertuples()):
        a = None
        if r.preferred_side in dirs:
            dx, dy = dirs[r.preferred_side]
            a = (cx + dx * (maxx - minx) / 2, cy + dy * (maxy - miny) / 2)
        out.append(Party(str(i), str(r.name), r.entitlement_sqm / tot, a))
    return out


# ------------------------------------------------------------------ propose ----
with t3:
    parties = build_parties()
    st.write(f"{len(parties)} parties · method: weighted recursive bisection with quality-weighted value"
             + (" + CP-SAT whole-field assignment" if S.get("units") else ""))
    if st.button("Generate candidate plans", type="primary"):
        specs = [("compact", 0), ("compact", 1), ("compact", 2)]
        if roads is not None and not roads.is_empty:
            specs += [("frontage", 0), ("road_parallel", 0)]
        plans = []
        with st.spinner("Optimising…"):
            for strat, seed in specs:
                try:
                    lots, meta = generate_plan(plot, parties, zones, strat, roads, S.get("units"), seed)
                    res = evaluate(lots, parties, plot, zones, roads, None, None, S.get("units"), tol)
                    plans.append({"name": f"{strat} #{seed}", "lots": lots, "res": res})
                except Exception as e:  # keep going; show what failed
                    st.warning(f"{strat} #{seed}: {e}")
        plans.sort(key=lambda p: rank_key(p["res"]))
        S.plans, S.parties = plans, parties
    if S.get("plans"):
        rows = []
        for p in S.plans:
            row = {"plan": p["name"]}
            row.update({r.code: ICON[r.status] for r in p["res"]})
            rows.append(row)
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption("a share · b compactness · c quality mix · d field splits · e possession · f frontage · "
                   "g settlement · G1 sliver · G2 access. Ranked by fewest reds, then ambers.")

# ------------------------------------------------------------ compare / edit ----
with t4:
    if not S.get("plans"):
        st.info("Generate plans first.")
    else:
        names = [p["name"] for p in S.plans]
        pick = st.selectbox("Plan", names)
        plan = next(p for p in S.plans if p["name"] == pick)
        col1, col2 = st.columns([3, 2])
        col1.plotly_chart(fig_of(plan["lots"], S.parties), use_container_width=True, config={"displayModeBar": True, "scrollZoom": True})
        col2.dataframe(report.lots_table(plan["lots"], S.parties, plot, zones), use_container_width=True)
        for r in plan["res"]:
            col2.write(f"{ICON[r.status]} **{r.code} · {r.name_en}** — {r.metric} {('· ' + r.detail) if r.detail else ''}")
        st.caption("Drag-to-edit cut lines is not in this prototype; adjust tolerances/preferences and regenerate.")

# --------------------------------------------------------------------- pack ----
with t5:
    if not S.get("plans"):
        st.info("Generate plans first.")
    else:
        pick = st.selectbox("Plan to export", [p["name"] for p in S.plans], key="exp")
        plan = next(p for p in S.plans if p["name"] == pick)
        od = st.date_input("Date of court order (starts the one-month timer)", date.today())
        tbl = report.lots_table(plan["lots"], S.parties, plot, zones)
        meta = {"district": f"{loc['district'][0]} {loc['district'][1]}",
                "tehsil": f"{loc['tehsil'][0]} {loc['tehsil'][1]}",
                "village": f"{loc['village'][0]} {loc['village'][1]}",
                "plot": plot_no, "area_sqm": plot.area}
        md = report.kurra_markdown(meta, tbl, plan["res"], pick, od)
        st.markdown(md)
        st.download_button("Kurra draft (Markdown)", md, "kurra_draft.md")
        st.download_button("Lots (GeoJSON, WGS84)", report.lots_geojson(plan["lots"], S.parties), "kurra_lots.geojson")
        st.download_button("Allotment table (CSV)", tbl.to_csv(index=False), "kurra_table.csv")
