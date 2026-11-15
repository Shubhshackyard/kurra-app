"""CrewAI Multi-Agent Team for Kurra MVP Engineering.

Defines specialized AI agent roles for developing, verifying, and optimizing
the UP Revenue Code Rule 109(5) Kurra partition MVP:
1. Lead GIS & Cadastral Architect
2. Revenue Court & Rule 109(5) Legal Compliance Expert
3. Frontend Cadastral Mapping Engineer
4. Geometric Optimization & Partition Algorithms Engineer
5. Cadastral Quality Assurance & Validation Engineer

Follows official CrewAI documentation (https://docs.crewai.com/en/).
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List

# Graceful import of CrewAI components
try:
    from crewai import Agent, Crew, Process, Task
    CREWAI_AVAILABLE = True
except Exception:
    Agent = None
    Crew = None
    Process = None
    Task = None
    CREWAI_AVAILABLE = False


def build_gis_architect(llm: Any = None) -> Any:
    """Agent: Lead GIS & Cadastral Spatial Architect."""
    if not CREWAI_AVAILABLE:
        return None
    return Agent(
        role="Lead GIS & Cadastral Spatial Architect",
        goal="Design robust georeferenced spatial architectures, coordinate transformations "
             "(UTM 44N EPSG:32644 to WGS84 EPSG:4326), vector parcel topologies, and scalable full-village maps.",
        backstory="Veteran geospatial architect specialized in Indian cadastral land surveys, "
                  "Bhunaksha REST and raster data extraction, boundary georeferencing, and spatial index optimization.",
        verbose=True,
        allow_delegation=True,
        llm=llm
    )


def build_legal_expert(llm: Any = None) -> Any:
    """Agent: UP Revenue Code Rule 109(5) Legal Compliance Specialist."""
    if not CREWAI_AVAILABLE:
        return None
    return Agent(
        role="UP Revenue Code Rule 109(5) Legal Compliance Specialist",
        goal="Ensure deterministic compliance with statutory UP Revenue Code laws, including Rule 109(5) "
             "kurra allotment, road frontage access for every co-sharer, minimum lot width, and Khatauni reconciliation.",
        backstory="Senior revenue court and land partition legal expert who understands Lekhpal practices, "
                  "Section 116/117 proceedings, inherent least count error margins, and court purchase caveats.",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )


def build_frontend_engineer(llm: Any = None) -> Any:
    """Agent: Senior Frontend Cadastral Mapping Engineer."""
    if not CREWAI_AVAILABLE:
        return None
    return Agent(
        role="Senior Frontend Cadastral Mapping Engineer",
        goal="Develop responsive, interactive, and scalable browser-based vector cadastral maps (UP Bhunaksha style) "
             "in Streamlit with Leaflet.js, satellite layers, plot search, and real-time ROR property inspection.",
        backstory="Frontend GIS expert who builds lightning-fast web mapping interfaces, SVG vector renderers, "
                  "and high-contrast cadastral themes with Hindi/English bilingual UI.",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )


def build_optimization_engineer(llm: Any = None) -> Any:
    """Agent: Geometric Optimization & Partition Algorithms Engineer."""
    if not CREWAI_AVAILABLE:
        return None
    return Agent(
        role="Geometric Optimization & Partition Algorithms Engineer",
        goal="Formulate and solve multi-objective land partition problems using weighted recursive bisection, "
             "soil quality zone weighting, road-parallel cuts, and CP-SAT discrete parcel assignment.",
        backstory="Computational geometry and discrete optimization specialist with deep expertise in Shapely, "
                  "OR-Tools CP-SAT, and Pareto-optimal fair division algorithms.",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )


def build_qa_engineer(llm: Any = None) -> Any:
    """Agent: Cadastral Quality Assurance & Validation Engineer."""
    if not CREWAI_AVAILABLE:
        return None
    return Agent(
        role="Cadastral Quality Assurance & Validation Engineer",
        goal="Enforce rigorous spatial topology verification: zero overlap between adjacent parcels, "
             "zero coordinate drift against official server bboxes, and 100% share tolerance accuracy.",
        backstory="Quality assurance engineer who designs automated cadastral integrity suites, "
                  "validates bounding box containment, and ensures regression-free application releases.",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )


def get_default_llm() -> Any:
    """Get the default Google Gemini LLM instance."""
    if not CREWAI_AVAILABLE:
        return None
    import os
    from pathlib import Path
    from crewai import LLM
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please set it in your environment or .env file.")
    os.environ["GEMINI_API_KEY"] = api_key
    os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
    os.environ["OTEL_SDK_DISABLED"] = "true"
    return LLM(model="gemini/gemini-3.8-flash", api_key=api_key)


def create_kurra_crew(llm: Any = None) -> Any:
    """Create the full CrewAI team for developing and auditing the Kurra MVP."""
    if not CREWAI_AVAILABLE:
        return None

    if llm is None:
        llm = get_default_llm()

    gis = build_gis_architect(llm)
    legal = build_legal_expert(llm)
    frontend = build_frontend_engineer(llm)
    algo = build_optimization_engineer(llm)
    qa = build_qa_engineer(llm)

    task_gis = Task(
        description="Verify the georeferenced cadastral dataset for Village 151769 (Jalaun, Orai) "
                    "in both EPSG:32644 (UTM Zone 44N) and EPSG:4326 (WGS84). Ensure all 303 surveyed parcels "
                    "have correct topological adjacency without false overlaps.",
        expected_output="Cadastral dataset integrity report with bounding box verification.",
        agent=gis
    )

    task_legal = Task(
        description="Audit the Rule 109(5) compliance rules: share tolerance (a), minimum lot width, "
                    "compactness threshold (b), road frontage access (f), and Khatauni order description parsing.",
        expected_output="Statutory compliance review conforming to UP Revenue Code.",
        agent=legal
    )

    task_algo = Task(
        description="Formulate the multi-objective Pareto-optimal partition algorithm for Gata 12 and other co-shared plots. "
                    "Ensure equal proportional valuation considering road frontage (Rule 109(5)(f)), rectangularity (compactness > 0.45), "
                    "and minimum width constraint (> 5.0m).",
        expected_output="Mathematical formulation and algorithm optimization strategy for automated Kurra division.",
        agent=algo
    )

    task_frontend = Task(
        description="Integrate an interactive, scalable Leaflet cadastral map matching UP Bhunaksha "
                    "(https://upbhunaksha.gov.in/home) into the Reconcile tab. Enable vector zoom, plot search, "
                    "satellite imagery basemap, and instant property inspection.",
        expected_output="Interactive village map specification and Streamlit integration plan.",
        agent=frontend
    )

    task_qa = Task(
        description="Run automated spatial verification tests on Plot 12 and its neighboring parcels (10, 11, 13, 36) "
                    "to confirm zero overlap and millimeter alignment with the official UP Bhunaksha server bbox.",
        expected_output="Test execution report with all assertions passed.",
        agent=qa
    )

    return Crew(
        agents=[gis, legal, algo, frontend, qa],
        tasks=[task_gis, task_legal, task_algo, task_frontend, task_qa],
        process=Process.sequential,
        verbose=True
    )

