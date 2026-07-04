# PRD 0011 — Async, streaming multi-agent ideation (watch the agents report in)

> Triage: `ready-for-agent`. Source: follow-up to PRD 0010 (multi-agent GLM-5.2 ideation is live but
> synchronously blocks the POST ~1:52). Reconciled via `/grill-with-docs` (4 decisions). Decisions:
> ADR-0063 (grilled). Builds on `ab_growth/multiagent.py` (`MultiAgentIdeationModel` + `AgentTrace`),
> the pure `ideate()`/`ideation_gate` (PRD 0007), `ab_console/stream.py` + `/events/stream` (the
> existing SSE + native `EventSource` rail), the `build()`/`publish_event()` emission ritual (Deepen 1,
> ADR-0060), and the console's kill-switch read. Tracker: no `gh` → issues under `.scratch/ideate-async/`.
> **Status: A1–A5 SHIPPED + live-verified. `POST /growth/ideate` returns immediately; the page streams
> started → per-agent progressed → complete over per-run SSE and swaps in the gated cards; IdeationRun*
> lifecycle events on the bus; kill-switch pre-check + mid-run abort + whole-run timeout with
> best-effort partials; reload/snapshot endpoint; `make ideate-async` demo. Commits `9decf88` (A1),
> `503c45e` (A2), `35c64bb` (A3), `fc2894c` (A4), + A5.**

## Problem statement

Multi-agent GLM-5.2 ideation works (PRD 0010) but `POST /growth/ideate` runs all 5 reasoning calls
**inside the request** and blocks ~1:52 before rendering — even with the generators concurrent
(`97dd275`). A ~2-minute blocking POST is a poor control-plane experience and ties the browser request
to a detached agent's work. The operator should trigger ideation, get an **immediate** response, and
**watch each agent report in live**, ending on the deterministic verdict.

## Solution

An **`IdeationRunner`** port with an **in-process background runner** (the stub): `POST /growth/ideate`
starts a run and returns immediately with a `run_id` + a streaming shell; an `asyncio` task drives the
existing `MultiAgentIdeationModel` + gate and pushes a **per-run SSE** frame as each agent finishes
(reusing `stream.py`), ending on a terminal frame carrying the server-rendered candidate cards. The
runner also publishes `IdeationRun*` **domain events** on the bus (audit + live feed). One active run
per business (re-submits dedup to protect the LLM budget); ephemeral capped registry. Full governance
envelope: eval-gated calls (unchanged), authoritative gate, audited start/terminal events,
kill-switch-aware abort, whole-run timeout with best-effort partials. A detached-agent or persisted-job
adapter slots in later behind the same port. Full rationale + rejected alternatives: ADR-0063.

## Grilled decisions (ADR-0063)

1. Execution = in-process `asyncio` runner behind a new `IdeationRunner` port (stub now; detached-agent
   / persisted-job adapters later behind the same seam); ephemeral capped in-process registry.
2. Progress transport = a per-run SSE stream for the browser (native `EventSource`, reuse `stream.py`)
   **+** `IdeationRun*` domain events on the bus (audit + feed).
3. Lifecycle = one active run per business; a re-submit re-attaches to the in-flight run (budget-safe);
   registry holds status/trace/candidates, capped; restart drops in-flight runs.
4. Governance = full envelope: eval-gated calls (unchanged) + authoritative gate + audited start/terminal
   events + kill-switch-aware mid-run abort + whole-run timeout with best-effort partial candidates.

## Slices (vertical, tracer-bullet first)

