---
title: Kurra Cadastral Partition Engine
emoji: 🏛️
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
---

# Kurra Cadastral Partition & Demarcation Platform

An open-source geometric optimization engine and Next.js / FastAPI platform for agricultural land partition and lot allotment under **Uttar Pradesh Revenue Code, 2006 (Section 116/117 & Rule 109(5))**.

## Core Capabilities

- **Cadastral Ingestion:** Fetches ultra-high definition WMS tiles (300 DPI) and vector geometries in EPSG:32644 (UTM Zone 44N).
- **Directional Boundary Analysis:** Computes metric boundary dimensions along cardinal directions (North, South, East, West) along with bounding box dimensions and aspect ratios.
- **Record Reconciliation:** Reconciles surveyed map polygon areas with Khatauni record of rights and extracts co-sharer details.
- **Fair Division Optimization:** Multi-strategy recursive bisection supporting compact shapes, proportional road frontage, and road-parallel division.
- **Rule 109(5) Auditing:** Deterministic verification of share deviations (2% tolerance), minimum lot width (4m guardrail), Polsby-Popper compactness (0.40 threshold), and access.
- **CrewAI Multi-Agent Architecture:** Specialized autonomous tech roles for domain modeling, GIS engineering, mathematical optimization, legal auditing, and UI.

## Getting Started

### Local Setup
```bash
pip install -r requirements.txt
uvicorn kurra.api.main:app --reload --port 8000
```

### Next.js Web UI
```bash
cd web
npm install
npm run dev
```
