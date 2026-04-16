# LifeScope Static MVP

This is a zero-dependency MVP sketch for the Simulated Life website direction.

Product status and PM guidance live in [`docs/product.md`](docs/product.md).

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
- Runtime mode switch: deterministic draft or real `simulate_life` / Moonshot Kimi 2.5
- Three branch cards with probability and confidence
- A short path timeline
- A trust surface with evidence, missing information, and rerun guidance
- Redacted local persistence under `data/runs/` when the backend is running

## What It Does Not Do Yet

- It does not store raw long-form user text by default.
- It does not parse PDF/DOCX uploads.
- It is not medical, legal, financial, or psychological advice.
- It does not run the Kimi path asynchronously yet; real engine runs can take minutes.

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

To run the real Kimi-backed engine from the web API:

```bash
LIFESCOPE_ENGINE=simulate_life python3 server.py
```

Or request it per call:

```text
POST /api/simulate?engine=simulate_life
```

The backend imports `/Users/wangyiqi/Desktop/code/simulate_life`, reads that repo's `.env`, uses `provider=moonshot`, and defaults to `model=kimi-k2.5`. Full engine artifacts are written under `data/simulate_life_runs/`, while the LifeScope run index stores only a redacted response snapshot. Web API calls default the upstream visible artifact language to English for synchronous response reliability; set `LIFESCOPE_SIMULATE_LIFE_LANGUAGE=zh` when you want the upstream Chinese report artifacts and can tolerate the longer localization path.

## Intended Next Step

Wrap the existing Python engine in a small web backend:

1. web intake to friendly `UserLifeProfile`
2. user confirmation screen
3. mapper to the existing `SimulationRequest`
4. background `run_simulation(...)`
5. result page using `simulation.json`, `report.md`, `visual_summary.md`, and `analysis_dossier.json`

## Product Document

The living PM document is maintained at [`docs/product.md`](docs/product.md). It records the current product stage, beta definition, roadmap, metrics, and privacy/technical risks.

## Verification

```bash
node --check app.js
python3 -m compileall .
python3 -m unittest
```
