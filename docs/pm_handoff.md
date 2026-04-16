# LifeScope PM Handoff

Last updated: 2026-04-16

## One-Sentence Product

LifeScope is a website that helps a user turn one important life question into several comparable future paths, with evidence, uncertainty, and next actions.

## Current Stage

Current stage: **internal alpha / working alpha**.

This means:

- the product works locally
- the web flow exists
- the backend can call Kimi 2.5 through the existing `simulate_life` engine
- real artifacts can be generated
- the product is still not safe or polished enough for invited external users

Do not call it beta yet.

## What Exists Today

User-facing flow:

1. User writes background, interests, constraints, and a life question.
2. User chooses assumptions such as risk, stability, mobility, and what-if paths.
3. User reviews what the system understood.
4. User generates either a deterministic draft or a Kimi 2.5 run.
5. Product shows a one-screen answer, three paths, a timeline, and a trust surface.

Backend:

- `server.py` exposes the local API.
- `lifescope/core.py` creates deterministic draft readings.
- `lifescope/engine_mapper.py` maps web intake into `simulate_life.SimulationRequest`.
- `lifescope/engine_runner.py` calls the real upstream `simulate_life` engine.
- `lifescope/storage.py` stores redacted LifeScope snapshots.
- `lifescope/report_quality.py` checks obvious Chinese report fluency failures.
- `lifescope/report_renderer.py` writes a shorter LifeScope-owned Chinese report for alpha review.

Product docs:

- `docs/product.md`: broader product direction and beta roadmap
- `docs/product_status.md`: current stage, blockers, gates, metrics, live evidence
- `docs/pm_handoff.md`: this handoff

## Live Evidence

Known real Kimi 2.5 run:

- run id: `run-20260415155731-0b049441`
- provider: `moonshot`
- model: `kimi-k2.5`
- branch count: `3`
- top branch: `Balanced Compounding Path`

Artifacts:

- `data/simulate_life_runs/run-20260415155731-0b049441/simulation.json`
- `data/simulate_life_runs/run-20260415155731-0b049441/report.md`
- `data/simulate_life_runs/run-20260415155731-0b049441/visual_summary.md`
- `data/simulate_life_runs/run-20260415155731-0b049441/analysis_dossier.json`

## Biggest Product Issue

The biggest issue right now is **Chinese report fluency**.

The report can be structurally complete but still fail as a product if the Chinese reads like a translated internal memo.

Known bad examples from current local artifacts:

- "诚实答案仍是拒绝"
- "报告能看到"
- "树故意保持"
- "感觉被居住"
- "这版推演看到的"

These are not copy nitpicks. They break user trust.

PM rule:

> Kimi run completed does not mean the report is product-ready.

The current LifeScope-side mitigation:

- Kimi responses include `quality.beta_blockers` when Chinese artifacts fail the fluency gate.
- The web layer writes a shorter LifeScope-owned Chinese report under `data/lifescope_reports/`.
- Upstream `report.md` should be treated as an internal artifact until Chinese output quality improves.

The real fix still needs upstream work in `/Users/wangyiqi/Desktop/code/simulate_life`, especially around Chinese-first visible generation, localization review, and report templates.

## Do Not Break These Decisions

- Keep deterministic mode. It is the cheap product loop for fast testing.
- Keep Kimi mode separate and visibly labeled. Users must know when a long model run is happening.
- Keep probability and confidence separate.
- Keep uncertainty visible.
- Keep raw long-form user text out of lightweight LifeScope snapshots.
- Do not expose upstream `analysis_dossier.json` directly to users.
- Do not claim beta while Chinese reports are hard to read.

## Next Milestone

Next milestone: **invite-only beta readiness**.

The next PM/engineering owner should work in this order:

1. Improve Chinese report quality enough for human review.
2. Add background jobs for Kimi runs.
3. Add real job progress polling.
4. Add retry and cancellation.
5. Add session ownership for jobs/runs.
6. Extend deletion to linked upstream artifacts.
7. Add browser E2E tests.
8. Run 5 live Chinese Kimi cases.
9. Interview at least 5 alpha users.

## Acceptance Criteria For The Next Release

Before inviting external testers:

- A Kimi job returns immediately with a job id.
- User can see real progress.
- User can refresh and recover a running/completed job.
- User can delete a result and linked artifacts.
- At least 5 Chinese reports pass human fluency review.
- No critical Chinese phrases like "诚实答案仍是拒绝" appear.
- The first screen makes the top path, challenger, risk, uncertainty, and next action clear.

## How To Run Locally

Fast local mode:

```bash
python3 server.py
```

Open:

```text
http://127.0.0.1:8765/
```

Real Kimi mode:

```bash
LIFESCOPE_ENGINE=simulate_life python3 server.py
```

Or call:

```text
POST /api/simulate?engine=simulate_life
```

The real Kimi path reads `.env` from:

```text
/Users/wangyiqi/Desktop/code/simulate_life
```

## Verification

Run before committing:

```bash
node --check app.js
python3 -m compileall .
python3 -m unittest discover -s tests -p 'test_*.py'
```

Current expected result:

```text
Ran 25 tests
OK
```

## Product Metrics To Track In Alpha

- intake completion rate
- profile confirmation edit rate
- Kimi completion rate
- average Kimi runtime
- Chinese fluency pass rate
- percent of users who say "this feels like me"
- percent who open the trust surface
- percent who rerun with edited assumptions
- percent who would save, return, or pay

## Final PM Note

The product is promising because the end-to-end loop is real.

The product is not yet trustworthy because the user-facing Chinese report is not consistently readable.

The next owner should resist adding more features until the report quality and long-running Kimi experience are strong enough for invited testers.

