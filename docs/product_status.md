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

It is **not beta-ready** because the Chinese report is not yet consistently fluent, the real Kimi path is still a synchronous long request, and the product does not yet have account ownership, background jobs, cancellation, full deletion of upstream artifacts, browser E2E coverage, or production privacy controls.

## Build Path So Far

Keep this path simple and update it after every meaningful product step:

1. **Static product sketch**: a single-page website showed the intended intake, three-path result, timeline, and trust surface.
2. **Profile review**: the flow added a checkpoint where users can see what the system understood before generation.
3. **Deterministic draft**: the browser/backend can generate a fast local three-path reading without calling a model.
4. **Backend API**: the local Python server added `/api/profile`, `/api/simulate`, `/api/runs`, and the engine contract endpoint.
5. **Real Kimi path**: `/api/simulate?engine=simulate_life` can call the upstream `simulate_life` engine with Moonshot / Kimi 2.5.
6. **Redacted storage**: LifeScope stores a lightweight run snapshot with raw long-form text replaced by redaction metadata.
7. **Product documentation**: this status document and `docs/product.md` now track stage, blockers, gates, and next milestones.
8. **Chinese quality gate**: Kimi-backed results now carry a lightweight Chinese report fluency check so a successful model run is not mistaken for a beta-ready report.
9. **LifeScope short report**: the web layer now writes a shorter Chinese report from structured results under `data/lifescope_reports/`, so alpha users are not forced to read the upstream localized long report first.

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
- Kimi-backed runs can produce a LifeScope-owned short Chinese report for alpha review, separate from upstream engine artifacts.

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

Known quality issue from existing runs:

- Chinese `report.md` / `visual_summary.md` artifacts fail the lightweight fluency gate in existing local runs.
- The issue is not just style polish. Phrases such as "诚实答案仍是拒绝", "报告能看到", "树故意保持", and "感觉被居住" make the report feel machine-translated and semantically unreliable.
- Product rule: a completed Kimi run is only an engine success; it is not beta-ready until the Chinese user-facing artifacts are readable.

### Verification

Current local verification:

```bash
node --check app.js
python3 -m compileall .
python3 -m unittest discover -s tests -p 'test_*.py'
```

Current passing suite:

- 23 tests
- covers core branch generation
- covers LifeScope storage redaction
- covers server routes
- covers engine aliasing and fallback
- covers Kimi result mapping with fakes
- covers Chinese artifact fluency gating
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

1. **Chinese report fluency**
   Chinese reports must read like natural Chinese. A report can be structurally correct and still fail the product if the wording is awkward, mixed-language, or semantically broken. Invite-only beta requires repeated Chinese runs that pass human review and the lightweight fluency gate.

2. **Background job execution**
   Kimi runs can take minutes. `/api/simulate` must not block a request thread for public beta.

3. **Progress and cancellation**
   Users need visible queued/running/done/failed states and a way to stop or retry.

4. **Deletion semantics**
   Current delete removes LifeScope local run snapshots, but upstream `simulate_life` artifacts under `data/simulate_life_runs/` must also be deleted or governed by a retention policy.

5. **User ownership**
   There is no account/session owner check. Any multi-user deployment needs access control before storing life data.

6. **Privacy controls**
   Need explicit retention copy, upload limits, log policy, data deletion, and sensitive-field consent separation.

7. **Browser E2E**
   Current verification is API/Python focused. Need browser tests for intake, confirmation, Kimi mode loading, result rendering, rerun, and delete.

8. **Content QA**
   Need repeated live runs across thin/rich profiles, Chinese/English, sensitive/low-sensitive inputs, and different what-if combinations.

## Chinese Report Quality Bar

This product is a report-reading product. If the Chinese is not smooth, the product fails even when the Kimi run succeeds.

For beta, a Chinese report must:

- sound like it was written directly in Chinese, not translated from English
- avoid stiff phrases such as "这版推演看到的"
- avoid semantic breaks such as "诚实答案仍是拒绝", "报告能看到", and "树故意保持"
- explain life paths in plain sentences, not internal memo language
- make each branch concrete: life scene, weekly rhythm, pressure point, tradeoff, and landing
- keep English words to approved product terms only
- make the first screen understandable in about 30 seconds
- pass at least one human Chinese-readability review before being shown to invited testers

Current automated guardrail:

- Kimi-backed responses include a lightweight Chinese artifact fluency check.
- The check inspects `report.md` and `visual_summary.md`.
- A failed check adds `chinese_report_fluency_not_beta_ready` to `quality.beta_blockers`.
- This check is only a guardrail. It does not replace human review.
- When upstream Chinese artifacts fail, the LifeScope short report may still be useful for alpha review, but it does not clear the beta blocker by itself.

## Product Metrics For Alpha

For the next internal-alpha round, track:

- intake completion rate
- profile-confirmation edit rate
- Kimi generation completion rate
- average Kimi run time
- Chinese report fluency pass rate
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

1. Fix Chinese report fluency enough that reports are understandable, natural, and accurate.
2. Convert synchronous Kimi execution into background jobs.
3. Add job status endpoints: queued, running, completed, failed, cancelled.
4. Add frontend polling and long-task progress.
5. Make profile confirmation editable in place.
6. Add run history and rerun-from-previous-result.
7. Extend delete to cover LifeScope snapshots and upstream engine artifacts.
8. Add basic session ownership.
9. Add browser E2E tests.
10. Run 5 repeated live Kimi cases and review artifacts.
11. Interview at least 5 alpha users before adding monetization.

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

- Chinese reports pass human review for fluency and meaning.
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
- Chinese report quality findings
- launch blockers

Update cadence during active build: after every meaningful product commit or live user test.
