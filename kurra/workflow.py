"""Intelligent Cadastral Analysis & Partition Workflow for UP Revenue Code Rule 109(5).

Executes the 3-step automated pipeline:
1. Ingestion: Given GIS Code & Plot No, fetches ultra-high-definition WMS PNGs
   (isolated highlight + bird's eye surroundings view) and official Khatauni owner ROR details.
2. Cadastral Analysis: Computes metric plot dimensions wrt directions (N, S, E, W),
   area reconciliation, co-sharer entitlements, and surrounding road/neighbor context.
3. Statutory Partition: Generates multi-objective Rule 109(5) compliant partition plans
   (Compact, Road Frontage, Road-Parallel) with legal compliance audit scorecards.
"""
from __future__ import annotations
import io
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from shapely.geometry import box, shape, Polygon, LineString
from shapely.ops import unary_union

from .bhunaksha import BhunakshaClient, resolve_giscode
from .optimizer import Party, generate_plan
from .rules import evaluate, RuleResult
from .config import Tolerances

HERE = Path(__file__).parent
DATA_DIR = HERE.parent / "data" / "jalaun_151769"
OUTPUT_DIR = HERE.parent / "data" / "workflow_output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class CadastralWorkflow:
    def __init__(self, gis_code: str = "16500854151769", plot_no: str = "181"):
        self.gis_code = resolve_giscode(str(gis_code).strip())
        self.plot_no = str(plot_no).strip()
        self.client = BhunakshaClient()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Referer": "https://upbhunaksha.gov.in/home"
        }
        self.wms_base = "https://upbhunaksha.gov.in/bhunakshaserver/WMS/tile"
        
        # In-memory storage for workflow outputs
        self.plot_geom: Optional[Polygon] = None
        self.plot_id: Optional[str] = None
        self.bbox: Optional[Tuple[float, float, float, float]] = None
        self.khatauni_text: str = ""
        self.khata_no: str = ""
        self.record_area_sqm: float = 0.0
        self.record_area_ha: float = 0.0
        self.owners: List[str] = []
        
        self.directional_dims: Dict[str, Any] = {}
        self.surroundings: Dict[str, List[str]] = {}
        self.touching_roads: List[str] = []
        self.roads_geom: Optional[Any] = None
        
        self.isolated_wms_path: Optional[Path] = None
        self.birdseye_wms_path: Optional[Path] = None
        self.partition_plans: List[Dict[str, Any]] = []

    # -------------------------------------------------------------------------
    # STEP 1: INGESTION (WMS PNGs + Plot Owner Info)
    # -------------------------------------------------------------------------
    def fetch_plot_assets(self, dpi: int = 300) -> Dict[str, Any]:
        """Fetch ultra-high definition WMS tiles and official plot owner information."""
        # 1. Fetch Plot Bounding Box & Plot UUID (with local dataset fallback)
        bbox_data = None
        try:
            bbox_data = self.client._call("plot_bbox", giscode=self.gis_code, plot=self.plot_no)
        except Exception:
            pass

        if not bbox_data or "minx" not in bbox_data:
            local_utm = DATA_DIR / "all_plots_151769_utm.geojson"
            if local_utm.exists():
                with open(local_utm, encoding="utf-8") as f:
                    vdata = json.load(f)
                for feat in vdata.get("features", []):
                    if str(feat["properties"].get("plot_no")) == self.plot_no:
                        p_poly = shape(feat["geometry"])
                        minx, miny, maxx, maxy = p_poly.bounds
                        bbox_data = {
                            "minx": minx, "miny": miny, "maxx": maxx, "maxy": maxy,
                            "id": feat["properties"].get("plot_id", ""),
                            "kide": self.plot_no
                        }
                        self.plot_geom = p_poly
                        break

        if not bbox_data or "minx" not in bbox_data:
            raise RuntimeError(f"गाटा {self.plot_no} GIS कोड {self.gis_code} में नहीं मिला।")

        minx = float(bbox_data["minx"])
        miny = float(bbox_data["miny"])
        maxx = float(bbox_data["maxx"])
        maxy = float(bbox_data["maxy"])
        self.bbox = (minx, miny, maxx, maxy)
        self.plot_id = bbox_data.get("id")

        # 2. Fetch Plot Geometry (vector polygon)
        if self.plot_geom is None:
            try:
                self.plot_geom, meta = self.client.plot_geometry(self.gis_code, self.plot_no)
            except Exception:
                self.plot_geom = box(minx, miny, maxx, maxy)

        # 3. Fetch Owner / Khatauni ROR details
        try:
            self.khatauni_text = self.client.plot_info(self.gis_code, self.plot_no)
            self._parse_khatauni_info()
        except Exception:
            pass

        if not self.owners or self.owners == ["एकल खातेदार (Single Khatedar)"]:
            inv_csv = DATA_DIR / "village_151769_inventory.csv"
            if inv_csv.exists():
                import csv
                with open(inv_csv, encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        if str(row.get("plot_no")) == self.plot_no:
                            raw_owners = row.get("owners", "")
                            if raw_owners and raw_owners not in ["—", "-", "None"]:
                                self.owners = [o.strip() for o in raw_owners.split(",") if o.strip()]
                            self.khata_no = row.get("khata_no", "")
                            self.record_area_sqm = float(row.get("area_sqm", 0) or 0)
                            self.record_area_ha = float(row.get("area_ha", 0) or 0)
                            break

        # 4. Fetch Ultra-HD Isolated Plot Highlight WMS PNG
        self.isolated_wms_path = OUTPUT_DIR / f"plot_{self.plot_no}_isolated.png"
        self._fetch_wms_tile(
            bbox=self.bbox,
            style="PLOT_SELECTION" if self.plot_id else "VILLAGE_MAP",
            layer="PLOT_LIST" if self.plot_id else "VILLAGE_MAP",
            plot_id=self.plot_id,
            dpi=dpi,
            width=1024,
            height=1024,
            out_file=self.isolated_wms_path
        )

        # 5. Fetch Ultra-HD Birdseye View WMS PNG (padded for neighborhood context)
        pad = max((maxx - minx) * 0.45, 120.0)
        birdseye_bbox = (minx - pad, miny - pad, maxx + pad, maxy + pad)
        self.birdseye_wms_path = OUTPUT_DIR / f"plot_{self.plot_no}_birdseye.png"
        self._fetch_wms_tile(
            bbox=birdseye_bbox,
            style="VILLAGE_MAP",
            layer="VILLAGE_MAP",
            dpi=dpi,
            width=1280,
            height=1280,
            out_file=self.birdseye_wms_path
        )

        return {
            "plot_no": self.plot_no,
            "gis_code": self.gis_code,
            "plot_id": self.plot_id,
            "khata_no": self.khata_no,
            "record_area_ha": self.record_area_ha,
            "record_area_sqm": self.record_area_sqm,
            "owners": self.owners,
            "bbox_utm": self.bbox,
            "isolated_wms_image": str(self.isolated_wms_path),
            "birdseye_wms_image": str(self.birdseye_wms_path)
        }

    def _parse_khatauni_info(self):
        """Extract Khata No, Area, and Owner names from official Khatauni text."""
        # Khata No
        km = re.search(r"Khata No\s*:\s*([0-9]+)", self.khatauni_text)
        if km:
            self.khata_no = km.group(1)

        # Area
        am = re.search(r"Area\s*:\s*([0-9\.]+)\s*Hectare", self.khatauni_text)
        if am:
            self.record_area_ha = float(am.group(1))
            self.record_area_sqm = round(self.record_area_ha * 10000.0, 2)
        elif self.plot_geom:
            self.record_area_sqm = round(self.plot_geom.area, 2)
            self.record_area_ha = round(self.record_area_sqm / 10000.0, 4)

        # Owners list
        owner_matches = re.findall(r"नाम\s*:\s*([^\n\r]+?)(?:\s+संरक्षक|\s*$)", self.khatauni_text)
        self.owners = [o.strip() for o in owner_matches if o.strip() and o.strip() != "---"]
        if not self.owners:
            self.owners = ["एकल खातेदार (Single Khatedar)"]

    def _fetch_wms_tile(self, bbox: Tuple[float, float, float, float], style: str, layer: str,
                        dpi: int, width: int, height: int, out_file: Path, plot_id: Optional[str] = None):
        """Fetch WMS tile from UP Bhunaksha server and save to local disk."""
        params = {
            "REQUEST": "GetMap",
            "SERVICE": "WMS",
            "VERSION": "1.3.0",
            "FORMAT": "image/png",
            "STYLES": style,
            "TRANSPARENT": "TRUE",
            "LAYERS": layer,
            "gis_code": self.gis_code,
            "CRS": "EPSG:32644",
            "FORMAT_OPTIONS": f"dpi:{dpi}",
            "WIDTH": str(width),
            "HEIGHT": str(height),
            "BBOX": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
        }
        if plot_id:
            params["plot_id"] = plot_id

        try:
            r = requests.get(self.wms_base, params=params, headers=self.headers, timeout=15)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                out_file.write_bytes(r.content)
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # STEP 2: CADASTRAL ANALYSIS (Directional Dimensions, Area, Surroundings)
    # -------------------------------------------------------------------------
    def analyze_plot(self) -> Dict[str, Any]:
        """Analyze plot dimensions wrt cardinal directions, area reconciliation, and surroundings."""
        if self.plot_geom is None:
            self.fetch_plot_assets()

        g = self.plot_geom
        c = g.centroid
        minx, miny, maxx, maxy = g.bounds

        # 1. Edge Segment Decomposition wrt Cardinal Directions
        coords = list(g.exterior.coords)
        north_len, south_len, east_len, west_len = 0.0, 0.0, 0.0, 0.0

        for i in range(len(coords) - 1):
            p1, p2 = coords[i], coords[i + 1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            seg_len = math.hypot(dx, dy)
            angle = math.degrees(math.atan2(dy, dx)) % 360

            # Vertical edges (East/West) vs Horizontal edges (North/South)
            if 45 <= angle < 135 or 225 <= angle < 315:
                mid_x = (p1[0] + p2[0]) / 2.0
                if mid_x >= c.x:
                    east_len += seg_len
                else:
                    west_len += seg_len
            else:
                mid_y = (p1[1] + p2[1]) / 2.0
                if mid_y >= c.y:
                    north_len += seg_len
                else:
                    south_len += seg_len

        # Aspect Ratio & Principal Orientation
        width_ew = maxx - minx
        height_ns = maxy - miny
        aspect_ratio = max(width_ew, height_ns) / max(min(width_ew, height_ns), 0.1)

        self.directional_dims = {
            "bbox_width_ew_meters": round(width_ew, 2),
            "bbox_height_ns_meters": round(height_ns, 2),
            "north_boundary_length_meters": round(north_len, 2),
            "south_boundary_length_meters": round(south_len, 2),
            "east_boundary_length_meters": round(east_len, 2),
            "west_boundary_length_meters": round(west_len, 2),
            "total_perimeter_meters": round(g.length, 2),
            "aspect_ratio": round(aspect_ratio, 2),
            "orientation": "East-West Long" if width_ew >= height_ns else "North-South Long"
        }

        # 2. Area Reconciliation
        map_sqm = round(g.area, 2)
        diff_sqm = round(map_sqm - self.record_area_sqm, 2)
        diff_pct = round((diff_sqm / max(self.record_area_sqm, 1.0)) * 100.0, 2)

        area_recon = {
            "khatauni_record_area_sqm": self.record_area_sqm,
            "khatauni_record_area_ha": self.record_area_ha,
            "surveyed_map_area_sqm": map_sqm,
            "surveyed_map_area_ha": round(map_sqm / 10000.0, 4),
            "area_difference_sqm": diff_sqm,
            "area_difference_percent": diff_pct,
            "status": "Reconciled (Within Least-Count Tolerance)" if abs(diff_pct) <= 2.5 else "Mismatch Flagged"
        }

        # 3. Surroundings & Road Frontage Discovery
        self._analyze_surroundings()

        return {
            "plot_no": self.plot_no,
            "directional_dimensions": self.directional_dims,
            "area_reconciliation": area_recon,
            "owners_count": len(self.owners),
            "co_sharers": self.owners,
            "surroundings": self.surroundings,
            "touching_pathways": self.touching_roads
        }

    def _analyze_surroundings(self):
        """Analyze adjacent cadastral parcels, pathways (चक मार्ग / रास्ता), and water drains."""
        self.surroundings = {"North": [], "South": [], "East": [], "West": []}
        self.touching_roads = []
        road_polys = []

        village_utm_file = DATA_DIR / "all_plots_151769_utm.geojson"
        if not village_utm_file.exists():
            return

        with open(village_utm_file, encoding="utf-8") as f:
            vdata = json.load(f)

        g = self.plot_geom
        c = g.centroid

        for feat in vdata.get("features", []):
            pno = str(feat["properties"].get("plot_no", ""))
            if pno == self.plot_no:
                continue

            poly = shape(feat["geometry"])
            lc = feat["properties"].get("land_class", "")
            is_path = "मार्ग" in lc or "रास्ता" in lc or "सड़क" in lc

            if is_path:
                road_polys.append(poly)

            dist = g.distance(poly)
            if dist < 12.0:  # Direct contact or immediate neighbor
                nc = poly.centroid
                ang = math.degrees(math.atan2(nc.y - c.y, nc.x - c.x)) % 360

                label = f"गाटा {pno}"
                if is_path:
                    label += f" ({lc})"
                    if dist < 1.0:
                        self.touching_roads.append(f"गाटा {pno} ({lc})")
                elif "नाली" in lc:
                    label += " (नाली)"
                elif "तालाब" in lc:
                    label += " (तालाब)"

                if 45 <= ang < 135:
                    self.surroundings["North"].append(label)
                elif 135 <= ang < 225:
                    self.surroundings["West"].append(label)
                elif 225 <= ang < 315:
                    self.surroundings["South"].append(label)
                else:
                    self.surroundings["East"].append(label)

        if road_polys:
            self.roads_geom = unary_union(road_polys)

    # -------------------------------------------------------------------------
    # STEP 3: STATUTORY PARTITION OPTIONS (UP Revenue Code Rule 109(5))
    # -------------------------------------------------------------------------
    def suggest_partition_options(self) -> List[Dict[str, Any]]:
        """Generate Rule 109(5) compliant partition options for all co-sharers."""
        if not self.directional_dims:
            self.analyze_plot()

        n_parties = len(self.owners)
        equal_share = 1.0 / max(n_parties, 1)

        # Build party objects
        parties = [
            Party(id=str(idx + 1), name=owner_name, share=equal_share)
            for idx, owner_name in enumerate(self.owners)
        ]

        # Strategies under UP Revenue Code Rule 109(5)
        strategy_specs = [
            ("compact", "विकल्प 1: सममित चकबन्दी विभाजन (Compact Allotment — Rule 109(5)(b))",
             "Maximizes rectangularity and Polsby-Popper compactness, reducing parcel boundary disputes."),
            ("frontage", "विकल्प 2: सड़क/रास्ता समानांतर विभाजन (Road Frontage Proportional — Rule 109(5)(f))",
             "Guarantees every single co-sharer receives equal, unobstructed road frontage along the adjacent path."),
            ("road_parallel", "विकल्प 3: लम्बवत् सीमांकन (Road-Parallel Division — Rule 109(5)(a,f))",
             "Partitions parcels parallel to the existing roadway or drainage channel alignment.")
        ]

        self.partition_plans = []

        for strat, strat_title, strat_desc in strategy_specs:
            try:
                lots, meta = generate_plan(
                    self.plot_geom, parties, zones=[],
                    strategy=strat, road=self.roads_geom, seed=0
                )
                eval_res = evaluate(lots, parties, self.plot_geom, zones=[], roads=self.roads_geom)

                allotments = []
                for p in parties:
                    lot_poly = lots[p.id]
                    allotments.append({
                        "party_id": p.id,
                        "owner_name": p.name,
                        "share_fraction": f"{p.share:.4f}",
                        "share_percent": f"{p.share * 100:.2f}%",
                        "allotted_area_sqm": round(lot_poly.area, 2),
                        "allotted_area_ha": round(lot_poly.area / 10000.0, 4),
                        "compactness_score": round(4 * math.pi * lot_poly.area / max(lot_poly.length ** 2, 0.1), 3),
                        "touches_road": "हाँ (Yes)" if (self.roads_geom and lot_poly.distance(self.roads_geom) < 1.0) else "पहुंच मार्ग आवश्यक"
                    })

                audit_scores = []
                for r in eval_res:
                    audit_scores.append({
                        "rule_code": r.code,
                        "rule_name": r.name_en,
                        "rule_name_hi": r.name_hi,
                        "status": r.status.upper(),
                        "metric": r.metric,
                        "detail": r.detail
                    })

                self.partition_plans.append({
                    "strategy_key": strat,
                    "title": strat_title,
                    "description": strat_desc,
                    "allotments": allotments,
                    "statutory_compliance_audit": audit_scores
                })
            except Exception as e:
                self.partition_plans.append({
                    "strategy_key": strat,
                    "title": strat_title,
                    "error": str(e)
                })

        return self.partition_plans
