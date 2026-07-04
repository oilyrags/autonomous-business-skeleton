---
status: accepted
---

# Async, streaming multi-agent ideation (kick-off → watch agents report in)

Follows ADR-0062 (multi-agent GLM-5.2 ideation). That pipeline is live but **synchronous**: `POST
/growth/ideate` runs all 5 GLM-5.2 reasoning calls inside the request handler and blocks ~1:52 before
returning the page (even with the 3 generators concurrent, `97dd275`). A ~2-minute blocking POST is a
poor control-plane UX and couples the browser request lifetime to a detached agent's work. Intent: the
operator triggers ideation, gets an **immediate** response, and **watches each agent report in live**
(market-gap → adjacent → contrarian → critic → synthesizer → gated verdict). Grilled via
`/grill-with-docs` (4 decisions). Plan: PRD 0011.

The skeleton already has the rail for this: `ab_console/stream.py` + `/events/stream` stream Server-Sent
Events to the browser's **native `EventSource`** (no HTMX, no client framework, no toolchain) for the
live feed. Async ideation reuses that exact rail — no new client tech.

## Decisions (grilled)

1. **Execution = an in-process runner behind a new `IdeationRunner` port.** `POST /growth/ideate`
   returns immediately with a `run_id`; an in-process `asyncio` background task owns the run after the
   response returns, driving the existing `MultiAgentIdeationModel` + pure `ideate()`/`ideation_gate`
   (both **unchanged**). Shipped as the **stub** behind an `IdeationRunner` seam so a later
   **detached-agent adapter** (the real `growth.experiment_design_agent` running it out-of-process,
   publishing progress) slots in behind the same interface — the ports+stubs pattern the skeleton uses
   everywhere. Run state is an **ephemeral, capped in-process registry** (lost on restart, single-worker
   — acceptable for this slice; durability is the later adapter's job). (Rejected now, kept as adapters:
   detached growth agent up front; a persisted `IdeationRun` job + worker — both heavier than the slice
   needs and both expressible behind the same port later.)

2. **Progress transport = a per-run SSE stream for the browser + domain events on the bus.** A dedicated
   `GET /growth/ideate/{run_id}/stream` (native `EventSource`, reusing `stream.py`'s `sse_format`) drives
   progressive rendering: a frame per agent as it finishes, then a terminal `complete` frame carrying the
   server-rendered candidate cards. The runner **also** publishes `IdeationRunStarted/Progressed/
   Completed/Failed` **domain events** on the bus, so audit + the live feed see the run — the per-run SSE
   endpoint is just the tight, filtered view of the same facts. (Rejected: browser subscribes to the
   shared `/events/stream` and filters by `run_id` — couples the workspace to the global feed + needs
   client-side filtering; a poll endpoint — coarse, chattier, no true streaming.)

3. **Lifecycle = one active run per business, dedup re-submits, ephemeral capped registry.** A second
   submit while a run is in flight **re-attaches to it** rather than starting a second run — the LLM
   budget is a governed resource and mashing the button must not multiply GLM spend. The registry holds
   `run_id → {status, partial trace, final candidates}`, capped (last N runs / TTL); reload within the
   process re-attaches to the stream or shows the finished cards; a restart drops in-flight runs.
   (Rejected: unbounded concurrent runs — no budget guard; persisted browsable history — that is the
   persisted-job adapter, out of slice.)

4. **Governance = the full envelope, because a detached run raises the robustness bar.** Each GLM call
   still routes through eval-gated `model_gateway.complete` (only a promoted model serves — unchanged);
   the pure `ideation_gate` stays the sole decider (the streamed trace is advisory display, never an
   input to the gate); **audited** `IdeationRunStarted` + terminal event (operator, `business_id`,
   `run_id`, candidate count); **kill-switch-aware abort** — if the business/global switch is tripped
   mid-run the runner stops spending on GLM and emits a terminal `failed` frame; a **whole-run timeout**
   emits a terminal `failed`/`timeout` frame and shows best-effort partial candidates. A detached agent
   action with no terminal-failure state or kill-switch respect is exactly where cutting a corner would
   be regretted. (Rejected: governance-only, defer robustness — a hung run leaves the SSE stream with no
   terminal state; happy-path only — ships a governance gap.)

## Determinism boundary (unchanged, restated)

| Advisory / transport (never gates) | Deterministic (replayable; authoritative) |
|---|---|
| the `run_id`, the SSE progress frames, the per-agent "reported in" order, the whole async plumbing + the agent trace | `overall_score`; `ideation_gate` (PROCEED needs grounded + bars); the governed `growth.experiment.create` a PROCEED idea reaches |

Making ideation async changes **nothing** about the decision — the same candidates reach the same pure
gate. Async only changes *when* the browser learns the answer and *what it watches* while it waits.

## Consequences

- The control plane feels instant: submit returns immediately and the operator watches five GLM-5.2
  agents report in, ending on the deterministic verdict — the "reasoning at every gate" intent, live.
- Reuses the existing SSE rail (`stream.py` + native `EventSource`), the `build()`/`publish_event()`
  emission ritual (Deepen 1), the `MultiAgentIdeationModel` + gate, and the kill-switch read the console
  already has — no new framework, no client toolchain, CI stays infra-free + model-free.
- The `IdeationRunner` port keeps the production shape open: a detached-agent or persisted-job adapter
  drops in later without touching the console or the gate.

## Shipped (A1–A5)

- **A1** (`9decf88`) `ab_growth/ideation_runner.py`: `IdeationRunner` port + `InProcessIdeationRunner`
  (asyncio task, blocking pipeline in a thread executor, ephemeral capped registry, dedup). `POST
  /growth/ideate` returns a streaming shell; `GET /growth/ideate/{run_id}/stream` drives the native
  `EventSource`; the terminal `complete` frame carries the server-rendered cards.
- **A2** (`503c45e`) an `on_step` hook on `MultiAgentIdeationModel` → a `progressed` frame per agent
  (generators emit the moment they finish; UI keyed by step name) framed by started…complete.
- **A3** (`35c64bb`) `IdeationRunStarted`/`Completed`/`Failed` (new `ab_schemas` events + a
  `growth.ideation.run` topic + AsyncAPI docs) via an injected sink, wired to the bus only under a live
  bus. Per-agent progress stays SSE-only (advisory transport, not a durable audit fact) by design.
- **A4** (`fc2894c`) kill-switch pre-check (halted → no spend), whole-run timeout, mid-run abort (the
  model polls `should_abort` before critic/synth), best-effort partial cards (a generator-pool snapshot
  gated through `ideate.judge_candidates`), always a terminal `failed` frame + `IdeationRunFailed`.
- **A5** `GET /growth/ideate/{run_id}` reload/snapshot (re-attach if running, cards if done, bounce to
  `/growth` if unknown); `make ideate-async` (canned, infra-free) streams start → 5 agents → gated
  cards; docs closed. Live-verified end to end through the console.

## Out of scope / deferred

Durable run history + multi-worker/shared registry (the persisted-job adapter behind the same port);
the detached growth-agent execution adapter; auth on the per-run stream beyond the existing operator
identity; scheduled/autonomous ideation runs; ideation ledger-metering (the pre-existing ADR-0062
follow-up — still `complete`, not `complete_for_business`).
