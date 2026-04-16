# LifeScope Product Document

Last updated: 2026-04-16

## 1. Product Stage

LifeScope is currently in **working alpha**.

What is proven:

- Users can enter a life background, interests, constraints, and what-if assumptions in a web UI.
- The product has the right core flow: intake -> profile review -> path generation -> branch comparison -> trust surface.
- The backend can run both a deterministic draft and the real `simulate_life` Moonshot / Kimi 2.5 engine.
- The real engine writes upstream artifacts: `simulation.json`, `report.md`, `visual_summary.md`, and `analysis_dossier.json`.
- Local persistence stores a redacted response snapshot rather than raw long-form user text by default.

What is not beta-ready:

- Chinese reports are not yet consistently fluent enough for invited users.
- Kimi runs are synchronous and can block the HTTP request for minutes.
- Progress is only server stderr plus frontend simulated loading, not real job state.
- There is no cancellation, retry, resumable job status, auth, or per-user access control.
- The UI exposes only a simplified projection of engine artifacts.
- Privacy controls are MVP-level and local, not production-grade.

PM read: the product has crossed from "mockup" to **working alpha** because it can call Kimi 2.5 end to end. It has not crossed into beta because Chinese reports are not yet consistently fluent, and real users still need reliable job handling, safer data boundaries, and clearer result review surfaces.

### Build Path So Far

The product has been built in this order:

1. A static web sketch proved the intended flow.
2. A profile review step made the system's understanding visible before generation.
3. A deterministic draft made the three-path experience fast and cheap to test.
4. A local Python API connected the page to backend routes.
5. The backend mapped web intake into the upstream `simulate_life` request shape.
6. The real Moonshot / Kimi 2.5 path ran end to end and produced artifacts.
7. Redacted local storage kept the lightweight LifeScope snapshot safer for internal testing.
8. Product docs now track the stage, release gates, and current blockers.
9. A lightweight Chinese fluency gate now marks Kimi-backed reports that are not readable enough for beta.

## 2. Product Promise

LifeScope helps a user turn one important life question into several comparable future paths.

It is:

- A future-reading and decision-rehearsal website.
- A multi-path simulation surface.
- A way to expose assumptions, uncertainty, and next actions.

It is not:

- A game.
- Fortune telling.
- A medical, legal, financial, immigration, or psychological advice product.
- A chatbot that gives a single answer.

Primary user promise:

> Upload or write your background, interests, constraints, and a key life question. LifeScope returns three possible 3-10 year paths, the opportunities and costs of each path, the confidence behind the reading, what information is missing, and what to do next.

## 3. Target Beta User

Initial beta should stay narrow.

Primary segment:

- 22-40 year-old users facing a real life choice.
- Especially career, city, study, startup, relationship/family timing, and lifestyle tradeoff decisions.
- Willing to write a meaningful self-description.
- Wants reflection and planning, not entertainment-only output.

Good first beta cases:

- "Should I leave my stable job for an AI startup?"
- "Should I go abroad for graduate school or stay in my current market?"
- "Should I move cities for career upside even if my relationship becomes harder?"
- "How do I compare income growth, health, relationship, and meaning over ten years?"

Do not broaden to all users until the product consistently feels personal and useful for these high-intent cases.

## 4. Current MVP Surface

Implemented surfaces:

- Landing promise.
- Text/file intake for background and interests.
- Assumption controls for focus, risk, stability, mobility, and what-if options.
- Consent notes for sensitive information and local redacted storage.
- Profile review before generation.
- Runtime mode selector: deterministic draft or Kimi 2.5.
- Loading panel with long-task copy for Kimi.
- One-screen answer.
- Three branch cards with probability and confidence.
- Path comparison.
- Timeline.
- Trust surface: evidence, missing information, and rerun guidance.

Current backend/API:

- `GET /api/health`
- `GET /api/runs`
- `GET /api/runs/<run_id>`
- `POST /api/profile`
- `POST /api/intake`
- `POST /api/simulate`
- `POST /api/engine-contract`
- `DELETE /api/runs/<run_id>`

