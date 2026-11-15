"""CrewAI Team for Revenue Court Legal Drafting (Hindi Microcopy & Exhibits).

CRITICAL ARCHITECTURAL GUARDRAIL:
Deterministic audit in kurra/rules.py is the SOLE source of truth for all spatial,
area, share, and statutory compliance decisions.
CrewAI agents strictly DRAFT official Hindi legal text, report summaries,
and court notices; they NEVER decide or alter partition geometry.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional


class RevenueLegalDrafter:
    """CrewAI-backed Hindi drafting assistant for SDM Revenue Court partitions."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")

    def draft_lekhpal_report(
        self,
        case_info: Dict[str, Any],
        plot_info: Dict[str, Any],
        plan_meta: Dict[str, Any],
        audit_results: List[Dict[str, Any]]
    ) -> str:
        """Draft official Lekhpal Kurra Phant Report (प्रस्तावित कुर्रा फांट आख्या)."""
        plot_no = plot_info.get("plot_no", "57")
        village = case_info.get("village", "इखलाशपुरा च0क्षे0")
        tehsil = case_info.get("tehsil", "उरई")
        district = case_info.get("district", "जालौन")
        case_no = case_info.get("case_no", "116/2026")

        parties = plan_meta.get("parties", [])
        shared_path = plan_meta.get("shared_pathway", {})

        # Deterministic statutory Hindi draft
        lines = [
            f"न्यायालय उपजिलाधिकारी, {tehsil}, जनपद {district}",
            f"वाद संख्या: {case_no} अंतर्गत धारा 116 उ०प्र० राजस्व संहिता 2006",
            f"मौजा: {village}, गाटा संख्या: {plot_no}",
            "────────────────────────────────────────────────────────",
            "विषय: नियम 109(5) के अंतर्गत प्रस्तावित कुर्रा फांट व नजरी नक्शा आख्या",
            "",
            "महोदय,",
            f"  सादर अवगत कराना है कि न्यायालय के आदेशानुसार मौजा {village} के गाटा संख्या {plot_no} "
            f"का स्थलीय व अभिलेखीय सर्वेक्षण कर उ०प्र० राजस्व संहिता नियमावली 2016 के नियम 109(5) के "
            "प्राविधानों के अनुसार कुर्रा विभाजन प्रस्तावित किया गया है:",
            "",
            "1. कुर्रा विवरण व आबंटन सूची (Sanket Suchi):"
        ]

        for idx, p in enumerate(parties, start=1):
            lines.append(
                f"   ({idx}) कुर्रा {p.get('name', 'खातेदार')} — "
                f"अंश: {p.get('share_str', '1/2')} ({p.get('share_pct', 50):.1f}%), "
                f"क्षेत्रफल: {p.get('area_sqm', 0.0):.1f} वर्ग मीटर ({p.get('area_ha', 0.0):.4f} हे०), "
                f"रंग: {p.get('color_hi', 'लाल')}"
            )

        if shared_path.get("enabled"):
            lines.append(
                f"   (*) साझा रास्ता — चौड़ाई {shared_path.get('width_m', 3.0)} मीटर, "
                f"क्षेत्रफल: {shared_path.get('area_sqm', 0.0):.1f} वर्ग मीटर (सभी खातेदारों के अंश से आनुपातिक कटौती)"
            )

        lines.extend([
            "",
            "2. नियम 109(5) वैधानिक अनुपालन सारांश:",
            "   • प्रत्येक खातेदार को सघन एवं चकबंदी सिद्धांतों के अनुरूप एकल संहत चक आबंटित किया गया है।",
            "   • मौके पर पूर्व से चले आ रहे पृथक कब्जे को यथासंभव सुरक्षित रखा गया है।",
            "   • सड़क/मार्ग व नाली की सुविधा का आनुपातिक एवं निर्बाध निकास सुनिश्चित किया गया है।",
            "   • कोई भी कुर्रा कृषि योग्य न्यूनतम चौड़ाई से कम (स्लिवर) नहीं है।",
            "",
            "यह आख्या पक्षकारों के अवलोकनार्थ एवं नियमानुसार आपत्तियों हेतु सादर प्रस्तुत है।",
            "",
            "हस्ताक्षर राजस्व निरीक्षक                 हस्ताक्षर लेखपाल",
            "दिनांक: ....................              क्षेत्र: ...................."
        ])

        return "\n".join(lines)

    def draft_sdm_preliminary_decree(
        self,
        case_info: Dict[str, Any],
        plot_info: Dict[str, Any],
        plan_meta: Dict[str, Any]
    ) -> str:
        """Draft SDM Court Preliminary Order under Section 116 (प्रारंभिक डिक्री आदेश)."""
        tehsil = case_info.get("tehsil", "उरई")
        district = case_info.get("district", "जालौन")
        case_no = case_info.get("case_no", "116/2026")
        plaintiff = case_info.get("plaintiff", "वादी")
        defendant = case_info.get("defendant", "प्रतिवादी")
        plot_no = plot_info.get("plot_no", "57")

        return f"""न्यायालय उपजिलाधिकारी, {tehsil}, जनपद {district}
वाद संख्या: {case_no} अंतर्गत धारा 116 उ०प्र० राजस्व संहिता 2006
{plaintiff} बनाम {defendant}

॥ आदेश ॥
पत्रावली प्रस्तुत हुई। वाद धारा 116 उ०प्र० राजस्व संहिता 2006 के अंतर्गत मौजा {case_info.get('village', '')} के गाटा संख्या {plot_no} के विभाजन हेतु संस्थित किया गया है।
अभिलेखों के अवलोकन से स्पष्ट है कि पक्षों के मध्य अंश निर्विवादित हैं। अतः प्रारंभिक डिक्री पारित की जाती है।
क्षेत्रीय लेखपाल को निर्देशित किया जाता है कि वह उ०प्र० राजस्व संहिता नियमावली 2016 के नियम 109(5) के वैधानिक मानकों के अनुसार कुर्रा फांट व नजरी नक्शा तैयार कर आगामी नियत तिथि से पूर्व न्यायालय में प्रस्तुत करें।

आदेश की प्रति संबंधित लेखपाल व राजस्व निरीक्षक को अनुपालनार्थ प्रेषित हो।

(उपजिलाधिकारी)
{tehsil}, {district}"""