**A1 — Tracer: in-process runner + `run_id` + terminal SSE.** `ab_growth`: an `IdeationRunner` protocol
+ `InProcessIdeationRunner` — `start(business_id, prompt, operator) -> run_id` launches an `asyncio`
task running the existing `ideate()` multi-agent pipeline, registers a `RunState`, returns the `run_id`
immediately; `stream(run_id)` is an async iterator yielding at least a `started` frame then a terminal
`complete` frame carrying the candidates; `snapshot(run_id)` returns current state. Console: `POST
/growth/ideate` calls `start()` and returns a **streaming shell** (a `growth.html` state that opens an
`EventSource` on the stream endpoint); `GET /growth/ideate/{run_id}/stream` →
`StreamingResponse(sse_format(...))`. On `complete`, the shell swaps in the server-rendered cards.
Async tests: `start` returns a `run_id`; `stream` yields `started`→`complete`; a second `start` while
active returns the **same** `run_id` (dedup). Proves the async spine end-to-end: submit returns
instantly, cards arrive over SSE.

**A2 — Per-agent progress frames.** Thread a lightweight `on_step(step, status)` hook into
`MultiAgentIdeationModel.propose` so the runner emits a `progressed` frame as each of the 5 agents
finishes (`market_gap ✓` … `synthesizer ✓`); the shell renders a live checklist keyed by step name
(concurrent generators may finish out of order — frames carry the step, the UI is keyed, not ordered).
Tests: 5 `progressed` frames with the right step names; the hook is optional (CI/stub path unaffected).

**A3 — Domain events on the bus (audit + feed).** The runner publishes
`IdeationRunStarted/Progressed/Completed/Failed` (new `ab_schemas` events) via `build()` +
`publish_event()` (Deepen 1), so a run shows in the live feed and the audit log. Tests: events carry the
common `Envelope` (name, id, producer, `business_id` subject); the terminal event carries the candidate
count/verdict summary.

**A4 — Governance envelope: kill-switch abort + whole-run timeout.** Inject a kill-switch check + a
total-run timeout into the runner. If the business/global switch is tripped mid-run, stop before the
next GLM call and emit `IdeationRunFailed(reason="killswitch")` + a terminal `failed` frame; on timeout
emit `…Failed(reason="timeout")` + a `failed` frame that still shows best-effort partial candidates from
whatever completed. The SSE stream **always** reaches a terminal frame. Tests: tripped switch → aborts
before further calls, `failed` frame; timeout → `failed` frame + partials; eval-gate + gate still
authoritative throughout.

**A5 — Reload/snapshot + demo + docs.** `GET /growth/ideate/{run_id}` renders a snapshot — re-attach to
the stream if running, show the cards if done, redirect to `/growth` if unknown. `make ideate-async`
drives the runner start→stream→complete on a **canned fast agent** (infra-free, no GLM) as an end-to-end
demo. CONTEXT-MAP note; PRD/ADR closure; `PROJECT.md` changelog.

## Determinism boundary (the audit line)

| Advisory / transport (never gates) | Deterministic (replayable; authoritative) |
|---|---|
| the `run_id`, the SSE progress frames, the per-agent "reported in" order, the async plumbing + the agent trace | `overall_score`; `ideation_gate` (grounded + bars → PROCEED); the governed `growth.experiment.create` |

Async changes only *when* the browser learns the verdict and *what it watches* meanwhile — the same
candidates reach the same pure gate.

## Out of scope / follow-ups

- Durable run history + multi-worker/shared registry (the persisted-job adapter behind the same port).
- The detached growth-agent execution adapter (the real `growth.experiment_design_agent` running it
  out-of-process) — a later adapter behind `IdeationRunner`.
- Auth on the per-run stream beyond the existing operator identity; scheduled/autonomous runs.
- Ideation ledger-metering (still `model_gateway.complete`, not `complete_for_business` — the
  pre-existing ADR-0062 follow-up).

## Success criteria

An operator triggers ideation in `/growth` and the page responds **immediately**, then shows five
GLM-5.2 agents reporting in live (a per-agent checklist streamed over SSE), ending on the deterministic
PROCEED/REFINE/KILL cards + the advisory agent trace — with the run audited, kill-switchable, and
bounded by a timeout. A re-submit while running re-attaches instead of double-spending. Without a
promoted model the pipeline still degrades to the stub (no crash). CI stays infra-free + model-free;
ruff + mypy-strict + pytest green; the determinism boundary is intact.
