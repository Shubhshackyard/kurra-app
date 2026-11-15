"""Plot Report Parser for UP Bhunaksha ("भूमि का विवरण").

Parses cadastral plot reports containing header administrative location,
scale, north arrow, sub-plots under different Khatas, owner details,
and computes parcel boundary adjacency for the Chauhaddi.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from shapely.geometry import Polygon, shape


@dataclass
class OwnerRecord:
    khata_no: str
    serial_no: int
    name: str
    guardian: Optional[str]  # None if "---" or not recorded
    residence: str           # e.g. "नि.ग्राम"


@dataclass
class SubPlotRecord:
    sub_plot_no: str        # e.g. "57/2", "57/1", or "57"
    base_plot_no: str       # e.g. "57"
    sub_div: Optional[str]  # e.g. "2", "1", or None
    khata_no: str           # e.g. "00087"
    area_ha: float          # e.g. 0.134000
    area_sqm: float         # e.g. 1340.0
    owners: List[OwnerRecord] = field(default_factory=list)


@dataclass
class AdjacentNeighbor:
    plot_no: str            # e.g. "58", "56", "51/318"
    side: str               # "उत्तर (North)", "पूर्व (East)", etc.
    shared_length_m: float  # Length of boundary contact in metres
    touches_type: str       # "shared_edge" or "corner_touch"
    land_class: str = ""    # e.g. "रास्ता (Roadway)", "कृषि (Agricultural)"


@dataclass
class PlotReportData:
    district_code: str
    district_name: str
    tehsil_code: str
    tehsil_name: str
    village_code: str
    village_name: str
    khasra_no: str
    scale: str
    total_area_ha: float
    total_area_sqm: float
    sub_plots: List[SubPlotRecord] = field(default_factory=list)
    adjacencies: List[AdjacentNeighbor] = field(default_factory=list)
    raw_header: str = ""
    raw_plot_info: str = ""
    map_image_b64: Optional[str] = None
    map_image_path: Optional[str] = None
    fetched_at: str = ""
    source_url: str = ""
    sha256: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def parse_header_attribution(attr_text: str) -> Dict[str, str]:
    """Parse 'जिला : 165 जालौन, तहसील : 00854 उरई, गाँव : 151769 इखलाशपुरा च0क्षे0'.
    
    Robust against spacing, punctuation variations, and newlines.
    """
    clean_text = attr_text.replace("\n", " ").strip()
    res = {
        "district_code": "", "district_name": "",
        "tehsil_code": "", "tehsil_name": "",
        "village_code": "", "village_name": ""
    }

    # Match जिला : <code> <name>
    m_dist = re.search(r"जिला\s*[:\-]\s*(\d+)\s+([^,]+?)(?:,|$)", clean_text)
    if m_dist:
        res["district_code"] = m_dist.group(1).strip()
        res["district_name"] = m_dist.group(2).strip()

    # Match तहसील : <code> <name>
    m_teh = re.search(r"तहसील\s*[:\-]\s*(\d+)\s+([^,]+?)(?:,|$)", clean_text)
    if m_teh:
        res["tehsil_code"] = m_teh.group(1).strip()
        res["tehsil_name"] = m_teh.group(2).strip()

    # Match गाँव : <code> <name>
    m_vil = re.search(r"(?:गाँव|ग्राम)\s*[:\-]\s*(\d+)\s+([^,]+?)(?:,|$)", clean_text)
    if m_vil:
        res["village_code"] = m_vil.group(1).strip()
        res["village_name"] = m_vil.group(2).strip()

    return res


def parse_plot_info_text(raw_text: str, base_plot_no: str) -> List[SubPlotRecord]:
    """Parse PlotInfo rows and Owner Details per Khata.
    
    Handles:
    1. Multi-Khata / Multi-Subplot rows:
       Khata No: 00087   Plot No: 57/2    Area : 0.134000 Hectare
       Khata No: 00146   Plot No: 57/1    Area : 0.239000 Hectare
    2. Owner sections:
       Owner Details For Khata No.:- 00087
       1 :-  नाम :   जगदीश प्रसाद     संरक्षक का नाम : राम रतन     निवास स्थान : नि.ग्राम
       ...
       Owner Details For Khata No.:- 00146
       1 :-  नाम :   बंजर     संरक्षक का नाम : ---     निवास स्थान : नि.ग्राम
    """
    sub_plots_map: Dict[str, SubPlotRecord] = {}
    khata_owners_map: Dict[str, List[OwnerRecord]] = {}

    # 1. Parse Sub-plot entries
    # Matches: Khata No: <no> Plot No: <plot> Area : <ha> Hectare
    row_pattern = re.compile(
        r"Khata\s*No\s*:\s*([0-9]+)\s+Plot\s*No\s*:\s*([0-9\/\w\-]+)\s+Area\s*:\s*([0-9\.]+)\s*Hectare",
        re.IGNORECASE
    )

    for km in row_pattern.finditer(raw_text):
        khata_no = km.group(1).strip()
        plot_str = km.group(2).strip()
        area_ha = float(km.group(3).strip())
        area_sqm = round(area_ha * 10000.0, 2)

        sub_div = None
        if "/" in plot_str:
            parts = plot_str.split("/", 1)
            sub_div = parts[1].strip()

        sp = SubPlotRecord(
            sub_plot_no=plot_str,
            base_plot_no=base_plot_no,
            sub_div=sub_div,
            khata_no=khata_no,
            area_ha=area_ha,
            area_sqm=area_sqm,
            owners=[]
        )
        sub_plots_map[khata_no] = sp

    # 2. Parse Owner Details per Khata No
    # Split text into khata blocks
    khata_sections = re.split(r"Owner\s*Details\s*For\s*Khata\s*No\.?\s*[:-]+\s*([0-9]+)", raw_text, flags=re.IGNORECASE)
    # Result has alternating [preamble, khata_no_1, text_1, khata_no_2, text_2, ...]
    if len(khata_sections) > 1:
        for i in range(1, len(khata_sections), 2):
            khata_num = khata_sections[i].strip()
            block_text = khata_sections[i + 1] if (i + 1) < len(khata_sections) else ""
            owners_list: List[OwnerRecord] = []

            # Match lines: 1 :- नाम : <name> संरक्षक का नाम : <guardian> निवास स्थान : <residence>
            owner_pattern = re.compile(
                r"(\d+)\s*[:\-]+\s*नाम\s*:\s*(.*?)\s*संरक्षक\s*का\s*नाम\s*:\s*(.*?)\s*निवास\s*स्थान\s*:\s*([^\n\r]+)"
            )
            for om in owner_pattern.finditer(block_text):
                s_no = int(om.group(1).strip())
                name = om.group(2).strip()
                guardian_raw = om.group(3).strip()
                residence = om.group(4).strip()

                guardian = None if (guardian_raw in ("---", "--", "-", "None", "")) else guardian_raw

                owners_list.append(OwnerRecord(
                    khata_no=khata_num,
                    serial_no=s_no,
                    name=name,
                    guardian=guardian,
                    residence=residence
                ))

            khata_owners_map[khata_num] = owners_list

    # 3. Associate owners to sub-plots
    for k_no, sp in sub_plots_map.items():
        if k_no in khata_owners_map:
            sp.owners = khata_owners_map[k_no]

    # Fallback if no sub-plot pattern matched but plain area and owners exist
    if not sub_plots_map:
        am = re.search(r"Area\s*:\s*([0-9\.]+)\s*Hectare", raw_text, re.IGNORECASE)
        area_ha = float(am.group(1)) if am else 0.0
        km = re.search(r"Khata\s*No\s*:\s*([0-9]+)", raw_text, re.IGNORECASE)
        k_no = km.group(1) if km else "00001"
        fallback_owners = khata_owners_map.get(k_no, [])
        if not fallback_owners:
            raw_owners = re.findall(r"नाम\s*:\s*([^\n\r]+?)(?:\s+संरक्षक|\s*$)", raw_text)
            for idx, o in enumerate(raw_owners, start=1):
                o_str = o.strip()
                if o_str and o_str != "---":
                    fallback_owners.append(OwnerRecord(
                        khata_no=k_no, serial_no=idx, name=o_str, guardian=None, residence="नि.ग्राम"
                    ))
        sp = SubPlotRecord(
            sub_plot_no=base_plot_no,
            base_plot_no=base_plot_no,
            sub_div=None,
            khata_no=k_no,
            area_ha=area_ha,
            area_sqm=round(area_ha * 10000.0, 2),
            owners=fallback_owners
        )
        sub_plots_map[k_no] = sp

    return list(sub_plots_map.values())


def outward_normal_direction(centroid_x: float, centroid_y: float,
                             edge_mid_x: float, edge_mid_y: float) -> str:
    """Classify the cardinal/ordinal direction of an outward normal from polygon centroid."""
    dx = edge_mid_x - centroid_x
    dy = edge_mid_y - centroid_y
    ang = math.degrees(math.atan2(dy, dx))

    if 67.5 <= ang < 112.5:
        return "उत्तर (North)"
    if 22.5 <= ang < 67.5:
        return "उत्तर-पूर्व (North-East)"
    if -22.5 <= ang < 22.5:
        return "पूर्व (East)"
    if -67.5 <= ang < -22.5:
        return "दक्षिण-पूर्व (South-East)"
    if -112.5 <= ang < -67.5:
        return "दक्षिण (South)"
    if -157.5 <= ang < -112.5:
        return "दक्षिण-पश्चिम (South-West)"
    if 112.5 <= ang < 157.5:
        return "उत्तर-पश्चिम (North-West)"
    return "पश्चिम (West)"


def compute_adjacency(target_poly: Polygon, features: List[dict],
                      target_plot_no: str, corner_threshold_m: float = 1.5) -> List[AdjacentNeighbor]:
    """Compute directional adjacency list for Chauhaddi using outward normal vectors."""
    adjacencies: List[AdjacentNeighbor] = []
    c = target_poly.centroid

    for ft in features:
        p_no = str(ft.get("properties", {}).get("plot_no", "")).strip()
        if not p_no or p_no == target_plot_no:
            continue

        geom = ft.get("geometry")
        if not geom:
            continue

        try:
            poly = shape(geom)
        except Exception:
            continue

        land_class = ft.get("properties", {}).get("land_class", "")

        # 1. Direct shared boundary contact
        inter = target_poly.intersection(poly)
        if not inter.is_empty and inter.length > 0.1:
            edge_mid = inter.centroid
            direction = outward_normal_direction(c.x, c.y, edge_mid.x, edge_mid.y)
            adjacencies.append(AdjacentNeighbor(
                plot_no=p_no,
                side=direction,
                shared_length_m=round(inter.length, 2),
                touches_type="shared_edge",
                land_class=land_class
            ))
            continue

        # 2. Corner touch / point contact within threshold
        dist = target_poly.distance(poly)
        if dist <= corner_threshold_m:
            other_centroid = poly.centroid
            direction = outward_normal_direction(c.x, c.y, other_centroid.x, other_centroid.y)
            adjacencies.append(AdjacentNeighbor(
                plot_no=p_no,
                side=direction,
                shared_length_m=0.0,
                touches_type="corner_touch",
                land_class=land_class
            ))

    # Sort primarily by shared length descending, then by plot number
    adjacencies.sort(key=lambda a: (-a.shared_length_m, a.plot_no))
    return adjacencies


def build_plot_report(
    district_code: str,
    district_name: str,
    tehsil_code: str,
    tehsil_name: str,
    village_code: str,
    village_name: str,
    plot_no: str,
    scale: str,
    raw_plot_info: str,
    raw_header: str = "",
    map_image_b64: Optional[str] = None,
    map_image_path: Optional[str] = None,
    features: Optional[List[dict]] = None,
    target_poly: Optional[Polygon] = None,
    source_url: str = ""
) -> PlotReportData:
    """Construct full structured PlotReportData from components."""
    base_plot_no = str(plot_no).strip()
    sub_plots = parse_plot_info_text(raw_plot_info, base_plot_no)

    total_area_ha = round(sum(sp.area_ha for sp in sub_plots), 6)
    total_area_sqm = round(sum(sp.area_sqm for sp in sub_plots), 2)

    adjacencies: List[AdjacentNeighbor] = []
    if target_poly and features:
        adjacencies = compute_adjacency(target_poly, features, base_plot_no)

    now_iso = datetime.utcnow().isoformat() + "Z"
    sha = hashlib.sha256((raw_header + raw_plot_info + (map_image_b64 or "")).encode("utf-8")).hexdigest()

    return PlotReportData(
        district_code=district_code,
        district_name=district_name,
        tehsil_code=tehsil_code,
        tehsil_name=tehsil_name,
        village_code=village_code,
        village_name=village_name,
        khasra_no=base_plot_no,
        scale=scale,
        total_area_ha=total_area_ha,
        total_area_sqm=total_area_sqm,
        sub_plots=sub_plots,
        adjacencies=adjacencies,
        raw_header=raw_header,
        raw_plot_info=raw_plot_info,
        map_image_b64=map_image_b64,
        map_image_path=map_image_path,
        fetched_at=now_iso,
        source_url=source_url,
        sha256=sha
    )
