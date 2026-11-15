"""Cadastral Map Scale Precision & Area Uncertainty Model.

Models cartographic drawing error based on official cadastral map scale (e.g. 1:1698),
computes ground coordinate uncertainty bands, and governs area reconciliation
between Khatauni recorded area and surveyed map area under UP Revenue Code Rule 109(5).
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Optional, Tuple

from shapely.geometry import Polygon


@dataclass
class AreaUncertainty:
    scale_denominator: int         # e.g. 1698
    paper_line_thickness_mm: float # e.g. 0.25 mm standard cartographic pencil/pen line
    ground_linear_error_m: float   # e.g. 0.42 m at 1:1698
    polygon_perimeter_m: float     # Ground boundary length
    area_sqm: float                # Nominal area in sq m
    delta_area_sqm: float          # ± Area uncertainty band (sq m)
    relative_uncertainty_pct: float# e.g. ±1.8%
    area_min_sqm: float            # area - delta_area
    area_max_sqm: float            # area + delta_area
    area_ha: float                 # area in Hectares
    delta_area_ha: float           # delta area in Hectares

    def format_sqm(self) -> str:
        return f"{self.area_sqm:.1f} ± {self.delta_area_sqm:.1f} m² (±{self.relative_uncertainty_pct:.1f}%)"

    def format_ha(self) -> str:
        return f"{self.area_ha:.4f} ± {self.delta_area_ha:.4f} Ha"


def parse_scale_denominator(scale_str: str, default: int = 1698) -> int:
    """Parse '1:1698' or '1698' into an integer scale denominator."""
    if not scale_str:
        return default
    m = re.search(r"1\s*:\s*([0-9]+)", str(scale_str))
    if m:
        return int(m.group(1))
    digits = re.sub(r"[^\d]", "", str(scale_str))
    return int(digits) if digits else default


def compute_area_uncertainty(
    poly: Polygon,
    scale_str: str = "1:1698",
    paper_line_thickness_mm: float = 0.25
) -> AreaUncertainty:
    """Compute physical ground uncertainty band for a surveyed parcel.
    
    Mathematical Derivation:
      At scale 1:S, paper drafting error of thickness 't' mm corresponds to:
        Δx_ground = (t / 1000) * S  [metres]
      For a polygon with perimeter P, a boundary expansion/contraction of Δx_ground
      changes area by approximately:
        ΔArea ≈ (1/2) * P * Δx_ground
    """
    scale_s = parse_scale_denominator(scale_str)
    linear_err_m = (paper_line_thickness_mm / 1000.0) * scale_s

    p_len = poly.length
    area = poly.area

    delta_area = 0.5 * p_len * linear_err_m
    rel_pct = (delta_area / max(area, 1e-6)) * 100.0

    return AreaUncertainty(
        scale_denominator=scale_s,
        paper_line_thickness_mm=paper_line_thickness_mm,
        ground_linear_error_m=round(linear_err_m, 3),
        polygon_perimeter_m=round(p_len, 2),
        area_sqm=round(area, 2),
        delta_area_sqm=round(delta_area, 2),
        relative_uncertainty_pct=round(rel_pct, 2),
        area_min_sqm=round(max(0.0, area - delta_area), 2),
        area_max_sqm=round(area + delta_area, 2),
        area_ha=round(area / 10000.0, 6),
        delta_area_ha=round(delta_area / 10000.0, 6)
    )


def reconcile_record_vs_mapped(
    record_area_sqm: float,
    mapped_poly: Polygon,
    scale_str: str = "1:1698"
) -> Tuple[bool, AreaUncertainty, float, str]:
    """Reconcile Khatauni recorded area against surveyed cadastral map area.
    
    Returns:
      (is_reconciled, uncertainty_model, variance_sqm, status_message_hi)
    """
    u = compute_area_uncertainty(mapped_poly, scale_str=scale_str)
    variance_sqm = u.area_sqm - record_area_sqm
    variance_pct = (variance_sqm / max(record_area_sqm, 1e-6)) * 100.0

    # If record area falls inside the cartographic uncertainty band [area_min, area_max]:
    if u.area_min_sqm <= record_area_sqm <= u.area_max_sqm:
        msg = (
            f"मानचित्र क्षेत्रफल ({u.area_sqm:.1f} m²) खतौनी क्षेत्रफल ({record_area_sqm:.1f} m²) "
            f"के साथ नक्शा पैमाना {scale_str} की त्रुटि सीमा (±{u.delta_area_sqm:.1f} m²) में पूर्णतः सुसंगत है।"
        )
        return True, u, variance_sqm, msg

    direction = "अधिक" if variance_sqm > 0 else "कम"
    msg = (
        f"मानचित्र क्षेत्रफल खतौनी दर्ज क्षेत्रफल से {abs(variance_sqm):.1f} m² ({abs(variance_pct):.1f}%) {direction} है। "
        f"पैमाना त्रुटि सीमा (±{u.delta_area_sqm:.1f} m²) से अधिक विचलन होने पर नियम 109(5) के तहत आनुपातिक समायोजन लागू किया जाता है।"
    )
    return False, u, variance_sqm, msg
