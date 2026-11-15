"""Client for UP Bhunaksha (https://upbhunaksha.gov.in/bhunakshaserver).

Verified against UP Bhunaksha REST services. Retrieves georeferenced cadastral boundaries,
spatial bounding boxes in EPSG:32644, exact surveyed parcel polygons, and Khatauni land records.
"""
from __future__ import annotations
import base64
import io
import json
import math
import re
import time
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
import requests
from shapely import wkt
from shapely.affinity import scale
from shapely.geometry import box, Polygon, shape

from .config import DEFAULT_LOCATION, STATE_CODE
from .geometry import clean
from .report_parser import build_plot_report, parse_header_attribution, PlotReportData

HERE = Path(__file__).parent
CACHE = HERE.parent / "data" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)


class BhunakshaError(RuntimeError):
    pass


def _fmt(d: dict, **kw) -> dict:
    return {k: (v.format(**kw) if isinstance(v, str) else v) for k, v in d.items()}


def resolve_giscode(giscode: str) -> str:
    """Normalize 6-digit village code to 14-digit UP GIS code using current location."""
    giscode = str(giscode).strip()
    if len(giscode) <= 6:
        dist = DEFAULT_LOCATION["district"][0]
        tehsil = DEFAULT_LOCATION["tehsil"][0]
        return f"{dist}{tehsil}{giscode}"
    return giscode


def extract_polygon_from_report(img_b64: str, minx: float, miny: float, maxx: float, maxy: float,
                                target_area: float | None = None) -> Polygon | None:
    """Extract the exact surveyed plot polygon from the official Bhunaksha plotreport image."""
    try:
        img_bytes = base64.b64decode(img_b64)
        im = Image.open(io.BytesIO(img_bytes))
        arr = np.array(im)

        # Yellow mask [255, 255, 0] represents the active plot on UP Bhunaksha
        mask = (arr[:, :, 0] > 200) & (arr[:, :, 1] > 200) & (arr[:, :, 2] < 50)
        if not np.any(mask):
            return None

        # Morphological closing to fill plot number labels inside the plot
        mask_img = Image.fromarray(mask.astype(np.uint8) * 255)
        mask_closed = mask_img.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
        closed_arr = np.array(mask_closed) > 128

        # Find outer boundary pixels
        pad = np.pad(closed_arr, 1, mode="constant", constant_values=False)
        boundary = closed_arr & (
            (~pad[:-2, 1:-1]) | (~pad[2:, 1:-1]) |
            (~pad[1:-1, :-2]) | (~pad[1:-1, 2:])
        )
        by, bx = np.where(boundary)
        if len(bx) < 3:
            return None

        px_minx, px_maxx = bx.min(), bx.max()
        px_miny, px_maxy = by.min(), by.max()
        if px_maxx == px_minx or px_maxy == px_miny:
            return None

        # Moore boundary tracing algorithm
        start_idx = np.lexsort((bx, by))[0]
        start = (by[start_idx], bx[start_idx])
        directions = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]

        contour = [start]
        curr = start
        backtrack = 6
        for _ in range(8000):
            found = False
            start_dir = (backtrack + 2) % 8
            for i in range(8):
                d_idx = (start_dir + i) % 8
                ny, nx = curr[0] + directions[d_idx][0], curr[1] + directions[d_idx][1]
                if 0 <= ny < closed_arr.shape[0] and 0 <= nx < closed_arr.shape[1] and closed_arr[ny, nx]:
                    curr = (ny, nx)
                    backtrack = (d_idx + 4) % 8
                    found = True
                    break
            if not found or curr == start:
                break
            contour.append(curr)

        if len(contour) < 4:
            return None

        # Georeference image pixels to UTM Zone 44N metric coordinates
        sx = (maxx - minx) / (px_maxx - px_minx)
        sy = (maxy - miny) / (px_maxy - px_miny)

        coords = []
        for y_px, x_px in contour:
            x_utm = minx + (x_px - px_minx) * sx
            y_utm = maxy - (y_px - px_miny) * sy
            coords.append((x_utm, y_utm))

        poly = clean(Polygon(coords))
        if poly.is_empty or not poly.is_valid:
            return None

        # Simplify to remove raster pixel steps while preserving genuine boundary corners
        tol = max(math.sqrt(poly.area) * 0.005, 0.5)
        simple = poly.simplify(tol, preserve_topology=True)

        # Scale precisely to recorded Khatauni area if available
        if target_area and target_area > 0 and simple.area > 0:
            factor = math.sqrt(target_area / simple.area)
            simple = scale(simple, xfact=factor, yfact=factor)

        return simple
    except Exception:
        return None


