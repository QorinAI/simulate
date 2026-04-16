# LifeScope Product Status

Last updated: 2026-04-16

## Product Stage

LifeScope is currently in **internal alpha**.

It has moved past a static concept prototype because the web MVP can now:

- collect user background, interests, constraints, and what-if assumptions
- show a profile confirmation step
- produce a deterministic three-path draft in the browser/backend
- route backend simulation requests into the existing `simulate_life` engine
- complete a real Moonshot / Kimi 2.5 run
- persist a redacted LifeScope snapshot locally
- produce upstream engine artifacts: `simulation.json`, `report.md`, `visual_summary.md`, and `analysis_dossier.json`

It is **not beta-ready** because the real Kimi path is still a synchronous long request and the product does not yet have account ownership, background jobs, cancellation, full deletion of upstream artifacts, browser E2E coverage, or production privacy controls.

## Current Product Definition

LifeScope is an **AI life-path simulation and decision rehearsal website**.

It is not:

- a game
- destiny prediction
- a generic chatbot
- a medical, legal, financial, or psychological adviser

It is:

- a structured intake experience
- a multi-branch life-path reading
- a decision comparison tool
- a trust-calibrated reflection product

The core promise:

> Upload or write your background, interests, constraints, and key life question; LifeScope returns several plausible future paths, what each path gives and costs, what information the judgment used, what remains uncertain, and what to change or observe before rerunning.

## Target User For Alpha

The alpha should stay narrow:

- age range: roughly 22-40
- situation: facing an actual life decision
- examples: career transition, graduate school, startup vs stable job, relocation, relationship/family timing, lifestyle sustainability
- motivation: wants reflection and decision clarity, not entertainment only

The first alpha cohort should be invite-only and recruited from users who are willing to provide detailed background and be interviewed after reading the result.

## Validated So Far

### Product/UX

- The page has the minimum loop: intake -> profile review -> loading -> result -> branch compare -> trust surface.
- The UI distinguishes deterministic draft mode from Kimi 2.5 mode.
- Kimi mode is presented as a long-running task rather than an instant calculator.

### Technical

- `POST /api/simulate?engine=simulate_life` routes through the LifeScope backend into the existing `simulate_life` engine.
- The engine path uses `provider=moonshot` and `model=kimi-k2.5`.
- The deterministic path remains available for local demos and fallback.
- Web intake can be mapped into the existing `simulate_life.SimulationRequest` shape.
- Redacted LifeScope snapshots are stored locally; raw long-form fields are replaced in the lightweight LifeScope store.

### Live Evidence

Known successful live run:

- run id: `run-20260415155731-0b049441`
- provider: `moonshot`
- model: `kimi-k2.5`
- branch count: `3`
- top branch: `Balanced Compounding Path`
- artifacts:
  - `data/simulate_life_runs/run-20260415155731-0b049441/simulation.json`
  - `data/simulate_life_runs/run-20260415155731-0b049441/report.md`
  - `data/simulate_life_runs/run-20260415155731-0b049441/visual_summary.md`
  - `data/simulate_life_runs/run-20260415155731-0b049441/analysis_dossier.json`

### Verification

Current local verification:

```bash
node --check app.js
python3 -m compileall .
python3 -m unittest discover -s tests -p 'test_*.py'
```

Current passing suite:

- 19 tests
- covers core branch generation
- covers LifeScope storage redaction
- covers server routes
- covers engine aliasing and fallback
- covers Kimi result mapping with fakes
- covers bad JSON response path

## Not Yet Validated

The following are product risks, not minor polish:

- whether real users feel the result is specific enough to be about them
- whether users trust probability/confidence explanations
- whether users are willing to wait for the Kimi path
- whether users understand profile confirmation as a meaningful control point
- whether users rerun after editing one what-if
- whether the result page makes the top path, challenger, risk, uncertainty, and next action obvious in one screen
- whether users would pay for the full report or rerun package

## Current Launch Blockers

Do not launch publicly until these are resolved:

1. **Background job execution**
   Kimi runs can take minutes. `/api/simulate` must not block a request thread for public beta.

2. **Progress and cancellation**
   Users need visible queued/running/done/failed states and a way to stop or retry.

3. **Deletion semantics**
   Current delete removes LifeScope local run snapshots, but upstream `simulate_life` artifacts under `data/simulate_life_runs/` must also be deleted or governed by a retention policy.

4. **User ownership**
   There is no account/session owner check. Any multi-user deployment needs access control before storing life data.

5. **Privacy controls**
   Need explicit retention copy, upload limits, log policy, data deletion, and sensitive-field consent separation.

6. **Browser E2E**
   Current verification is API/Python focused. Need browser tests for intake, confirmation, Kimi mode loading, result rendering, rerun, and delete.

7. **Content QA**
   Need repeated live runs across thin/rich profiles, Chinese/English, sensitive/low-sensitive inputs, and different what-if combinations.

## Product Metrics For Alpha

For the next internal-alpha round, track:

- intake completion rate
- profile-confirmation edit rate
- Kimi generation completion rate
- average Kimi run time
- first-screen comprehension score from interviews
- percent of users who say “this feels like me”
- percent who expand trust surface
- percent who rerun with edited assumptions
- percent who would save, share privately, or pay
- top reasons users distrust or abandon the output

Minimum learning target before beta:

- 20-30 alpha users
- at least 60% complete intake
- at least 40% read the branch comparison
- at least 30% rerun or say they would rerun after a real life update
- at least 50% say the first screen feels specific to their situation

## Next Milestone

Next milestone: **invite-only beta readiness**.

Required work:

1. Convert synchronous Kimi execution into background jobs.
2. Add job status endpoints: queued, running, completed, failed, cancelled.
3. Add frontend polling and long-task progress.
4. Make profile confirmation editable in place.
5. Add run history and rerun-from-previous-result.
6. Extend delete to cover LifeScope snapshots and upstream engine artifacts.
7. Add basic session ownership.
8. Add browser E2E tests.
9. Run 5 repeated live Kimi cases and review artifacts.
10. Interview at least 5 alpha users before adding monetization.

## Release Gates

### Internal Alpha

Current status: **met**.

Evidence:

- local app runs
- deterministic mode works
- Kimi 2.5 backend path works
- test suite passes
- redacted LifeScope storage exists

### Invite-Only Beta

Status: **not met**.

Gates:

- background Kimi jobs
- progress and retry
- delete/retention model
- basic user/session ownership
- browser E2E
- at least 5 successful live Kimi runs
- first-screen result template reviewed by users

### Paid Experiment

Status: **not met**.

Gates:

- beta retention data
- clear free vs paid value split
- stable rerun flow
- privacy/legal copy
- support path for failed Kimi runs

## Product Documentation Maintenance

Keep this document updated whenever one of these changes:

- product stage
- target user
- release gate
- Kimi integration status
- privacy/data retention policy
- alpha/beta metrics
- evidence from live runs
- launch blockers

Update cadence during active build: after every meaningful product commit or live user test.

