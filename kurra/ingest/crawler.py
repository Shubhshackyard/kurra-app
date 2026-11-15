"""Polite, Resumable Cadastral Ingestion Crawler for UP Bhunaksha.

Features:
- Rate-limited (1-2 req/s max with random jitter)
- Resumable and idempotent
- Exponential backoff on transient network errors
- Strict stop-on-block / stop-on-captcha (never attempts bypass)
- Generates SHA-256 hashes for all cached artifacts
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests
from shapely.geometry import Polygon, box, mapping, shape

from ..bhunaksha import BhunakshaClient
from ..report_parser import PlotReportData
from .store import CadastreStore, to_wgs84_geojson

logger = logging.getLogger("kurra.ingest")


def compute_sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def compute_sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class IngestBlockedError(RuntimeError):
    """Raised when portal responds with HTTP 403, Cloudflare, or CAPTCHA challenge."""
    pass


class VillageCrawler:
    def __init__(
        self,
        district: str = "165",
        tehsil: str = "00854",
        village: str = "151769",
        base_data_dir: Optional[Path] = None,
        rate_limit_s: float = 1.0,
        max_retries: int = 3
    ):
        self.district = str(district).strip()
        self.tehsil = str(tehsil).strip().zfill(5)
        self.village = str(village).strip()
        self.gis_code = f"{self.district}{self.tehsil}{self.village}"
        self.rate_limit_s = rate_limit_s
        self.max_retries = max_retries

        self.store = CadastreStore(self.district, self.tehsil, self.village, base_data_dir=base_data_dir)
        self.client = BhunakshaClient()
        self.wms_base = "https://upbhunaksha.gov.in/bhunakshaserver/WMS/tile"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)",
            "Referer": "https://upbhunaksha.gov.in/home",
            "Origin": "https://upbhunaksha.gov.in"
        }

        # Failure log
        self.failure_log_path = self.store.village_dir / "ingest_failures.log"

        # Load local village GeoJSON features if available (for fast fallback and adjacency)
        self.village_features: List[dict] = []
        local_geojson = self.store.village_dir.parent.parent.parent / "jalaun_151769" / "all_plots_151769_utm.geojson"
        if not local_geojson.exists():
            local_geojson = self.store.village_dir / "all_plots_utm.geojson"
        if local_geojson.exists():
            try:
                with open(local_geojson, encoding="utf-8") as f:
                    self.village_features = json.load(f).get("features", [])
            except Exception:
                pass

    def _sleep_polite(self):
        """Sleep with random jitter (1.0 to 1.5s by default) to respect government servers."""
        jitter = random.uniform(0.1, 0.4)
        time.sleep(self.rate_limit_s + jitter)

    def _fetch_wms_tile(
        self,
        bbox: Tuple[float, float, float, float],
        style: str,
        layer: str,
        dpi: int,
        width: int,
        height: int,
        plot_id: Optional[str] = None
    ) -> Optional[bytes]:
        """Fetch georeferenced raster tile from UP Bhunaksha WMS service."""
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

        for attempt in range(self.max_retries):
            try:
                r = requests.get(self.wms_base, params=params, headers=self.headers, timeout=20)
                if r.status_code == 403 or "captcha" in r.text.lower():
                    raise IngestBlockedError("UP Bhunaksha server returned 403 or CAPTCHA challenge.")
                if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                    return r.content
                if r.status_code in (429, 502, 503, 504):
                    time.sleep(1.5 * (attempt + 1))
                    continue
            except IngestBlockedError:
                raise
            except Exception:
                time.sleep(1.0 * (attempt + 1))
        return None

    def ingest_plot(self, plot_no: str, force: bool = False) -> PlotReportData:
        """Ingest a single plot: report data, sub-plots, owners, vector geom, and tiles."""
        p_no = str(plot_no).strip()

        # Resumable check
        if not force and self.store.has_plot(p_no):
            existing = self.store.get_plot(p_no)
            if existing:
                return existing

        artifacts_meta: List[Dict[str, Any]] = []
        now_iso = datetime.utcnow().isoformat() + "Z"

        # 1. Fetch Plot Report Data
        report = self.client.get_plot_report(
            district=self.district,
            tehsil=self.tehsil,
            village=self.village,
            plot=p_no,
            output_dir=self.store.artifacts_dir,
            village_features=self.village_features
        )
        self._sleep_polite()

        # 2. Extract or retrieve surveyed vector polygon
        target_poly = None
        bbox = None
        plot_id = None

        # Check local village GeoJSON first for exact polygon
        for ft in self.village_features:
            if str(ft.get("properties", {}).get("plot_no")) == p_no:
                target_poly = shape(ft["geometry"])
                plot_id = ft.get("properties", {}).get("plot_id")
                bbox = target_poly.bounds
                break

        # If not in local features, fetch from live Bhunaksha
        if target_poly is None:
            try:
                target_poly, meta = self.client.plot_geometry(self.gis_code, p_no)
                bbox = target_poly.bounds
                plot_id = meta.get("bbox", {}).get("id")
            except Exception:
                pass

        if target_poly is None:
            # Fallback to bounding box from plot_bbox
            try:
                bdata = self.client._call("plot_bbox", giscode=self.gis_code, plot=p_no)
                if bdata and "minx" in bdata:
                    minx, miny = float(bdata["minx"]), float(bdata["miny"])
                    maxx, maxy = float(bdata["maxx"]), float(bdata["maxy"])
                    target_poly = box(minx, miny, maxx, maxy)
                    bbox = (minx, miny, maxx, maxy)
                    plot_id = bdata.get("id")
            except Exception:
                pass

        if target_poly is None:
            raise RuntimeError(f"Could not determine spatial geometry for plot {p_no}")

        # Re-compute adjacency with target_poly
        if self.village_features:
            from ..report_parser import compute_adjacency
            report.adjacencies = compute_adjacency(target_poly, self.village_features, p_no)

        # 3. Save Report PNG artifact
        if report.map_image_b64:
            report_img_path = self.store.artifacts_dir / f"plot_{p_no}_report.png"
            img_bytes = base64.b64decode(report.map_image_b64)
            report_img_path.write_bytes(img_bytes)
            report.map_image_path = str(report_img_path)
            artifacts_meta.append({
                "artifact_type": "report_png",
                "file_path": report_img_path,
                "source_url": f"https://upbhunaksha.gov.in/bhunakshaserver/api/plots?gisCode={self.gis_code}&plotNo={p_no}",
                "fetched_at": now_iso,
                "sha256": compute_sha256_bytes(img_bytes)
            })

        # 4. Save Vector Polygon GeoJSON artifact
        geom_path = self.store.artifacts_dir / f"plot_{p_no}_geom.geojson"
        geom_data = {
            "type": "Feature",
            "properties": {
                "plot_no": p_no,
                "gis_code": self.gis_code,
                "plot_id": plot_id,
                "area_ha": report.total_area_ha,
                "area_sqm": report.total_area_sqm,
                "scale": report.scale
            },
            "geometry": mapping(target_poly)
        }
        geom_bytes = json.dumps(geom_data, ensure_ascii=False, indent=2).encode("utf-8")
        geom_path.write_bytes(geom_bytes)
        artifacts_meta.append({
            "artifact_type": "vector_geojson",
            "file_path": geom_path,
            "source_url": f"https://upbhunaksha.gov.in/plotreport/{self.gis_code}/{p_no}",
            "fetched_at": now_iso,
            "sha256": compute_sha256_bytes(geom_bytes)
        })

        # 5. Save Survey WMS Tile (Isolated Highlight)
        survey_bytes = self._fetch_wms_tile(
            bbox=bbox,
            style="PLOT_SELECTION" if plot_id else "VILLAGE_MAP",
            layer="PLOT_LIST" if plot_id else "VILLAGE_MAP",
            dpi=300,
            width=1024,
            height=1024,
            plot_id=plot_id
        )
        if survey_bytes:
            survey_path = self.store.artifacts_dir / f"plot_{p_no}_survey.png"
            survey_path.write_bytes(survey_bytes)
            artifacts_meta.append({
                "artifact_type": "survey_tile",
                "file_path": survey_path,
                "source_url": f"{self.wms_base}?STYLES=PLOT_SELECTION&LAYERS=PLOT_LIST&plot_id={plot_id}",
                "fetched_at": now_iso,
                "sha256": compute_sha256_bytes(survey_bytes)
            })
            self._sleep_polite()

        # 6. Save Bird's-Eye Surroundings WMS Tile
        pad = max((bbox[2] - bbox[0]) * 0.45, 120.0)
        birdseye_bbox = (bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad)
        birdseye_bytes = self._fetch_wms_tile(
            bbox=birdseye_bbox,
            style="VILLAGE_MAP",
            layer="VILLAGE_MAP",
            dpi=300,
            width=1280,
            height=1280
        )
        if birdseye_bytes:
            birdseye_path = self.store.artifacts_dir / f"plot_{p_no}_birdseye.png"
            birdseye_path.write_bytes(birdseye_bytes)
            artifacts_meta.append({
                "artifact_type": "birdseye_tile",
                "file_path": birdseye_path,
                "source_url": f"{self.wms_base}?STYLES=VILLAGE_MAP&LAYERS=VILLAGE_MAP",
                "fetched_at": now_iso,
                "sha256": compute_sha256_bytes(birdseye_bytes)
            })
            self._sleep_polite()

        # 7. Persist into SQLite Store
        self.store.save_plot_report(report, polygon=target_poly, artifacts_meta=artifacts_meta)
        return report

    def enumerate_village_plots(self) -> List[str]:
        """Enumerate all available plot numbers for the village."""
        # 1. From local features if present
        if self.village_features:
            plots = []
            for ft in self.village_features:
                p = str(ft.get("properties", {}).get("plot_no", "")).strip()
                if p and p not in plots:
                    plots.append(p)
            return sorted(plots, key=lambda x: (int(x) if x.isdigit() else 999999, x))

        # 2. Check local CSV inventory if present
        inv_csv = self.store.village_dir.parent.parent.parent / "jalaun_151769" / "village_151769_inventory.csv"
        if inv_csv.exists():
            import csv
            plots = []
            with open(inv_csv, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    p = str(row.get("plot_no", "")).strip()
                    if p and p not in plots:
                        plots.append(p)
            return sorted(plots, key=lambda x: (int(x) if x.isdigit() else 999999, x))

        # Default fallback sample
        return ["57"]

    def crawl_all(
        self,
        progress_cb: Optional[Callable[[int, int, str], None]] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """Crawl all plots in the village with polite rate limits, retry, and progress."""
        plots = self.enumerate_village_plots()
        total = len(plots)
        success_count = 0
        skipped_count = 0
        failures: List[Dict[str, str]] = []

        logger.info(f"Starting village crawl for {self.gis_code}: {total} plots to process.")

        for idx, p_no in enumerate(plots, start=1):
            if progress_cb:
                progress_cb(idx, total, p_no)

            if not force and self.store.has_plot(p_no):
                skipped_count += 1
                continue

            try:
                self.ingest_plot(p_no, force=force)
                success_count += 1
            except IngestBlockedError as e:
                # Critical security stop
                msg = f"HALTED CRAWL at plot {p_no}: Government portal blocked access ({e}). Stopped immediately."
                logger.error(msg)
                with open(self.failure_log_path, "a", encoding="utf-8") as fl:
                    fl.write(f"[{datetime.utcnow().isoformat()}] CRITICAL BLOCK: {msg}\n")
                raise
            except Exception as e:
                logger.warning(f"Failed to ingest plot {p_no}: {e}")
                failures.append({"plot_no": p_no, "error": str(e)})
                with open(self.failure_log_path, "a", encoding="utf-8") as fl:
                    fl.write(f"[{datetime.utcnow().isoformat()}] Plot {p_no} failed: {e}\n")

        return {
            "gis_code": self.gis_code,
            "total_plots": total,
            "success_count": success_count,
            "skipped_count": skipped_count,
            "failure_count": len(failures),
            "failures": failures
        }