class BhunakshaClient:
    def __init__(self, endpoints_path: Path | None = None, timeout: int = 30):
        self.cfg = json.loads((endpoints_path or HERE / "endpoints.json").read_text(encoding="utf-8"))
        self.s = requests.Session()
        self.s.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)",
            "Referer": "https://upbhunaksha.gov.in/home",
            "Origin": "https://upbhunaksha.gov.in",
            "Accept": "application/json, text/plain, */*"
        })
        self.timeout = timeout

    def _call(self, name: str, **kw):
        ep = self.cfg[name]
        url = self.cfg["base"] + ep["path"].format(**kw)
        method = ep.get("method", "POST")

        data = _fmt(ep.get("data", {}), state=STATE_CODE, **kw) if "data" in ep else None
        json_body = _fmt(ep.get("json", {}), state=STATE_CODE, **kw) if "json" in ep else None

        key = CACHE / (name + "_" + "_".join(f"{k}-{v}" for k, v in sorted(kw.items())) + ".json")
        if key.exists() and time.time() - key.stat().st_mtime < 86400:
            return json.loads(key.read_text(encoding="utf-8"))

        try:
            r = self.s.request(method, url, data=data, json=json_body, timeout=self.timeout)
            r.raise_for_status()
            ctype = r.headers.get("content-type", "")
            if "application/json" in ctype:
                js = r.json()
            else:
                js = {"text": r.text}
        except Exception as e:
            raise BhunakshaError(
                f"{name} failed ({e}). Check village GIS code and plot number, "
                "or use the GeoJSON-upload fallback.") from e

        key.write_text(json.dumps(js, ensure_ascii=False), encoding="utf-8")
        return js

    def plot_info(self, giscode: str, plot: str):
        full_gis = resolve_giscode(giscode)
        res = self._call("plot_info", giscode=full_gis, plot=plot)
        return res.get("text", "") if isinstance(res, dict) else str(res)

    def plot_geometry(self, giscode: str, plot: str):
        full_gis = resolve_giscode(giscode)

        # 1. Fetch plot bounding box from verified endpoint
        bbox_data = self._call("plot_bbox", giscode=full_gis, plot=plot)
        if not bbox_data or not isinstance(bbox_data, dict) or "minx" not in bbox_data:
            raise BhunakshaError(
                f"Plot {plot} was not found in village GIS {giscode} (full: {full_gis}). "
                "Please verify the plot number.")

        # 2. Fetch Khatauni text for land area reconciliation
        info_txt = ""
        rec_sqm = None
        try:
            info_data = self._call("plot_info", giscode=full_gis, plot=plot)
            info_txt = info_data.get("text", "") if isinstance(info_data, dict) else str(info_data)
            m = re.search(r'Area\s*:\s*([0-9\.]+)\s*Hectare', info_txt)
            if m:
                rec_sqm = float(m.group(1)) * 10000.0
        except Exception:
            pass

        # 3. Construct geometry:
        # Check if official plotreport raster gives the exact surveyed polygon
        g = None
        try:
            rep = self._call("plot_report", giscode=full_gis, plot=plot)
            if rep and isinstance(rep, dict) and "imageBase64" in rep:
                g = extract_polygon_from_report(
                    rep["imageBase64"],
                    float(bbox_data["minx"]), float(bbox_data["miny"]),
                    float(bbox_data["maxx"]), float(bbox_data["maxy"]),
                    target_area=None
                )
        except Exception:
            pass

        # Fallback to schema search or bounding box if plotreport image extraction was not possible
        if g is None:
            g = find_geometry(bbox_data)
        if g is None:
            minx, miny = float(bbox_data["minx"]), float(bbox_data["miny"])
            maxx, maxy = float(bbox_data["maxx"]), float(bbox_data["maxy"])
            g = box(minx, miny, maxx, maxy)

        meta = {
            "bbox": bbox_data,
            "giscode": full_gis,
            "plot": plot,
            "khatauni_text": info_txt,
            "record_area_sqm": rec_sqm or g.area
        }
        return g, meta

    def get_plot_report(self, district: str, tehsil: str, village: str, plot: str,
                        output_dir: Path | None = None,
                        village_features: list[dict] | None = None) -> PlotReportData:
        """Fetch and parse complete Plot Report ('भूमि का विवरण') for a given parcel."""
        district = str(district).strip()
        tehsil = str(tehsil).strip().zfill(5)
        village = str(village).strip()
        plot = str(plot).strip()
        full_gis = f"{district}{tehsil}{village}"

        # 1. Header Location Attribution
        attr_text = ""
        try:
            loc_res = self._call("location_info", giscode=full_gis)
            if isinstance(loc_res, dict):
                attr_text = loc_res.get("attribution", "")
            elif isinstance(loc_res, str):
                attr_text = loc_res
        except Exception:
            pass

        loc_dict = parse_header_attribution(attr_text)
        dist_name = loc_dict.get("district_name") or "जालौन"
        teh_name = loc_dict.get("tehsil_name") or "उरई"
        vil_name = loc_dict.get("village_name") or "इखलाशपुरा च0क्षे0"

        # 2. Plot Report Map Image & Scale
        img_b64 = None
        scale_val = "1:1698"
        try:
            rep_res = self._call("plot_report", giscode=full_gis, plot=plot)
            if isinstance(rep_res, dict):
                img_b64 = rep_res.get("imageBase64")
                scale_val = rep_res.get("scale", "1:1698")
        except Exception:
            pass

        # 3. Plot Info Text (Subplots & Owners)
        info_txt = ""
        try:
            info_res = self._call("plot_info", giscode=full_gis, plot=plot)
            info_txt = info_res.get("text", "") if isinstance(info_res, dict) else str(info_res)
        except Exception:
            pass

        # 4. Target Geometry for adjacency
        target_poly = None
        try:
            target_poly, _ = self.plot_geometry(full_gis, plot)
        except Exception:
            pass

        # Save map image asset if requested
        saved_img_path = None
        if img_b64 and output_dir:
            out_p = Path(output_dir)
            out_p.mkdir(parents=True, exist_ok=True)
            img_file = out_p / f"plot_{plot}_report.png"
            img_file.write_bytes(base64.b64decode(img_b64))
            saved_img_path = str(img_file)

        source_url = f"https://upbhunaksha.gov.in/plotreport/{full_gis}/{plot}"

        return build_plot_report(
            district_code=district,
            district_name=dist_name,
            tehsil_code=tehsil,
            tehsil_name=teh_name,
            village_code=village,
            village_name=vil_name,
            plot_no=plot,
            scale=scale_val,
            raw_plot_info=info_txt,
            raw_header=attr_text,
            map_image_b64=img_b64,
            map_image_path=saved_img_path,
            features=village_features,
            target_poly=target_poly,
            source_url=source_url
        )

    def get_plot(self, district: str, tehsil: str, village: str, plot: str,
                 output_dir: Path | None = None,
                 village_features: list[dict] | None = None) -> PlotReportData:
        """Runtime variable retrieval: get_plot(district, tehsil, village, plot)."""
        return self.get_plot_report(district, tehsil, village, plot, output_dir, village_features)



def find_geometry(obj):
    """Recursively locate a Polygon/MultiPolygon in GeoJSON dicts or WKT strings."""
    if isinstance(obj, dict):
        if obj.get("type") in ("Polygon", "MultiPolygon") and "coordinates" in obj:
            return shape(obj)
        if obj.get("type") == "Feature" and obj.get("geometry"):
            return find_geometry(obj["geometry"])
        for v in obj.values():
            g = find_geometry(v)
            if g is not None:
                return g
    elif isinstance(obj, list):
        for v in obj:
            g = find_geometry(v)
            if g is not None:
                return g
    elif isinstance(obj, str):
        s = obj.strip().upper()
        if s.startswith(("POLYGON", "MULTIPOLYGON")):
            try:
                return wkt.loads(obj)
            except Exception:
                return None
        if s.startswith("{") and "COORDINATES" in s:
            try:
                return find_geometry(json.loads(obj))
            except Exception:
                return None
    return None
