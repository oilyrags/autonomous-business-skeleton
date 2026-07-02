# PRD 0006 — ab_console: GUI control plane

> Triage: `ready-for-agent`. Source: `gui-engineering-prompt.md`. Design: ADR-0056 (grilled).
> Tracker: no `gh` → issues under `.scratch/gui/`. Builds on `ab_obs`, `ab_portfolio`, `ab_econ`,
> `ab_monitor`, `ab_killswitch`, `ab_audit`, and the governed gateway.

## Problem Statement

The skeleton can run a fleet of autonomous businesses, but a human has no way to *see* or *safely
intervene* in it. Every signal exists in a bounded context (health, economics, experiments, audit,
kill switch), yet an operator would have to read JSON or the ledger to know what's happening. There
is no control plane — the interface through which operators, portfolio managers, and compliance
reviewers govern the system.

## Solution

A calm, premium, trustworthy web control plane — `ab_console` — that surfaces the fleet's state at a
glance and lets operators drill in effortlessly, with high-stakes actions (kill switch, approvals)
that feel deliberate and are always governed + audited. Built skeleton-native: deterministic
view-models over the existing read-models, server-rendered with an Apple-HIG design system, running
in the repo's Python CI. The interface *disappears* when all is well and surfaces exactly what needs
attention when it isn't.

## Personas & jobs-to-be-done

1. **Operator / Platform** (high trust, technical) — "Is the fleet healthy? What needs me *now*? Let
   me drill from a red signal to its cause and, if needed, hit the kill switch safely."
2. **Portfolio manager** (outcome-focused) — "Which businesses make money? Where should capital go?
   Which experiments are winning?" — without reading code.
3. **Compliance / Security reviewer** (audit-focused) — "Show me every material decision and human
   override, searchable, deep-linked, tamper-evident."

## Core user flows

- **Scan → focus**: land on the Fleet Dashboard → a business or check is red → one click to its
  detail → see the cause (economics / experiment / anomaly) → act or acknowledge.
- **Intervene safely**: from a business (or globally) → Kill Switch → a deliberate confirm carrying
  full context (scope, blast radius, reason required) → routed through the gateway → audited →
  reflected in status.
- **Investigate**: Audit & Decision Explorer → filter by business/agent/time/type → open a decision
  → see its authority level, approval status, and linked event.
- **Edge/empty/error**: no businesses yet (onboarding empty state); a read-model unavailable (a
  degraded card, never a blank screen); an action denied by policy (a clear, calm explanation).

## Information architecture

Top bar (fleet name, environment, global kill-switch status + a "needs attention" count) → left of
content, primary nav (Fleet · Businesses · Experiments · Audit · Policy). Content is card-based,
progressive-disclosure: overview stats → tables → detail. `business_id` is a first-class route
segment (`/business/<id>`).

## Key screens & states (MVP)

1. **G1 Fleet Dashboard** — fleet totals (businesses, revenue, spend, profit, unprofitable count),
   per-business health rows (verdict + monitor status pill), open alerts (from `ab_monitor`), active
   experiments. Loading / empty / degraded states.
2. **G2 Business Detail** (`/business/<id>`) — overview (economics: profit, CAC, margin, LTV,
   payback), experiments, agents/decisions, financials (ledger view), compliance, monitor checks.
3. **G3 Kill Switch / Intervention** — a deliberate, reversible-where-possible control; scope
   (global/context/agent/business), required reason, confirmation; governed + audited.
4. **G4 Experiments** — list + result view with statistical context (p-value, lift, scale/pivot/
   kill), per business.
5. **G5 Audit & Decision Explorer** — searchable/filterable decisions + overrides + events, deep
   links, tamper-evident (hash-chain) indicator.

## Success metrics (UX + system)

- **UX**: land-to-understanding < 5s (a first-time operator names the fleet's status from the
  dashboard); core task (find a struggling business + open its cause) in < 3 clicks; WCAG 2.2 AA
  (keyboard-complete, focus-visible, contrast); no layout shift; renders < 100ms server-side.
- **System**: every mutating GUI action produces an audit record; the console can perform no action
  an agent couldn't (all through the gateway); read-models are pure + fully unit-tested.

## Implementation Decisions

- **New `src/ab_console/`**: `viewmodels.py` (pure aggregation over injected read-models),
  `app.py` (FastAPI + Jinja2 routes), `templates/`, `static/console.css` (the design system).
- View-models return plain dataclasses/dicts; templates render only (no logic). Money formatted from
  integer minor units; ratios from bps — one formatting helper.
- Governed actions call the gateway (not the contexts directly); MVP wires the kill-switch + approval
  surfaces to that path, everything else read-only.

## Testing Decisions

- Pure view-models unit-tested infra-free (independent literals) — the bulk of the logic. FastAPI
  routes tested via `TestClient` (status 200, key content present, correct view-model wired).
  Golden-HTML/snapshot for a couple of rendered fragments to catch structural regressions. An
  a11y-lint pass on templates (semantic landmarks, alt/aria, label associations). Prior art:
  `ab_data/app.py` tests, `ab_gateway` TestClient tests, `ab_obs` pure tests.

## Out of Scope

A React/Next frontend + Node toolchain (Playwright/Storybook/Chromatic); real-time websockets;
mobile-native app; live OTel/Grafana embedding (link out); the custom-dashboard builder (post-MVP).

## Further Notes

Sliced in `.scratch/gui/` and built via `/tdd`, one behaviour at a time — G1 Fleet Dashboard is the
tracer bullet (view-model → route → HIG template → tests), the rest layer on the same design system.
