# LifeScope Static MVP

This is a zero-dependency MVP sketch for the Simulated Life website direction.

Current product status: **internal alpha**. The product can run deterministic drafts and real Kimi 2.5 simulations, but it is not beta-ready yet. See [docs/product_status.md](docs/product_status.md) for the maintained PM status, [docs/product.md](docs/product.md) for product direction, and [docs/pm_handoff.md](docs/pm_handoff.md) for the handoff brief.

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
- Lightweight Chinese report fluency gate for Kimi-backed artifacts
- LifeScope-owned short Chinese report rendered from structured results
- Three branch cards with probability and confidence
- A short path timeline
- A trust surface with evidence, missing information, and rerun guidance
- Redacted local persistence under `data/runs/` when the backend is running

## What It Does Not Do Yet

- It does not store raw long-form user text by default.
- It does not parse PDF/DOCX uploads.
- It is not medical, legal, financial, or psychological advice.
- It does not run the Kimi path asynchronously yet; real engine runs can take minutes.
- It does not yet guarantee fluent Chinese reports; this is a blocker for invite-only beta.

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

The backend imports `/Users/wangyiqi/Desktop/code/simulate_life`, reads that repo's `.env`, uses `provider=moonshot`, and defaults to `model=kimi-k2.5`. Full engine artifacts are written under `data/simulate_life_runs/`, while the LifeScope run index stores only a redacted response snapshot. Web API calls default upstream visible artifacts to Chinese; set `LIFESCOPE_SIMULATE_LIFE_LANGUAGE=en` if you need the faster English artifact path for debugging.

Because the upstream localized Chinese report can still read awkwardly, the web layer also writes a shorter LifeScope-owned Chinese report under `data/lifescope_reports/`. Treat the upstream report as an internal artifact until repeated Chinese quality reviews pass.

## Intended Next Step

Make the Kimi-backed path beta-safe as a long-running operation:

1. fix Chinese report fluency enough for invited testers
2. create persisted job records for Kimi runs
3. move `run_simulation(...)` behind a background worker
4. expose job status, retry, and cancel endpoints
5. poll real progress from the frontend
6. bind jobs/runs to a session before inviting external testers
7. extend delete behavior to linked `simulate_life` artifacts

## Verification

```bash
node --check app.js
python3 -m compileall .
python3 -m unittest discover -s tests -p 'test_*.py'
```
