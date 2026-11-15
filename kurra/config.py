"""Statutory & Policy Configuration for UP Revenue Code Rule 109(5).

Thresholds and parameters are explicitly categorized into:
- [statutory]: Explicitly mandated by UP Revenue Code 2006 or Rules 2016.
- [case-law]: Established by Board of Revenue or High Court precedents.
- [policy]: Administrative / policy decisions (e.g. road access classification).
- [heuristic]: Algorithmic / computational thresholds (editable in settings).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

STATE_CODE = "09"  # Uttar Pradesh

DEFAULT_LOCATION = {
    "district": ("165", "जालौन"),
    "tehsil": ("00854", "उरई"),
    "village": ("151769", "इखलाशपुरा च0क्षे0"),
    "plot": "57",
}

PROJECTED_EPSG = 32644  # UTM zone 44N


# Official 12 revenue court partition colors
OFFICIAL_KURRA_COLORS = [
    {"name_hi": "लाल", "name_en": "Red", "hex": "#dc2626"},
    {"name_hi": "हरा", "name_en": "Green", "hex": "#16a34a"},
    {"name_hi": "पीला", "name_en": "Yellow", "hex": "#eab308"},
    {"name_hi": "नीला", "name_en": "Blue", "hex": "#2563eb"},
    {"name_hi": "गुलाबी", "name_en": "Pink", "hex": "#ec4899"},
    {"name_hi": "नारंगी", "name_en": "Orange", "hex": "#ea580c"},
    {"name_hi": "बैंगनी", "name_en": "Purple", "hex": "#9333ea"},
    {"name_hi": "आस्मानी", "name_en": "Sky Blue", "hex": "#0284c7"},
    {"name_hi": "कत्थई", "name_en": "Brown", "hex": "#78350f"},
    {"name_hi": "काला", "name_en": "Black", "hex": "#1f2937"},
    {"name_hi": "धानी", "name_en": "Light Green", "hex": "#84cc16"},
    {"name_hi": "स्लेटी", "name_en": "Grey", "hex": "#64748b"}
]


# Road Hierarchy [policy, not statute]
ROAD_HIERARCHY: Dict[str, Dict[str, Any]] = {
    "expressway": {
        "access_allowed": False,
        "weight": 0.0,
        "label_hi": "एक्सप्रेसवे (प्रवेश प्रतिबंधित / No Access)",
        "category": "policy",
        "description": "Expressways have controlled access; parcels cannot take direct road frontage."
    },
    "highway": {
        "access_allowed": True,
        "weight": 1.5,
        "label_hi": "राष्ट्रीय / राज्य राजमार्ग (Highway)",
        "category": "policy",
        "description": "Commercial frontage premium applies."
    },
    "village_road": {
        "access_allowed": True,
        "weight": 1.2,
        "label_hi": "पक्की सड़क / संपर्क मार्ग (Village Road)",
        "category": "policy",
        "description": "Standard vehicular road access."
    },
    "chakroad": {
        "access_allowed": True,
        "weight": 1.0,
        "label_hi": "चकमार्ग / चक रोड (Chak Road)",
        "category": "policy",
        "description": "Official agricultural field pathway demarcated in revenue map."
    },
    "pathway": {
        "access_allowed": True,
        "weight": 0.8,
        "label_hi": "रास्ता / पगडंडी (Pathway)",
        "category": "policy",
        "description": "Pedestrian and cattle pathway."
    },
    "drain": {
        "access_allowed": False,
        "weight": 0.0,
        "label_hi": "नाली / नहर / गूल (Drain / Canal)",
        "category": "policy",
        "description": "Irrigation channel only; does not provide legal road ingress/egress."
    }
}


@dataclass
class Tolerances:
    # Tier 3 (a): Proportional share tolerance [heuristic]
    share_tol: float = 0.02          # ±2% maximum relative area/value deviation

    # Guardrail: Minimum lot width in metres [heuristic - agronomic tractor width]
    min_width_m: float = 4.0         # 4.0 m minimum for cultivation access

    # Tier 3 (b): Minimum Polsby-Popper compactness [heuristic]
    min_compactness: float = 0.35    # 0.35 threshold for green compactness

    # Maximum aspect ratio length:width [case-law]
    max_aspect_ratio: float = 4.0    # 1:4 maximum aspect ratio to prevent ribbon strips

    # Tier 3 (f): Frontage allocation tolerance [heuristic]
    frontage_tol: float = 0.35       # ±35% deviation in road frontage share

    # Tier 2: Separate possession shortfall tolerance [statutory/heuristic]
    possession_tol: float = 0.02     # Maximum 2% shortfall from established possession

    # Shared pathway settings [statutory / policy]
    shared_path_default_enabled: bool = False
    shared_path_width_m: float = 3.0 # 3.0 m width for agricultural tractor passage

    # Cartographic drawing line thickness on paper map (mm) [heuristic]
    paper_line_thickness_mm: float = 0.25
