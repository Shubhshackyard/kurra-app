# Kurra App: Cadastral Land Partition Engine

An open-source geometric optimization engine and Streamlit application for agricultural land partition and lot allotment according to Uttar Pradesh Revenue Code Rule 109(5).

## Core Capabilities

- **Cadastral Ingestion:** Fetches ultra-high definition WMS tiles (300 DPI) and vector geometries in EPSG:32644 (UTM Zone 44N).
- **Directional Boundary Analysis:** Computes metric boundary dimensions along cardinal directions (North, South, East, West) along with bounding box dimensions and aspect ratios.
- **Record Reconciliation:** Reconciles surveyed map polygon areas with Khatauni record of rights and extracts co-sharer details.
- **Fair Division Optimization:** Multi-strategy recursive bisection supporting compact shapes, proportional road frontage, and road-parallel division.
- **Rule 109(5) Auditing:** Deterministic verification of share deviations (2% tolerance), minimum lot width (4m guardrail), Polsby-Popper compactness (0.35 threshold), and access.
- **CrewAI Multi-Agent Architecture:** Specialized autonomous tech roles for domain modeling, GIS engineering, mathematical optimization, legal auditing, and UI.

## Getting Started

### Installation
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running the App
```bash
streamlit run app.py
```

### Running Cadastral Analysis via CLI
```bash
python3 test_workflow.py 16500854151769 181
```

### Running the CrewAI Team
```bash
python3 run_crew.py
```

## Project Structure
- `app.py`: Streamlit interactive user interface.
- `kurra/workflow.py`: End-to-end cadastral ingestion and analysis pipeline.
- `kurra/optimizer.py`: Recursive bisection and CP-SAT fair division.
- `kurra/rules.py`: Deterministic Rule 109(5) compliance evaluator.
- `kurra/geometry.py`: Planar geometry primitives and Polsby-Popper compactness.
- `kurra/crew.py`: CrewAI multi-agent team definitions.
- `data/`: Cadastral GeoJSON layers and village datasets.
