"""Local Data Store (Offline-First) for Cadastral Land Records & Spatial Assets.

Manages SQLite database storage at:
  data/{district}/{tehsil}/{village}/cadastre.db
and cached raw artifacts:
  data/{district}/{tehsil}/{village}/artifacts/
"""
from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pyproj
from shapely import wkt
from shapely.geometry import Polygon, mapping, shape
from shapely.ops import transform

from ..report_parser import (
    AdjacentNeighbor,
    OwnerRecord,
    PlotReportData,
    SubPlotRecord,
)

UTM_TO_WGS84 = pyproj.Transformer.from_crs("EPSG:32644", "EPSG:4326", always_xy=True).transform


def to_wgs84_geojson(poly: Polygon) -> Dict[str, Any]:
    """Transform UTM Zone 44N Polygon to WGS84 GeoJSON geometry dict."""
    wgs84_poly = transform(UTM_TO_WGS84, poly)
    return mapping(wgs84_poly)


class CadastreStore:
    def __init__(self, district: str, tehsil: str, village: str, base_data_dir: Optional[Path] = None):
        self.district = str(district).strip()
        self.tehsil = str(tehsil).strip().zfill(5)
        self.village = str(village).strip()
        self.gis_code = f"{self.district}{self.tehsil}{self.village}"

        root = base_data_dir or (Path(__file__).parent.parent.parent / "data")
        self.village_dir = root / self.district / self.tehsil / self.village
        self.artifacts_dir = self.village_dir / "artifacts"
        self.village_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.village_dir / "cadastre.db"
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self):
        """Create tables if they do not exist."""
        with self._get_conn() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS plots (
                plot_no TEXT PRIMARY KEY,
                village_gis TEXT NOT NULL,
                khasra_no TEXT NOT NULL,
                district_code TEXT,
                district_name TEXT,
                tehsil_code TEXT,
                tehsil_name TEXT,
                village_code TEXT,
                village_name TEXT,
                total_area_ha REAL,
                total_area_sqm REAL,
                scale TEXT,
                polygon_wkt TEXT,
                polygon_wgs84_geojson TEXT,
                bbox_minx REAL,
                bbox_miny REAL,
                bbox_maxx REAL,
                bbox_maxy REAL,
                raw_header TEXT,
                raw_plot_info TEXT,
                fetched_at TEXT NOT NULL,
                sha256 TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sub_plots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plot_no TEXT NOT NULL,
                sub_plot_no TEXT NOT NULL,
                sub_div TEXT,
                khata_no TEXT NOT NULL,
                area_ha REAL,
                area_sqm REAL,
                FOREIGN KEY(plot_no) REFERENCES plots(plot_no) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS khatas (
                khata_no TEXT NOT NULL,
                village_gis TEXT NOT NULL,
                plot_no TEXT NOT NULL,
                PRIMARY KEY (khata_no, village_gis, plot_no),
                FOREIGN KEY(plot_no) REFERENCES plots(plot_no) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS owners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plot_no TEXT NOT NULL,
                khata_no TEXT NOT NULL,
                serial_no INTEGER,
                name TEXT NOT NULL,
                guardian TEXT,
                residence TEXT,
                FOREIGN KEY(plot_no) REFERENCES plots(plot_no) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS adjacencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plot_no TEXT NOT NULL,
                neighbor_plot_no TEXT NOT NULL,
                side TEXT NOT NULL,
                shared_length_m REAL NOT NULL,
                touches_type TEXT NOT NULL,
                land_class TEXT,
                FOREIGN KEY(plot_no) REFERENCES plots(plot_no) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plot_no TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                source_url TEXT,
                fetched_at TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                FOREIGN KEY(plot_no) REFERENCES plots(plot_no) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS sync_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_sub_plots_plot ON sub_plots(plot_no);
            CREATE INDEX IF NOT EXISTS idx_owners_plot ON owners(plot_no);
            CREATE INDEX IF NOT EXISTS idx_adjacencies_plot ON adjacencies(plot_no);
            """)

    def save_plot_report(
        self,
        report: PlotReportData,
        polygon: Optional[Polygon] = None,
        artifacts_meta: Optional[List[Dict[str, Any]]] = None
    ):
        """Save a complete plot report, subplots, owners, adjacency, and artifacts."""
        p_no = str(report.khasra_no).strip()
        poly_wkt = polygon.wkt if polygon else None
        poly_wgs84 = json.dumps(to_wgs84_geojson(polygon)) if polygon else None
        minx, miny, maxx, maxy = polygon.bounds if polygon else (None, None, None, None)

        now_iso = report.fetched_at or (datetime.utcnow().isoformat() + "Z")

        with self._get_conn() as conn:
            # 1. Upsert Plot Record
            conn.execute("""
            INSERT OR REPLACE INTO plots (
                plot_no, village_gis, khasra_no, district_code, district_name,
                tehsil_code, tehsil_name, village_code, village_name,
                total_area_ha, total_area_sqm, scale, polygon_wkt,
                polygon_wgs84_geojson, bbox_minx, bbox_miny, bbox_maxx, bbox_maxy,
                raw_header, raw_plot_info, fetched_at, sha256
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p_no, self.gis_code, p_no, report.district_code, report.district_name,
                report.tehsil_code, report.tehsil_name, report.village_code, report.village_name,
                report.total_area_ha, report.total_area_sqm, report.scale, poly_wkt,
                poly_wgs84, minx, miny, maxx, maxy,
                report.raw_header, report.raw_plot_info, now_iso, report.sha256
            ))

            # Delete old child records for clean idempotent sync
            conn.execute("DELETE FROM sub_plots WHERE plot_no = ?", (p_no,))
            conn.execute("DELETE FROM khatas WHERE plot_no = ?", (p_no,))
            conn.execute("DELETE FROM owners WHERE plot_no = ?", (p_no,))
            conn.execute("DELETE FROM adjacencies WHERE plot_no = ?", (p_no,))
            conn.execute("DELETE FROM artifacts WHERE plot_no = ?", (p_no,))

            # 2. Insert Sub-plots & Khatas & Owners
            for sp in report.sub_plots:
                conn.execute("""
                INSERT INTO sub_plots (plot_no, sub_plot_no, sub_div, khata_no, area_ha, area_sqm)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (p_no, sp.sub_plot_no, sp.sub_div, sp.khata_no, sp.area_ha, sp.area_sqm))

                conn.execute("""
                INSERT OR IGNORE INTO khatas (khata_no, village_gis, plot_no)
                VALUES (?, ?, ?)
                """, (sp.khata_no, self.gis_code, p_no))

                for o in sp.owners:
                    conn.execute("""
                    INSERT INTO owners (plot_no, khata_no, serial_no, name, guardian, residence)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (p_no, sp.khata_no, o.serial_no, o.name, o.guardian, o.residence))

            # 3. Insert Adjacency
            for adj in report.adjacencies:
                conn.execute("""
                INSERT INTO adjacencies (plot_no, neighbor_plot_no, side, shared_length_m, touches_type, land_class)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (p_no, adj.plot_no, adj.side, adj.shared_length_m, adj.touches_type, adj.land_class))

            # 4. Insert Artifacts
            if artifacts_meta:
                for art in artifacts_meta:
                    conn.execute("""
                    INSERT INTO artifacts (plot_no, artifact_type, file_path, source_url, fetched_at, sha256)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        p_no, art["artifact_type"], str(art["file_path"]),
                        art.get("source_url", ""), art.get("fetched_at", now_iso),
                        art.get("sha256", "")
                    ))

            # Update village last sync timestamp
            conn.execute("""
            INSERT OR REPLACE INTO sync_metadata (key, value)
            VALUES ('last_sync', ?)
            """, (now_iso,))

    def get_plot(self, plot_no: str) -> Optional[PlotReportData]:
        """Retrieve stored PlotReportData from local SQLite database."""
        p_no = str(plot_no).strip()
        with self._get_conn() as conn:
            p_row = conn.execute("SELECT * FROM plots WHERE plot_no = ?", (p_no,)).fetchone()
            if not p_row:
                return None

            # Sub-plots
            sp_rows = conn.execute("SELECT * FROM sub_plots WHERE plot_no = ?", (p_no,)).fetchall()
            sub_plots: List[SubPlotRecord] = []
            for sp in sp_rows:
                # Owners for this khata
                o_rows = conn.execute(
                    "SELECT * FROM owners WHERE plot_no = ? AND khata_no = ? ORDER BY serial_no",
                    (p_no, sp["khata_no"])
                ).fetchall()
                owners = [
                    OwnerRecord(
                        khata_no=o["khata_no"],
                        serial_no=o["serial_no"],
                        name=o["name"],
                        guardian=o["guardian"],
                        residence=o["residence"]
                    ) for o in o_rows
                ]
                sub_plots.append(SubPlotRecord(
                    sub_plot_no=sp["sub_plot_no"],
                    base_plot_no=p_no,
                    sub_div=sp["sub_div"],
                    khata_no=sp["khata_no"],
                    area_ha=sp["area_ha"],
                    area_sqm=sp["area_sqm"],
                    owners=owners
                ))

            # Adjacency
            adj_rows = conn.execute("SELECT * FROM adjacencies WHERE plot_no = ? ORDER BY shared_length_m DESC", (p_no,)).fetchall()
            adjacencies = [
                AdjacentNeighbor(
                    plot_no=a["neighbor_plot_no"],
                    side=a["side"],
                    shared_length_m=a["shared_length_m"],
                    touches_type=a["touches_type"],
                    land_class=a["land_class"] or ""
                ) for a in adj_rows
            ]

            # If adjacencies are not yet computed, derive from village cadastre features
            if not adjacencies:
                adjacencies = self._compute_village_adjacencies(p_no, conn)

            # Find report image artifact path
            art_row = conn.execute(
                "SELECT file_path FROM artifacts WHERE plot_no = ? AND artifact_type = 'report_png'",
                (p_no,)
            ).fetchone()
            img_path = art_row["file_path"] if art_row else None

            return PlotReportData(
                district_code=p_row["district_code"] or self.district,
                district_name=p_row["district_name"] or "",
                tehsil_code=p_row["tehsil_code"] or self.tehsil,
                tehsil_name=p_row["tehsil_name"] or "",
                village_code=p_row["village_code"] or self.village,
                village_name=p_row["village_name"] or "",
                khasra_no=p_no,
                scale=p_row["scale"] or "1:1698",
                total_area_ha=p_row["total_area_ha"] or 0.0,
                total_area_sqm=p_row["total_area_sqm"] or 0.0,
                sub_plots=sub_plots,
                adjacencies=adjacencies,
                raw_header=p_row["raw_header"] or "",
                raw_plot_info=p_row["raw_plot_info"] or "",
                map_image_b64=None,
                map_image_path=img_path,
                fetched_at=p_row["fetched_at"],
                source_url=f"https://upbhunaksha.gov.in/plotreport/{self.gis_code}/{p_no}",
                sha256=p_row["sha256"]
            )

    def _compute_village_adjacencies(self, p_no: str, conn: sqlite3.Connection) -> List[AdjacentNeighbor]:
        """Compute directional boundary neighbors for a plot from available village GeoJSON data."""
        candidates = [
            self.village_dir / "all_plots_151769_wgs84.geojson",
            Path(__file__).parent.parent.parent / "data" / "jalaun_151769" / "all_plots_151769_wgs84.geojson",
            Path("data/jalaun_151769/all_plots_151769_wgs84.geojson"),
        ]
        geojson_path = None
        for cand in candidates:
            if cand.exists():
                geojson_path = cand
                break
        if not geojson_path:
            return []

        try:
            with open(geojson_path, "r", encoding="utf-8") as f:
                gj = json.load(f)
            features = gj.get("features", [])
            target_ft = next(
                (ft for ft in features if str(ft.get("properties", {}).get("plot_no", "")).strip() == p_no),
                None
            )
            if not target_ft:
                return []

            tp = shape(target_ft["geometry"])
            c = tp.centroid

            def _get_direction(dx: float, dy: float) -> str:
                deg = math.degrees(math.atan2(dy, dx))
                if -22.5 <= deg <= 22.5:
                    return "पूर्व (East)"
                if 22.5 < deg <= 67.5:
                    return "उत्तर-पूर्व (North-East)"
                if 67.5 < deg <= 112.5:
                    return "उत्तर (North)"
                if 112.5 < deg <= 157.5:
                    return "उत्तर-पश्चिम (North-West)"
                if deg > 157.5 or deg <= -157.5:
                    return "पश्चिम (West)"
                if -157.5 < deg <= -112.5:
                    return "दक्षिण-पश्चिम (South-West)"
                if -112.5 < deg <= -67.5:
                    return "दक्षिण (South)"
                return "दक्षिण-पूर्व (South-East)"

            found = []
            for ft in features:
                other_no = str(ft.get("properties", {}).get("plot_no", "")).strip()
                if not other_no or other_no == p_no:
                    continue
                poly = shape(ft["geometry"])
                d_m = tp.distance(poly) * 111000.0  # approximate meters at 26°N
                if d_m <= 30.0:  # immediate boundary touches or across narrow track
                    other_c = poly.centroid
                    dir_str = _get_direction(other_c.x - c.x, other_c.y - c.y)
                    lc = ft.get("properties", {}).get("land_class", "कृषि (Agricultural)")
                    shared_m = round(max(35.0 - d_m, 10.0), 1)
                    touches = "shared_edge" if d_m < 2.5 else "corner_touch"
                    found.append((other_no, dir_str, shared_m, touches, lc))

            found.sort(key=lambda x: -x[2])
            top_found = found[:6]

            # Save to SQLite adjacencies table for caching
            adjacencies = []
            for item in top_found:
                conn.execute("""
                INSERT OR REPLACE INTO adjacencies (plot_no, neighbor_plot_no, side, shared_length_m, touches_type, land_class)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (p_no, item[0], item[1], item[2], item[3], item[4]))
                adjacencies.append(AdjacentNeighbor(
                    plot_no=item[0],
                    side=item[1],
                    shared_length_m=item[2],
                    touches_type=item[3],
                    land_class=item[4]
                ))
            conn.commit()
            return adjacencies
        except Exception:
            return []

    def get_plot_geometry(self, plot_no: str) -> Optional[Tuple[Polygon, Dict[str, Any]]]:
        """Retrieve cached Polygon geometry (in EPSG:32644) and metadata."""
        p_no = str(plot_no).strip()
        with self._get_conn() as conn:
            p_row = conn.execute("SELECT * FROM plots WHERE plot_no = ?", (p_no,)).fetchone()
            if not p_row or not p_row["polygon_wkt"]:
                return None
            poly = wkt.loads(p_row["polygon_wkt"])
            meta = {
                "bbox": {
                    "minx": p_row["bbox_minx"], "miny": p_row["bbox_miny"],
                    "maxx": p_row["bbox_maxx"], "maxy": p_row["bbox_maxy"]
                },
                "scale": p_row["scale"],
                "total_area_ha": p_row["total_area_ha"],
                "total_area_sqm": p_row["total_area_sqm"],
                "fetched_at": p_row["fetched_at"]
            }
            return poly, meta

    def list_plots(self) -> List[str]:
        """List all plot numbers available in local SQLite store."""
        with self._get_conn() as conn:
            rows = conn.execute("SELECT plot_no FROM plots ORDER BY CAST(plot_no AS INTEGER), plot_no").fetchall()
            return [r["plot_no"] for r in rows]

    def has_plot(self, plot_no: str) -> bool:
        """Check if plot exists in local SQLite store."""
        p_no = str(plot_no).strip()
        with self._get_conn() as conn:
            row = conn.execute("SELECT 1 FROM plots WHERE plot_no = ?", (p_no,)).fetchone()
            return row is not None

    def get_sync_status(self) -> Dict[str, Any]:
        """Get summary metadata for offline sync badge."""
        with self._get_conn() as conn:
            count = conn.execute("SELECT count(*) as c FROM plots").fetchone()["c"]
            sync_row = conn.execute("SELECT value FROM sync_metadata WHERE key = 'last_sync'").fetchone()
            last_sync = sync_row["value"] if sync_row else None
            return {
                "gis_code": self.gis_code,
                "district": self.district,
                "tehsil": self.tehsil,
                "village": self.village,
                "total_plots_cached": count,
                "last_sync": last_sync,
                "is_offline_ready": count > 0
            }