Current engine modes:

- `deterministic`: fast local draft.
- `simulate_life`: real upstream engine using Moonshot / Kimi 2.5.

## 5. Beta Definition

Beta means a real external tester can safely run a Kimi-backed life simulation without developer supervision.

Beta must include:

- Chinese reports that read naturally, preserve meaning, and pass the lightweight fluency gate plus human review.
- Background job execution for Kimi runs.
- Real progress polling from server job state.
- Cancel and retry.
- Durable job/result status after page refresh.
- User/session-scoped result access.
- Delete and export controls.
- Clear provider/data-use consent before Kimi mode.
- No raw profile text in server logs or public metadata.
- Result UI that links the simplified reading back to engine artifacts or artifact-derived sections.
- A test suite covering job lifecycle, redaction, auth/session access, engine fallback, and API error paths.

Beta does not require:

- Payment.
- Full account system with passwords.
- PDF/DOCX parsing.
- Long-term memory.
- Social sharing.
- Mobile app.

## 6. Beta Roadmap

### Phase 1: Job System

Before or alongside this phase, fix the Chinese report quality bar. Invite-only beta cannot start if the report is hard to read in Chinese.

Goal: replace synchronous `/api/simulate?engine=simulate_life` with a safe long-running job flow.

Build:

- `POST /api/jobs` creates a job.
- `GET /api/jobs/<job_id>` returns status, stage, progress message, engine mode, run id, and errors.
- `POST /api/jobs/<job_id>/cancel` marks a pending/running job cancelled.
- Worker thread pool with `max_workers=1` by default for Kimi.
- Job states: `queued`, `running`, `succeeded`, `failed`, `cancel_requested`, `cancelled`.
- Store job records under `data/jobs/` or a small SQLite DB.
- Keep `/api/simulate` as deterministic-only or compatibility wrapper.

Acceptance:

- Browser submits Kimi job and receives a job id immediately.
- Page polls real job status.
- Refresh can recover the job.
- Failed jobs return a redacted error and preserve retry data.
- Completed Chinese jobs show whether `report.md` and `visual_summary.md` passed the fluency gate.

### Phase 1a: Chinese Report Fluency

Goal: make the report readable enough that a Chinese-speaking tester trusts the product.

Build:

- Treat Chinese fluency as a product release gate, not copy polish.
- Keep the lightweight artifact gate for `report.md` and `visual_summary.md`.
- Add human review for live Chinese runs before beta.
- Track examples of bad phrases and remove them from generation/localization prompts upstream.
- Prefer Chinese-first visible writing over English-first report localization for user-facing reports.

Acceptance:

- No critical semantic breaks such as "诚实答案仍是拒绝", "报告能看到", or "树故意保持".
- Branch sections include scene, rhythm, pressure, tradeoff, and landing.
- First screen is readable in about 30 seconds.
- At least 5 live Chinese runs pass human review before invite-only beta.

### Phase 2: Real Progress + Result Recovery

Goal: make Kimi feel like a trustworthy long operation instead of a frozen form.

Build:

- Connect `progress_hook` to job state.
- Frontend stages reflect actual backend stages.
- Result page loads from stored run id after completion.
- Show artifact paths in local mode for developer inspection.
- Add retry from deterministic fallback or failed Kimi job.

Acceptance:

- UI shows stage changes from the engine.
- User can leave and reopen `/api/jobs/<job_id>` or `/api/runs/<run_id>`.
- Kimi failure does not lose user context.

### Phase 3: Privacy and Session Boundary

Goal: make beta safe enough for invited testers.

Build:

- Anonymous session id stored in a secure cookie for local/beta deployments.
- Every run/job belongs to one session.
- Access checks on `GET /api/runs/<id>`, `GET /api/jobs/<id>`, delete, and export.
- Delete endpoint removes redacted run snapshot, job record, and linked engine artifact directory when requested.
- Export endpoint returns the user's redacted reading and artifact-derived summary.
- Do not log request bodies.
- Add provider consent copy before Kimi mode: user data may be sent to Moonshot/Kimi for generation.

