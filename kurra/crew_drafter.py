"""
CrewAI Legal Drafting Team for UP Revenue Code Section 116 / Rule 109(5).

Agents:
1. Lekhpal Rapporteur Agent (राजस्व लेखपाल) - drafts authentic cadastral field reports & kurra descriptions
2. SDM Judicial Clerk Agent (एसडीएम न्यायालय नायब रीडर) - drafts preliminary decree & objection notices

RULE CONSTRAINT:
- Deterministic audit is the source of truth.
- CrewAI agents may ONLY draft Hindi text using exact metrics passed from the engine, NEVER decide or alter partition geometry.
"""

from __future__ import annotations
import os
from typing import Dict, Any, Optional

try:
    from crewai import Agent, Task, Crew, Process
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

from kurra.legal_drafter import RevenueLegalDrafter


class KurraLegalCrew:
    """
    CrewAI Team for drafting UP Revenue Partition legal documents.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.fallback_drafter = RevenueLegalDrafter()

    def build_crew(self, case_meta: Dict[str, Any], scheme_data: Dict[str, Any]) -> Optional[Any]:
        if not CREWAI_AVAILABLE or not self.api_key:
            return None

        # 1. Lekhpal Surveyor Agent
        lekhpal = Agent(
            role="राजस्व लेखपाल (Cadastral Surveyor & Field Rapporteur)",
            goal="Draft an authentic, statutory Lekhpal Kurra Report (फर्द बटवारा आख्या) under Section 116 / Rule 109(5) UP Revenue Code 2006",
            backstory=(
                "You are an experienced Uttar Pradesh Revenue Lekhpal stationed in Tehsil Orai, District Jalaun. "
                "You have surveyed thousands of agricultural parcels (गाटा). You know exact revenue terms: "
                "मुताबिक, किता, चकमार्ग, गाटा संख्या, मौजा, अंश, दखल, चौहद्दी, संकेत सूची. "
                "You NEVER change or invent numbers. You strictly describe the parcel and proposed partition lots "
                "using the exact mathematical measurements and adjacencies provided."
            ),
            verbose=False,
            allow_delegation=False,
        )

        # 2. SDM Judicial Clerk Agent
        clerk = Agent(
            role="एसडीएम न्यायालय रीडर (SDM Revenue Court Clerk)",
            goal="Draft the formal Preliminary Decree (प्रारंभिक डिक्री) and Notice Inviting Objections under Rule 109(5)",
            backstory=(
                "You are the senior judicial reader in the Court of Sub-Divisional Magistrate / Assistant Collector 1st Class. "
                "You ensure all orders strictly cite Section 116 and Rule 109(5) of the UP Revenue Code, 2006, "
                "bind all recorded co-sharers to their declared shares, and provide statutory 15-day notice for objections."
            ),
            verbose=False,
            allow_delegation=False,
        )

        # 3. Tasks
        report_task = Task(
            description=(
                f"Draft the formal Lekhpal Partition Report in formal Hindi for Case: {case_meta.get('case_no', '116/2026')}, "
                f"Village: {case_meta.get('village_name', 'इखलाशपुरा')}, Plot: {case_meta.get('plot_no', '57')}. "
                f"Lots: {scheme_data.get('lots', [])}. "
                f"Explain how each lot complies with Rule 109(5) regarding road frontage and compactness."
            ),
            expected_output="A structured Hindi legal report formatted as 'न्यायालय उपजिलाधिकारी - फर्द बटवारा आख्या'.",
            agent=lekhpal,
        )

        decree_task = Task(
            description=(
                f"Draft the Preliminary Decree order for Case: {case_meta.get('case_no', '116/2026')} "
                f"confirming the partition shares and inviting objections under Rule 109(5)."
            ),
            expected_output="Formal Hindi Preliminary Decree order under Section 116.",
            agent=clerk,
        )

        crew = Crew(
            agents=[lekhpal, clerk],
            tasks=[report_task, decree_task],
            process=Process.sequential,
            verbose=False,
        )
        return crew

    def draft_documents(self, case_meta: Dict[str, Any], scheme_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Drafts documents using CrewAI if an API key is configured;
        otherwise falls back to deterministic template generation.
        """
        if CREWAI_AVAILABLE and self.api_key:
            try:
                crew = self.build_crew(case_meta, scheme_data)
                if crew:
                    result = crew.kickoff()
                    return {
                        "lekhpal_report_hi": str(result),
                        "preliminary_decree_hi": self.fallback_drafter.draft_preliminary_decree(case_meta, scheme_data),
                        "objection_notice_hi": self.fallback_drafter.draft_objection_notice(case_meta, scheme_data),
                        "source": "crewai_multi_agent",
                    }
            except Exception:
                pass  # Gracefully fall back to deterministic drafter

        # Deterministic source of truth fallback
        return {
            "lekhpal_report_hi": self.fallback_drafter.draft_lekhpal_report(case_meta, scheme_data),
            "preliminary_decree_hi": self.fallback_drafter.draft_preliminary_decree(case_meta, scheme_data),
            "objection_notice_hi": self.fallback_drafter.draft_objection_notice(case_meta, scheme_data),
            "source": "deterministic_audit_template",
        }
