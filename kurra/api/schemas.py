"""Typed Pydantic Schemas for SDM Kurra Dashboard API.

Generates complete OpenAPI spec for TypeScript code generation.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CoSharerInput(BaseModel):
    id: str = Field(..., description="Unique party ID")
    name: str = Field(..., description="Co-sharer name in Hindi/English")
    share: str = Field(..., description="Decreed fraction, percentage, or float (e.g. '1/2', '25%', '0.33')")
    color_hex: Optional[str] = Field(None, description="Assigned swatch color hex")
    color_name_hi: Optional[str] = Field(None, description="Official Hindi color name")
    possession_wkt: Optional[str] = Field(None, description="Existing possession polygon WKT if claimed")


class CaseMetadata(BaseModel):
    case_no: str = Field("116/2026", description="Revenue Court Case Number")
    court_name: str = Field("न्यायालय उपजिलाधिकारी", description="Presiding SDM Court")
    district_code: str = Field("165", description="LGD District Code")
    district_name: str = Field("जालौन", description="District Name")
    tehsil_code: str = Field("00854", description="LGD Tehsil Code")
    tehsil_name: str = Field("उरई", description="Tehsil Name")
    village_code: str = Field("151769", description="LGD Village Code")
    village_name: str = Field("इखलाशपुरा च0क्षे0", description="Village Name")
    plot_no: str = Field("57", description="Khasra / Plot Number")
    plaintiff: str = Field("वादी", description="Plaintiff Name")
    defendant: str = Field("प्रतिवादी", description="Defendant Name")


class AuditScorecard(BaseModel):
    tier: int
    tier_name: str
    code: str
    clause_ref: str
    legal_basis: str
    name_en: str
    name_hi: str
    status: str
    metric: str
    detail: str
    statutory_citation: str


class ProposedLot(BaseModel):
    party_id: str
    party_name: str
    share_nominal: float
    share_str: str
    area_sqm: float
    area_ha: float
    color_hex: str
    color_hi: str
    geojson: Dict[str, Any]
    wkt: str
    polsby_popper: float
    aspect_ratio: float
    road_frontage_m: float
    is_connected: bool


class PartitionScheme(BaseModel):
    scheme_id: str
    scheme_name_hi: str
    scheme_name_en: str
    description: str
    lots: List[ProposedLot]
    audit_results: List[AuditScorecard]
    all_passed: bool
    failure_reason: Optional[str] = None
    provenance: Dict[str, Any]


class ProposePlanRequest(BaseModel):
    district: str = "165"
    tehsil: str = "00854"
    village: str = "151769"
    plot_no: str = "57"
    parties: Optional[List[CoSharerInput]] = None
    sharers: Optional[List[CoSharerInput]] = None
    strategies: List[str] = ["compact", "frontage", "road_parallel"]
    seed: int = 7
    shared_path_width: Optional[float] = None
    shared_pathway: Optional[Dict[str, Any]] = None
    road_geometry_wkt: Optional[str] = None


class ProposePlanResponse(BaseModel):
    plot_no: str
    schemes: List[PartitionScheme]
    shares_valid: bool
    shares_message: str
    possession_overlap_matrix: Dict[str, Dict[str, float]] = Field(default_factory=dict)


class OverlapRequest(BaseModel):
    scheme_a_lots: Dict[str, str]  # party_id -> WKT
    scheme_b_lots: Dict[str, str]  # party_id -> WKT


class OverlapResponse(BaseModel):
    mean_overlap_pct: float
    party_overlaps: Dict[str, float]
    explanation: str


class LegalDraftRequest(BaseModel):
    case_info: CaseMetadata
    scheme: PartitionScheme


class LegalDraftResponse(BaseModel):
    lekhpal_report_hi: str
    preliminary_decree_hi: str


class CustomCutRequest(BaseModel):
    district: str = "165"
    tehsil: str = "00854"
    village: str = "151769"
    plot_no: str = "57"
    cut_lines: List[List[List[float]]] = Field(..., description="List of [[x1, y1], [x2, y2]] lines in plot coordinates")
    parties: List[CoSharerInput]


class CustomCutResponse(BaseModel):
    scheme: PartitionScheme
    success: bool
    message: str

