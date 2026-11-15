"""Rule 109(5) UP Revenue Code Partition Audit Engine.

Evaluates partition schemes across three ordered statutory tiers:
- Tier 1 [statutory]: Consent & Private Family Settlement (Rule 109(5)(g))
- Tier 2 [statutory]: Maintenance of Existing Separate Possession (Rule 109(5)(e))
- Tier 3 [statutory/case-law/heuristic]: Statutory Balance
    (a) Proportionate Share (Area & Quality-weighted)
    (b) Compactness & Non-Fragmentation (avoiding scattered chaks)
    (c) Land Quality Mix (no party gets exclusively inferior/superior land)
    (d) Integrity of Existing Field Boundaries (Bunds/Medhs)
    (f) Proportionate Road, Pathway & Commercial Frontage
    (G1) Minimum Lot Width & Non-Sliver Agronomic Feasibility
    (G2) Direct Road Ingress/Egress Access

Every check is explicitly tagged with [statutory | case-law | heuristic | policy].
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from shapely.geometry import Polygon
from shapely.ops import unary_union

from .config import Tolerances
from .geometry import (
    aspect_ratio,
    clean,
    is_connected,
    min_width,
    n_parts,
    polsby_popper,
    value_of,
)


@dataclass
class RuleResult:
    tier: int               # 1, 2, or 3
    tier_name: str          # e.g. "टियर 1: पारिवारिक समझौता"
    code: str               # 'g', 'e', 'a', 'b', 'c', 'd', 'f', 'G1', 'G2'
    clause_ref: str         # "Rule 109(5)(g)", etc.
    legal_basis: str        # "[statutory]", "[case-law]", "[heuristic]", "[policy]"
    name_en: str
    name_hi: str
    status: str             # "green" | "amber" | "red" | "na"
    metric: str
    detail: str = ""
    statutory_citation: str = ""


ICON = {"green": "🟢", "amber": "🟡", "red": "🔴", "na": "⚪"}


def _grade(worst: float, green_limit: float, amber_limit: float) -> str:
    return "green" if worst <= green_limit else "amber" if worst <= amber_limit else "red"


def evaluate(
    lots: Dict[str, Polygon],
    parties: list,
    plot: Polygon,
    zones: tuple = (),
    roads=None,
    possession=None,
    settlement=None,
    units=None,
    tol: Optional[Tolerances] = None
) -> List[RuleResult]:
    """Execute tiered deterministic audit of partition lots under Rule 109(5)."""
    tol = tol or Tolerances()
    zones = list(zones)
    out: List[RuleResult] = []
    names = {p.id: p.name for p in parties}

    # Filter out internal helper lots like shared pathway
    clean_lots = {p.id: lots[p.id] for p in parties if p.id in lots}

    total_v = value_of(plot, zones)
    total_a = plot.area

    # =========================================================================
    # TIER 1: CONSENT & PRIVATE FAMILY SETTLEMENT (Clause g) [statutory]
    # =========================================================================
    if not settlement:
        out.append(RuleResult(
            tier=1,
            tier_name="टियर 1: आपसी समझौता",
            code="g",
            clause_ref="Rule 109(5)(g)",
            legal_basis="[statutory]",
            name_en="Family settlement / Consent",
            name_hi="पारिवारिक समझौता / आपसी सहमति",
            status="na",
            metric="कोई पंजीकृत / मान्य समझौता प्रस्तुत नहीं",
            detail="यदि पक्षकारों के बीच पूर्व सहमति है, तो कुर्रे उसी अनुसार तैयार किए जाएंगे।",
            statutory_citation="उ०प्र० राजस्व संहिता नियमावली 2016, नियम 109(5)(छ)"
        ))
    else:
        misses = {pid: 1.0 - (clean_lots[pid].intersection(g).area / max(g.area, 1e-6))
                  for pid, g in settlement.items() if pid in clean_lots}
        worst_miss = max(misses.values()) if misses else 0.0
        st = "green" if worst_miss < 0.005 else "red"
        out.append(RuleResult(
            tier=1,
            tier_name="टियर 1: आपसी समझौता",
            code="g",
            clause_ref="Rule 109(5)(g)",
            legal_basis="[statutory]",
            name_en="Family settlement / Consent",
            name_hi="पारिवारिक समझौता / आपसी सहमति",
            status=st,
            metric=f"अधिकतम विचलन: {worst_miss:.2%}",
            detail="पारिवारिक समझौते के अनुसार भू-भाग का शत-प्रतिशत आबंटन अनिवार्य है।" if st == "green"
                   else f"समझौते का उल्लंघन: {worst_miss:.1%} भाग समझौते से भिन्न आबंटित है।",
            statutory_citation="उ०प्र० राजस्व संहिता नियमावली 2016, नियम 109(5)(छ)"
        ))

    # =========================================================================
    # TIER 2: SEPARATE POSSESSION (Clause e) [statutory]
    # =========================================================================
    if not possession:
        out.append(RuleResult(
            tier=2,
            tier_name="टियर 2: पृथक कब्जा",
            code="e",
            clause_ref="Rule 109(5)(e)",
            legal_basis="[statutory]",
            name_en="Separate possession",
            name_hi="मौके का पृथक कब्जा",
            status="na",
            metric="कोई पृथक कब्जा लेयर उपलब्ध नहीं",
            detail="जहाँ तक संभव हो, खातेदारों का पुराना भौतिक कब्जा अक्षुण्ण रखा जाना चाहिए।",
            statutory_citation="उ०प्र० राजस्व संहिता नियमावली 2016, नियम 109(5)(ङ)"
        ))
    else:
        worst_cov = 0.0
        shortfalls = {}
        for pid, g in possession.items():
            if pid not in clean_lots or g.is_empty:
                continue
            pv = value_of(g, zones)
            p_share = next((p.share for p in parties if p.id == pid), 0.0)
            expect = min(1.0, p_share * total_v / max(pv, 1e-9))
            cov = clean_lots[pid].intersection(g).area / g.area
            gap = max(0.0, expect - cov)
            shortfalls[pid] = gap
            worst_cov = max(worst_cov, gap)

        st = _grade(worst_cov, tol.possession_tol, 0.10)
        out.append(RuleResult(
            tier=2,
            tier_name="टियर 2: पृथक कब्जा",
            code="e",
            clause_ref="Rule 109(5)(e)",
            legal_basis="[statutory]",
            name_en="Separate possession",
            name_hi="मौके का पृथक कब्जा",
            status=st,
            metric=f"कब्जा विचलन: {worst_cov:.1%}",
            detail="मौजूदा कब्जे का संरक्षण सुचारु है।" if st == "green"
                   else f"कब्जा क्षेत्र में कमी पाई गई (अधिकतम कमी: {worst_cov:.1%})।",
            statutory_citation="उ०प्र० राजस्व संहिता नियमावली 2016, नियम 109(5)(ङ)"
        ))

    # =========================================================================
    # TIER 3: STATUTORY BALANCE (Clauses a, b, c, d, f)
    # =========================================================================
    # (a) Proportional share [statutory]
    devs_v = {p.id: abs(value_of(clean_lots[p.id], zones) / total_v - p.share) / max(p.share, 1e-6) for p in parties}
    devs_a = {p.id: abs(clean_lots[p.id].area / total_a - p.share) / max(p.share, 1e-6) for p in parties}
    graded = devs_v if zones else devs_a
    max_dev = max(graded.values()) if graded else 0.0
    worst_p = max(graded, key=graded.get) if graded else ""

    out.append(RuleResult(
        tier=3,
        tier_name="टियर 3: विधिक संतुलन",
        code="a",
        clause_ref="Rule 109(5)(a)",
        legal_basis="[statutory]",
        name_en="Proportional share",
        name_hi="आनुपातिक हिस्सा",
        status=_grade(max_dev, tol.share_tol, 2 * tol.share_tol),
        metric=f"अधिकतम विचलन: {max_dev:.2%}",
        detail=f"अनुमत सीमा ±{tol.share_tol:.1%}; सबसे बड़ा अंतर: {names.get(worst_p, '')} (क्षेत्रफल अंतर: {devs_a.get(worst_p, 0.0):.1%})",
        statutory_citation="उ०प्र० राजस्व संहिता नियमावली 2016, नियम 109(5)(क)"
    ))

    # (b) Compactness [statutory; thresholds heuristic]
    pps = {p.id: polsby_popper(clean_lots[p.id]) for p in parties}
    parts = {p.id: n_parts(clean_lots[p.id]) for p in parties}
    aspects = {p.id: aspect_ratio(clean_lots[p.id]) for p in parties}

    min_pp = min(pps.values()) if pps else 1.0
    max_p = max(parts.values()) if parts else 1
    max_asp = max(aspects.values()) if aspects else 1.0

    if max_p > 2 or min_pp < 0.12 or max_asp > tol.max_aspect_ratio * 1.5:
        st_b = "red"
    elif max_p > 1 or min_pp < tol.min_compactness or max_asp > tol.max_aspect_ratio:
        st_b = "amber"
    else:
        st_b = "green"

    out.append(RuleResult(
        tier=3,
        tier_name="टियर 3: विधिक संतुलन",
        code="b",
        clause_ref="Rule 109(5)(b)",
        legal_basis="[statutory / heuristic]",
        name_en="Compactness & shape",
        name_hi="सघनता / चक का आकार",
        status=st_b,
        metric=f"न्यूनतम Polsby-Popper: {min_pp:.2f}, अधिकतम टुकड़े: {max_p}",
        detail=f"औसत सघनता: {sum(pps.values())/max(len(pps), 1):.2f}, अधिकतम लंबाई:चौड़ाई अनुपात: {max_asp:.1f}:1",
        statutory_citation="उ०प्र० राजस्व संहिता नियमावली 2016, नियम 109(5)(ख)"
    ))

    # (c) Mixed quality [statutory]
    if len(zones) == 0:
        out.append(RuleResult(
            tier=3,
            tier_name="टियर 3: विधिक संतुलन",
            code="c",
            clause_ref="Rule 109(5)(c)",
            legal_basis="[statutory]",
            name_en="Mixed quality",
            name_hi="मिश्रित गुणवत्ता",
            status="na",
            metric="समान गुणवत्ता भूमि (Single Class)",
            detail="भूमि एक समान गुणवत्ता की है; श्रेणी-विभाजन की आवश्यकता नहीं।",
            statutory_citation="उ०प्र० राजस्व संहिता नियमावली 2016, नियम 109(5)(ग)"
        ))
    else:
        flagged = []
        for p in parties:
            got_classes = set()
            for z, m in zones:
                if clean_lots[p.id].intersection(z).area >= 0.05 * clean_lots[p.id].area:
                    got_classes.add(m)
            if len(got_classes) <= 1 and len(zones) > 1:
                flagged.append(p.name)
        frac = len(flagged) / max(len(parties), 1)
        st_c = "green" if not flagged else "amber" if frac <= 0.25 else "red"
        out.append(RuleResult(
            tier=3,
            tier_name="टियर 3: विधिक संतुलन",
            code="c",
            clause_ref="Rule 109(5)(c)",
            legal_basis="[statutory]",
            name_en="Mixed quality",
            name_hi="मिश्रित गुणवत्ता",
            status=st_c,
            metric=f"{len(flagged)} पक्षकार एकल श्रेणी में",
            detail="गुणवत्ता का न्यायसंगत वितरण सुनिश्चित है।" if not flagged else f"एकल श्रेणी पाने वाले पक्षकार: {', '.join(flagged)}",
            statutory_citation="उ०प्र० राजस्व संहिता नियमावली 2016, नियम 109(5)(ग)"
        ))

    # (d) Preserve existing fields / bunds [statutory / soft heuristic]
    if not units:
        out.append(RuleResult(
            tier=3,
            tier_name="टियर 3: विधिक संतुलन",
            code="d",
            clause_ref="Rule 109(5)(d)",
            legal_basis="[statutory]",
            name_en="Keep existing fields whole",
            name_hi="मौजूदा खेतों/मेड़ों का अक्षुण्ण रहना",
            status="na",
            metric="खेत उप-विभाजन लेयर उपलब्ध नहीं",
            detail="जहाँ तक संभव हो, पुराने खेत के टुकड़े नहीं किए जाने चाहिए।",
            statutory_citation="उ०प्र० राजस्व संहिता नियमावली 2016, नियम 109(5)(घ)"
        ))
    else:
        splits = 0
        for g in units.values():
            holders = sum(1 for p in parties if clean_lots[p.id].intersection(g).area > 0.5)
            if holders > 1:
                splits += 1
        lb = max(len(parties) - len(units), 0)
        st_d = "green" if splits <= lb else "amber" if splits <= lb + 2 else "red"
        out.append(RuleResult(
            tier=3,
            tier_name="टियर 3: विधिक संतुलन",
            code="d",
            clause_ref="Rule 109(5)(d)",
            legal_basis="[statutory]",
            name_en="Keep existing fields whole",
            name_hi="मौजूदा खेतों/मेड़ों का अक्षुण्ण रहना",
            status=st_d,
            metric=f"{splits} खेत विभाजित (अपरिहार्य: ≥ {lb})",
            detail=f"{len(units) - splits} खेत पूर्णतः अक्षुण्ण रखे गए।",
            statutory_citation="उ०प्र० राजस्व संहिता नियमावली 2016, नियम 109(5)(घ)"
        ))

    # (f) Proportionate road / abadi frontage [statutory]
    if roads is None or roads.is_empty:
        out.append(RuleResult(
            tier=3,
            tier_name="टियर 3: विधिक संतुलन",
            code="f",
            clause_ref="Rule 109(5)(f)",
            legal_basis="[statutory]",
            name_en="Road / commercial frontage",
            name_hi="सड़क / आबादी अग्रभाग",
            status="na",
            metric="गाटा सड़क या आबादी से संलग्न नहीं",
            detail="रास्ते की अनुपस्थिति में आंतरिक मेड़ से निकास प्रस्तावित किया जाता है।",
            statutory_citation="उ०प्र० राजस्व संहिता नियमावली 2016, नियम 109(5)(च)"
        ))
    else:
        frontages = {p.id: roads.intersection(clean_lots[p.id].buffer(0.5)).length for p in parties}
        tot_front = sum(frontages.values())
        if tot_front <= 0:
            out.append(RuleResult(
                tier=3,
                tier_name="टियर 3: विधिक संतुलन",
                code="f",
                clause_ref="Rule 109(5)(f)",
                legal_basis="[statutory]",
                name_en="Road / commercial frontage",
                name_hi="सड़क / आबादी अग्रभाग",
                status="red",
                metric="किसी भी कुर्रे को सड़क अग्रभाग नहीं मिला",
                detail="गाटा सड़क से संलग्न है किंतु कुर्रों को रास्ता स्पर्श नहीं करता।",
                statutory_citation="उ०प्र० राजस्व संहिता नियमावली 2016, नियम 109(5)(च)"
            ))
        else:
            front_devs = [abs(frontages[p.id] / tot_front - p.share) / max(p.share, 1e-6) for p in parties]
            max_f_dev = max(front_devs)
            st_f = _grade(max_f_dev, tol.frontage_tol, 2 * tol.frontage_tol)
            out.append(RuleResult(
                tier=3,
                tier_name="टियर 3: विधिक संतुलन",
                code="f",
                clause_ref="Rule 109(5)(f)",
                legal_basis="[statutory]",
                name_en="Road / commercial frontage",
                name_hi="सड़क / आबादी अग्रभाग",
                status=st_f,
                metric=f"अग्रभाग विचलन: {max_f_dev:.1%}",
                detail=f"सड़क सीमा की कुल लंबाई: {tot_front:.1f} m; सभी {len(parties)} खातेदारों को रास्ता संलग्न।",
                statutory_citation="उ०प्र० राजस्व संहिता नियमावली 2016, नियम 109(5)(च)"
            ))

    # =========================================================================
    # GUARDRAILS (G1: Minimum width & connectivity, G2: Direct Road Access)
    # =========================================================================
    # G1: Connectivity & Minimum Width [heuristic / case-law]
    thin_parties = []
    disjoint_parties = []
    for p in parties:
        lot = clean_lots[p.id]
        if not is_connected(lot):
            disjoint_parties.append(p.name)
        if min_width(lot) < tol.min_width_m:
            thin_parties.append(p.name)

    if disjoint_parties:
        out.append(RuleResult(
            tier=3,
            tier_name="सुरक्षा जांच (Guardrail)",
            code="G1",
            clause_ref="Agronomic Integrity",
            legal_basis="[case-law]",
            name_en="Connectivity & Single Polygon",
            name_hi="चक की अखंडता (एकल बहुभुज)",
            status="red",
            metric=f"{len(disjoint_parties)} चक खंडित (Disjoint)",
            detail=f"खंडित चक वाले खातेदार: {', '.join(disjoint_parties)}. नियम 109(5) के तहत एक खातेदार को एक ही चक दिया जाना चाहिए।",
            statutory_citation="उ०प्र० राजस्व संहिता नियमावली 2016, नियम 109(5)(ख)"
        ))
    elif thin_parties:
        out.append(RuleResult(
            tier=3,
            tier_name="सुरक्षा जांच (Guardrail)",
            code="G1",
            clause_ref="Agronomic Width Limit",
            legal_basis="[heuristic]",
            name_en="Minimum Lot Width",
            name_hi="न्यूनतम चौड़ाई (स्लिवर प्रतिबंध)",
            status="red",
            metric=f"न्यूनतम चौड़ाई < {tol.min_width_m}m",
            detail=f"कृषि कार्य एवं ट्रैक्टर संचालन हेतु अमान्य संकरे चक: {', '.join(thin_parties)}",
            statutory_citation="राजस्व परिषद न्यायिक दिशानिर्देश (कृषि उपयोगिता)"
        ))
    else:
        min_w = min(min_width(clean_lots[p.id]) for p in parties)
        out.append(RuleResult(
            tier=3,
            tier_name="सुरक्षा जांच (Guardrail)",
            code="G1",
            clause_ref="Agronomic Width Limit",
            legal_basis="[heuristic]",
            name_en="Minimum Lot Width & Connectivity",
            name_hi="चक अखंडता व न्यूनतम चौड़ाई",
            status="green",
            metric=f"न्यूनतम चौड़ाई: {min_w:.1f} m (मानक: ≥ {tol.min_width_m}m)",
            detail="सभी कुर्रे एकल, अखंड बहुभुज हैं तथा कृषि योग्य न्यूनतम चौड़ाई को पूरा करते हैं।",
            statutory_citation="राजस्व परिषद न्यायिक दिशानिर्देश"
        ))

    # G2: Direct Access [policy]
    if roads is not None and not roads.is_empty:
        no_access = [p.name for p in parties if roads.distance(clean_lots[p.id]) > 1.0]
        st_g2 = "green" if not no_access else "red" if len(no_access) == len(parties) else "amber"
        out.append(RuleResult(
            tier=3,
            tier_name="सुरक्षा जांच (Guardrail)",
            code="G2",
            clause_ref="Access Guarantee",
            legal_basis="[policy]",
            name_en="Direct road access",
            name_hi="सीधा निकास मार्ग",
            status=st_g2,
            metric=f"{len(no_access)} चक बिना सीधे सड़क संपर्क के",
            detail="सभी कुर्रों को सीधा रास्ता प्राप्त है।" if not no_access else f"आंतरिक/अवरुद्ध चक: {', '.join(no_access)}. साझा रास्ता प्रस्तावित करें।",
            statutory_citation="उ०प्र० राजस्व संहिता नियमावली 2016, नियम 109(5)(च)"
        ))

    return out


def explain_failure(results: List[RuleResult]) -> str:
    """Generate plain-language legal explanation of why a partition proposal failed."""
    reds = [r for r in results if r.status == "red"]
    if not reds:
        return "प्रस्तावित कुर्रा विभाजन नियम 109(5) के समस्त विधिक व तकनीकी मानकों पर खरा उतरा है।"

    lines = ["⚠️ प्रस्तावित कुर्रा विभाजन निम्नलिखित वैधानिक कारणों से अमान्य / अस्वीकृत है:"]
    for r in reds:
        lines.append(f"  • {r.tier_name} ({r.clause_ref} {r.legal_basis}): {r.name_hi}")
        lines.append(f"    कारण: {r.metric}. {r.detail}")
    return "\n".join(lines)


def rank_key(results: List[RuleResult]) -> Tuple[int, int, bool, int]:
    """Rank key for sorting proposals: fewest reds, fewest ambers, share green, compactness."""
    reds = sum(r.status == "red" for r in results)
    ambers = sum(r.status == "amber" for r in results)
    a_passed = any(r.code == "a" and r.status == "green" for r in results)
    tier1_or_2_red = any(r.tier in (1, 2) and r.status == "red" for r in results)
    return (1 if tier1_or_2_red else 0, reds, ambers, not a_passed)
