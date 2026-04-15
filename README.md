# LifeScope Static MVP

This is a zero-dependency MVP sketch for the Simulated Life website direction.

Open `index.html` in a browser for local-only fallback mode, or run the Python server for API-backed mode:

```bash
python3 server.py
```

Then open:

```text
http://127.0.0.1:8765/
```

## What It Demonstrates

- Text/file intake for background and interests
- Lightweight profile controls for risk, stability, mobility, focus, and what-if choices
- Profile confirmation before generation
- Three branch cards with probability and confidence
- A short path timeline
- A trust surface with evidence, missing information, and rerun guidance
- Redacted local persistence under `data/runs/` when the backend is running

## What It Does Not Do Yet

- It does not call Kimi or the Python simulation engine.
- It does not store raw long-form user text by default.
- It does not parse PDF/DOCX uploads.
- It is not medical, legal, financial, or psychological advice.

## Local API

```text
GET  /api/health
GET  /api/runs
GET  /api/runs/<run_id>
POST /api/profile
POST /api/intake
POST /api/simulate
POST /api/engine-contract
DELETE /api/runs/<run_id>
```

`POST /api/engine-contract` maps the web intake into the future `simulate_life.SimulationRequest` shape.

## Intended Next Step

Wrap the existing Python engine in a small web backend:

1. web intake to friendly `UserLifeProfile`
2. user confirmation screen
3. mapper to the existing `SimulationRequest`
4. background `run_simulation(...)`
5. result page using `simulation.json`, `report.md`, `visual_summary.md`, and `analysis_dossier.json`

## Verification

```bash
node --check app.js
python3 -m compileall .
python3 -m unittest
```