Acceptance:

- Another session cannot fetch a run id.
- Delete removes app records and linked artifacts.
- Logs contain no raw background/interests/question/constraints.

### Phase 4: Artifact Productization

Goal: stop treating upstream artifacts as hidden files and convert them into product surfaces.

Build:

- Artifact manifest in the app response.
- Result sections sourced from `simulation.json`:
  - branch overview
  - timeline
  - probability/confidence
  - uncertainty notes
  - evidence catalog
  - intervention sensitivity
- Optional developer-only links to `report.md`, `visual_summary.md`, and `analysis_dossier.json`.
- User-facing "why this path" section derived from evidence and uncertainty, not raw dossier dumps.

Acceptance:

- Result page clearly shows what came from Kimi/upstream engine.
- Users can understand probability vs confidence.
- Evidence and missing information are not buried.

### Phase 5: Deployment Beta

Goal: invite a small private beta cohort.

Build:

- Run behind HTTPS.
- Move provider keys to environment/secret manager.
- Use persistent storage appropriate to the deployment target.
- Add request size limits.
- Add per-session rate limits for Kimi jobs.
- Add basic admin/tester allowlist.
- Add operational runbook for stuck jobs and failed provider calls.

Acceptance:

- 20-30 invited users can complete a run without local developer help.
- Product owner can inspect failures without raw private data exposure.
- Costs and runtime are visible enough to decide whether to continue.

## 7. Success Metrics

Product signal:

- Intake completion rate >= 70%.
- Profile review confirmation rate >= 60%.
- Kimi job completion rate >= 80% for valid inputs.
- First-screen "this feels like me" rating >= 50% in interviews.
- Rerun or what-if edit rate >= 25%.
- At least 20% of testers say they would pay or return after a life update.

Quality signal:

- Chinese reports are natural, coherent, and not mixed-language.
- Three branches are meaningfully different in user review.
- Result names concrete tradeoffs, not generic advice.
- Uncertainty is visible and understandable.
- No deterministic destiny language.
- No medical/legal/financial/psychological diagnosis.

Operational signal:

- Median deterministic response < 2 seconds.
- Kimi job p50 < 4 minutes, p90 < 8 minutes.
- Kimi error/fallback rate tracked separately from deterministic success.
- Zero raw long-form profile text in app run snapshots.

## 8. Key Risks

Product risks:

- Chinese output may be technically complete but too awkward to trust.
- Users may feel the output is long but not personal.
- Users may interpret probabilities as destiny.
- Users may not trust the system unless evidence and uncertainty are clear.
- Users may abandon if Kimi takes minutes without real progress.

Technical risks:

- Synchronous Kimi calls can timeout or block server capacity.
- Upstream artifact schema drift can break UI mapping.
- Fallback can silently hide Kimi failures if not made explicit.
- File-based storage will become brittle under concurrent beta usage.

Privacy risks:

- Raw personal data may leak through logs, debug artifacts, provider prompts, or artifact directories.
- Current `localOnly` copy is not a security boundary; it is a storage behavior.
- Deletion must include linked upstream artifacts, not only redacted run snapshots.
- Kimi/provider data-use terms must be surfaced before live mode.

## 9. Immediate Next Sprint

Sprint goal: make Kimi beta-safe as a long-running operation.

Tasks:

1. Add a `JobStore`.
2. Add background `JobRunner` around `run_reading`.
3. Add `/api/jobs`, `/api/jobs/<id>`, and cancel endpoint.
4. Wire `progress_hook` into persisted job stages.
5. Update frontend Kimi mode to create/poll jobs.
6. Add job lifecycle tests.
7. Add session id and ownership checks for jobs/runs.
8. Add provider consent copy for Kimi mode.
9. Add delete behavior for linked engine artifacts.
10. Run one live Kimi smoke after job flow is implemented.

PM checkpoint after sprint:

- Can an invited tester start a Kimi run, watch real progress, recover after refresh, and delete the result?
- If yes, move to private beta prep.
- If no, continue infrastructure hardening before more UX polish.
