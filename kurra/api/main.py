"""FastAPI Application for SDM Kurra Dashboard.

Wraps the core cadastral partition engine, deterministic Rule 109(5) tiered audit,
local SQLite cadastre store, and CrewAI Hindi drafting assistance.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from shapely import wkt
from shapely.geometry import LineString, Polygon, box, mapping, shape

from ..bhunaksha import BhunakshaClient
from ..config import OFFICIAL_KURRA_COLORS, Tolerances
from ..fractions import parse_fraction, validate_shares
from ..geometry import (
    aspect_ratio,
    clean,
    is_connected,
    min_width,
    overlap_percentage,
    polsby_popper,
)
from ..ingest.store import CadastreStore, to_wgs84_geojson
from ..legal_drafter import RevenueLegalDrafter
from ..crew_drafter import KurraLegalCrew
from ..optimizer import Party, generate_plan
from ..report_parser import PlotReportData
from ..rules import evaluate, explain_failure, rank_key
from .schemas import (
    AuditScorecard,
    CaseMetadata,
    CoSharerInput,
    LegalDraftRequest,
    LegalDraftResponse,
    CustomCutRequest,
    CustomCutResponse,
    OverlapRequest,
    OverlapResponse,
    PartitionScheme,
    ProposedLot,
    ProposePlanRequest,
    ProposePlanResponse,
)

app = FastAPI(
    title="SDM Kurra Partition API",
    version="2.0.0",
    description="Section 116 / Rule 109(5) UP Revenue Code Cadastral Partition Engine"
)

# Enable CORS for Next.js frontend (local dev and web app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = BhunakshaClient()
drafter = RevenueLegalDrafter()
legal_crew = KurraLegalCrew()


@app.get("/api/health")
def health():
    return {"status": "ok", "engine": "kurra-v2", "crs": "EPSG:32644"}


@app.get("/api/media/status")
def media_status():
    """Check Cloudinary CDN integration and configuration status."""
    from ..cloudinary_service import is_configured
    configured = is_configured()
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    return {
        "status": "configured" if configured else "unconfigured",
        "cdn_provider": "cloudinary",
        "cloud_name": cloud_name if configured else None,
        "optimizations": ["f_auto", "q_auto:good", "pg_1_rasterization", "presigned_direct_upload"]
    }


@app.get("/api/media/signature")
def get_media_upload_signature(folder: str = "kurra_cadastre"):
    """Generate secure presigned upload signature for direct browser-to-Cloudinary upload."""
    from ..cloudinary_service import create_presigned_upload_signature
    return create_presigned_upload_signature(folder=folder)



@app.get("/api/store/status")
def store_status(
    district: str = Query("165"),
    tehsil: str = Query("00854"),
    village: str = Query("151769")
):
    """Retrieve local SQLite database sync and offline status."""
    store = CadastreStore(district, tehsil, village)
    return store.get_sync_status()


@app.get("/api/plots/{district}/{tehsil}/{village}/{plot_no}")
def get_plot_data(district: str, tehsil: str, village: str, plot_no: str):
    """Fetch complete plot details: local store first, live Bhunaksha fallback."""
    store = CadastreStore(district, tehsil, village)
    cached_report = store.get_plot(plot_no)

    if cached_report:
        poly_res = store.get_plot_geometry(plot_no)
        poly = poly_res[0] if poly_res else None
        return {
            "source": "local_store",
            "report": cached_report.to_dict(),
            "polygon_geojson": mapping(poly) if poly else None,
            "polygon_wgs84": to_wgs84_geojson(poly) if poly else None,
            "wkt": poly.wkt if poly else None,
            "colors": OFFICIAL_KURRA_COLORS
        }

    # Live fallback
    try:
        report = client.get_plot_report(district, tehsil, village, plot_no, output_dir=store.artifacts_dir)
        poly, _ = client.plot_geometry(f"{district}{tehsil}{village}", plot_no)
        # Cache into SQLite
        store.save_plot_report(report, polygon=poly)
        return {
            "source": "live_bhunaksha",
            "report": report.to_dict(),
            "polygon_geojson": mapping(poly) if poly else None,
            "polygon_wgs84": to_wgs84_geojson(poly) if poly else None,
            "wkt": poly.wkt if poly else None,
            "colors": OFFICIAL_KURRA_COLORS
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"गाटा {plot_no} प्राप्त नहीं हुआ: {e}")


@app.post("/api/plans/propose", response_model=ProposePlanResponse)
@app.post("/api/propose", response_model=ProposePlanResponse)
def propose_plans(req: ProposePlanRequest):
    """Generate multi-objective statutory partition plans under Rule 109(5)."""
    parties_input = req.parties or req.sharers or []
    if not parties_input:
        return ProposePlanResponse(
            plot_no=req.plot_no,
            schemes=[],
            shares_valid=False,
            shares_message="सह-खातेदारों की सूची आवश्यक है।"
        )

    # 1. Validate Co-sharer shares
    share_map = {p.id: p.share for p in parties_input}
    valid, float_shares, str_shares, share_msg = validate_shares(share_map)
    if not valid:
        return ProposePlanResponse(
            plot_no=req.plot_no,
            schemes=[],
            shares_valid=False,
            shares_message=share_msg
        )

    # 2. Retrieve Plot Geometry
    store = CadastreStore(req.district, req.tehsil, req.village)
    geom_res = store.get_plot_geometry(req.plot_no)
    if geom_res:
        plot_poly = geom_res[0]
    else:
        plot_poly, _ = client.plot_geometry(f"{req.district}{req.tehsil}{req.village}", req.plot_no)

    if not plot_poly or plot_poly.is_empty:
        raise HTTPException(status_code=400, detail="गाटा की ज्यामिति अनुपलब्ध है।")

    # 3. Roads geometry
    road_poly = None
    if req.road_geometry_wkt:
        try:
            road_poly = wkt.loads(req.road_geometry_wkt)
        except Exception:
            pass
    if road_poly is None:
        # Synthesize road buffer along southern boundary (Plot 50 / Chakroad)
        min_y = plot_poly.bounds[1]
        road_poly = LineString([(plot_poly.bounds[0], min_y), (plot_poly.bounds[2], min_y)]).buffer(2.0)

    # 4. Prepare Parties
    parties = []
    for idx, p in enumerate(parties_input):
        color_info = OFFICIAL_KURRA_COLORS[idx % len(OFFICIAL_KURRA_COLORS)]
        possession_poly = None
        if p.possession_wkt:
            try:
                possession_poly = clean(wkt.loads(p.possession_wkt).intersection(plot_poly))
            except Exception:
                pass

        parties.append(Party(
            id=p.id,
            name=p.name,
            share=float_shares[p.id],
            locked=possession_poly
        ))

    # Determine pathway width
    path_width = req.shared_path_width
    if path_width is None and req.shared_pathway and req.shared_pathway.get("enabled"):
        path_width = float(req.shared_pathway.get("width_m", 3.0))

    # 5. Generate Plans for each strategy
    strategy_names = {
        "compact": ("लेखपाल का मानक प्रस्ताव (सघन चक)", "Lekhpal Standard (Compact Chaks)"),
        "frontage": ("सड़क के लम्बवत सीधी पट्टियाँ (समान अग्रभाग)", "Perpendicular to Road (Frontage Parity)"),
        "road_parallel": ("सड़क के समानांतर पट्टियाँ (आगे-पीछे)", "Road-Parallel Rows (Front-to-Rear)")
    }

    schemes: List[PartitionScheme] = []
    scheme_lot_map: Dict[str, Dict[str, Polygon]] = {}

    for strat in req.strategies:
        lots, meta = generate_plan(
            plot=plot_poly,
            parties=parties,
            strategy=strat,
            road=road_poly,
            seed=req.seed,
            shared_path_width=path_width
        )
        scheme_lot_map[strat] = lots

        # Tiered Audit
        audit = evaluate(lots, parties, plot_poly, roads=road_poly)
        audit_cards = [
            AuditScorecard(
                tier=r.tier,
                tier_name=r.tier_name,
                code=r.code,
                clause_ref=r.clause_ref,
                legal_basis=r.legal_basis,
                name_en=r.name_en,
                name_hi=r.name_hi,
                status=r.status,
                metric=r.metric,
                detail=r.detail,
                statutory_citation=r.statutory_citation
            ) for r in audit
        ]

        has_red = any(r.status == "red" for r in audit)
        fail_msg = explain_failure(audit) if has_red else None

        # Build proposed lots
        prop_lots: List[ProposedLot] = []
        for idx, p in enumerate(parties):
            lot_geom = lots.get(p.id, Polygon())
            color_info = OFFICIAL_KURRA_COLORS[idx % len(OFFICIAL_KURRA_COLORS)]

            # Road frontage
            front_m = 0.0
            if road_poly and not lot_geom.is_empty:
                front_m = round(road_poly.intersection(lot_geom.buffer(0.5)).length, 2)

            prop_lots.append(ProposedLot(
                party_id=p.id,
                party_name=p.name,
                share_nominal=p.share,
                share_str=str_shares.get(p.id, f"{p.share:.2%}"),
                area_sqm=round(lot_geom.area, 2),
                area_ha=round(lot_geom.area / 10000.0, 4),
                color_hex=color_info["hex"],
                color_hi=color_info["name_hi"],
                geojson=mapping(lot_geom),
                wkt=lot_geom.wkt,
                polsby_popper=round(polsby_popper(lot_geom), 2),
                aspect_ratio=round(aspect_ratio(lot_geom), 2),
                road_frontage_m=front_m,
                is_connected=is_connected(lot_geom)
            ))

        name_hi, name_en = strategy_names.get(strat, (f"योजना ({strat})", strat))
        schemes.append(PartitionScheme(
            scheme_id=strat,
            scheme_name_hi=name_hi,
            scheme_name_en=name_en,
            description=f"नियम 109(5) के तहत {name_hi} आधारित विभाजन",
            lots=prop_lots,
            audit_results=audit_cards,
            all_passed=not has_red,
            failure_reason=fail_msg,
            provenance=meta
        ))

    # 6. Compute Cross-Scheme Overlap Matrix
    overlap_matrix: Dict[str, Dict[str, float]] = {}
    for s1 in req.strategies:
        overlap_matrix[s1] = {}
        for s2 in req.strategies:
            if s1 == s2:
                overlap_matrix[s1][s2] = 100.0
            else:
                overlaps = []
                for p in parties:
                    g1 = scheme_lot_map[s1].get(p.id)
                    g2 = scheme_lot_map[s2].get(p.id)
                    overlaps.append(overlap_percentage(g1, g2))
                overlap_matrix[s1][s2] = round(sum(overlaps) / max(len(overlaps), 1), 1)

    return ProposePlanResponse(
        plot_no=req.plot_no,
        schemes=schemes,
        shares_valid=True,
        shares_message=share_msg,
        possession_overlap_matrix=overlap_matrix
    )


@app.post("/api/plans/overlap", response_model=OverlapResponse)
def compute_overlap(req: OverlapRequest):
    """Compute percentage overlap between any two scheme partitions."""
    party_overlaps = {}
    pids = set(req.scheme_a_lots.keys()) | set(req.scheme_b_lots.keys())

    for pid in pids:
        w1 = req.scheme_a_lots.get(pid)
        w2 = req.scheme_b_lots.get(pid)
        if not w1 or not w2:
            party_overlaps[pid] = 0.0
            continue
        try:
            g1 = wkt.loads(w1)
            g2 = wkt.loads(w2)
            party_overlaps[pid] = overlap_percentage(g1, g2)
        except Exception:
            party_overlaps[pid] = 0.0

    mean_pct = round(sum(party_overlaps.values()) / max(len(party_overlaps), 1), 2)
    return OverlapResponse(
        mean_overlap_pct=mean_pct,
        party_overlaps=party_overlaps,
        explanation=f"दोनों योजनाओं के मध्य कुल कब्जा सामंजस्य: {mean_pct:.1f}%"
    )


@app.post("/api/plans/custom-cut", response_model=CustomCutResponse)
def custom_cut(req: CustomCutRequest):
    """Slice plot polygon using custom pencil/dragged cut lines and audit Rule 109(5)."""
    from shapely.ops import split
    from shapely.geometry import LineString
    
    # 1. Validate Co-sharer shares
    share_map = {p.id: p.share for p in req.parties}
    valid, float_shares, str_shares, share_msg = validate_shares(share_map)
    if not valid:
        raise HTTPException(status_code=400, detail=share_msg)

    # 2. Retrieve Plot Geometry
    store = CadastreStore(req.district, req.tehsil, req.village)
    geom_res = store.get_plot_geometry(req.plot_no)
    if geom_res:
        plot_poly = geom_res[0]
    else:
        plot_poly, _ = client.plot_geometry(f"{req.district}{req.tehsil}{req.village}", req.plot_no)

    if not plot_poly or plot_poly.is_empty:
        raise HTTPException(status_code=404, detail="Plot geometry not found")

    # Synthesize road buffer along southern boundary (Plot 50 / Chakroad)
    min_y = plot_poly.bounds[1]
    road_poly = LineString([(plot_poly.bounds[0], min_y), (plot_poly.bounds[2], min_y)]).buffer(2.0)

    parties = [
        Party(
            id=p.id,
            name=p.name,
            share=float_shares[p.id],
            locked=wkt.loads(p.possession_wkt) if p.possession_wkt and p.possession_wkt != "CLAIMED_EXISTING" else None
        ) for p in req.parties
    ]

    current_pieces = [plot_poly]
    for line_coords in req.cut_lines:
        if len(line_coords) >= 2:
            p1, p2 = line_coords[0], line_coords[1]
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            length = (dx*dx + dy*dy)**0.5 or 1.0
            ux, uy = dx / length, dy / length
            ext_line = LineString([
                (p1[0] - ux * 50.0, p1[1] - uy * 50.0),
                (p2[0] + ux * 50.0, p2[1] + uy * 50.0)
            ])
            new_pieces = []
            for piece in current_pieces:
                if piece.intersects(ext_line):
                    spl = split(piece, ext_line)
                    new_pieces.extend(list(spl.geoms) if hasattr(spl, "geoms") else [spl])
                else:
                    new_pieces.append(piece)
            current_pieces = [p for p in new_pieces if p.area > 1.0]

    # Assign pieces to parties
    lots: Dict[str, Any] = {}
    sorted_parties = sorted(parties, key=lambda p: p.share, reverse=True)
    sorted_pieces = sorted(current_pieces, key=lambda g: g.area, reverse=True)
    for i, p in enumerate(sorted_parties):
        if i < len(sorted_pieces):
            lots[p.id] = sorted_pieces[i]
        else:
            lots[p.id] = Polygon()

    # Rule 109(5) audit
    audit = evaluate(lots, parties, plot_poly, roads=road_poly)
    audit_cards = [
        AuditScorecard(
            tier=r.tier,
            tier_name=r.tier_name,
            code=r.code,
            clause_ref=r.clause_ref,
            legal_basis=r.legal_basis,
            name_en=r.name_en,
            name_hi=r.name_hi,
            status=r.status,
            metric=r.metric,
            detail=r.detail,
            statutory_citation=r.statutory_citation
        ) for r in audit
    ]
    has_red = any(r.status == "red" for r in audit)
    fail_msg = explain_failure(audit) if has_red else None

    prop_lots: List[ProposedLot] = []
    for idx, p in enumerate(parties):
        lot_geom = lots.get(p.id, Polygon())
        color_info = OFFICIAL_KURRA_COLORS[idx % len(OFFICIAL_KURRA_COLORS)]
        front_m = 0.0
        if road_poly and not lot_geom.is_empty:
            front_m = round(road_poly.intersection(lot_geom.buffer(0.5)).length, 2)

        prop_lots.append(ProposedLot(
            party_id=p.id,
            party_name=p.name,
            share_nominal=p.share,
            share_str=str_shares.get(p.id, f"{p.share:.2%}"),
            area_sqm=round(lot_geom.area, 2),
            area_ha=round(lot_geom.area / 10000.0, 4),
            color_hex=color_info["hex"],
            color_hi=color_info["name_hi"],
            geojson=mapping(lot_geom),
            wkt=lot_geom.wkt,
            polsby_popper=round(polsby_popper(lot_geom), 2),
            aspect_ratio=round(aspect_ratio(lot_geom), 2),
            road_frontage_m=front_m,
            is_connected=is_connected(lot_geom)
        ))

    scheme = PartitionScheme(
        scheme_id="scheme_custom_pencil",
        scheme_name_hi="योजना 4: हस्तनिर्मित विभाजन (पेंसिल द्वारा रेखांकित)",
        scheme_name_en="Scheme 4: Custom Pencil Cut Demarcation",
        description="खातेदारों / राजस्व लेखपाल द्वारा हाथ से खींची गई विभाजन रेखा के अनुसार सटीक कुर्रा सीमांकन।",
        lots=prop_lots,
        audit_results=audit_cards,
        all_passed=not has_red,
        failure_reason=fail_msg,
        provenance={"mode": "pencil_custom", "num_cuts": len(req.cut_lines)}
    )

    return CustomCutResponse(
        scheme=scheme,
        success=True,
        message="हस्तनिर्मित विभाजन रेखा सफलतापूर्वक लागू की गई।"
    )



@app.post("/api/draft/report", response_model=LegalDraftResponse)
def draft_legal_report(req: LegalDraftRequest):
    """Draft official Lekhpal Kurra Report and Preliminary Decree in Hindi."""
    case_dict = req.case_info.model_dump()
    plot_dict = {"plot_no": req.case_info.plot_no}

    scheme_dict = {
        "parties": [
            {
                "name": l.party_name,
                "share_str": l.share_str,
                "share_pct": l.share_nominal * 100.0,
                "area_sqm": l.area_sqm,
                "area_ha": l.area_ha,
                "color_hi": l.color_hi
            } for l in req.scheme.lots
        ],
        "shared_pathway": req.scheme.provenance.get("shared_pathway", {})
    }

    docs = legal_crew.draft_documents(
        case_meta=case_dict,
        scheme_data={
            "plot_no": req.case_info.plot_no,
            "lots": [l.model_dump() for l in req.scheme.lots],
            "audit_results": [a.model_dump() for a in req.scheme.audit_results],
            "shared_pathway": req.scheme.provenance.get("shared_pathway", {})
        }
    )

    return LegalDraftResponse(
        lekhpal_report_hi=docs.get("lekhpal_report_hi", ""),
        preliminary_decree_hi=docs.get("preliminary_decree_hi", "")
    )
