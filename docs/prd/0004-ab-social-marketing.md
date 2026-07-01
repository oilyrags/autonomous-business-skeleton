# PRD 0004 — ab_social: multichannel content generation & distribution

> Triage: `ready-for-agent`. Source: `plan.md` (AetherSocial). Design: ADR-0054 (grilled).
> Tracker: no `gh` → issues under `.scratch/`. Builds on ab_growth, ab_playbook, ab_ads, ab_org,
> the gateway LLM-budget path, and the ledger.

## Problem Statement

A business in the portfolio has no way to run its **marketing** — generate on-brand content, publish
it across multiple social platforms, measure engagement, and get better over time — the way it can
already take payments, buy ads, and allocate capital. `plan.md` specifies a powerful but heavyweight
standalone system; the owner wants that capability **inside this skeleton**, governed and per-business.

## Solution

A new `ab_social` bounded context: deterministic cores decide *what* to post and *whether* it's fit
to publish; injected **ports** (stub by default) reach the LLM/image/publish/metrics externals; and
self-optimization reuses the existing experiment engine. A post variant is an `ab_growth` experiment
arm, so engagement data drives scale/pivot/kill and reweights the brand's `SocialProfile`; winning
patterns distil via `ab_playbook`. Publishing is governed (authority-gated, audited, configurable
human review). Content-LLM cost meters to the ledger; boosts flow through `ab_ads`. Everything is
scoped by `business_id` and runs end-to-end in CI on stubs.

## User Stories

1. As a brand operator, I want a `SocialProfile` (voice, weighted pillars, platforms + format mix,
   posting rules, KPI weights, review mode) per business, so my marketing is configured, not coded.
2. As a content planner, I want a deterministic plan (pillar → platform → format → timing) drawn from
   the profile weights + recent performance, so posting is on-strategy and repeatable.
3. As a copywriter agent, I want copy generated behind a `ContentGenerator` port, so a real content
   LLM (via the gateway) drops in later without changing the planner or QA.
4. As a brand-safety reviewer, I want a deterministic QA gate that rejects posts violating posting
   rules (forbidden terms, missing required elements, value/promo ratio), so nothing off-brand ships.
5. As a growth agent, I want each post published as an experiment variant, so engagement is an
   `ab_growth` experiment that concludes scale/pivot/kill.
6. As a publisher, I want a governed `Publisher` port (stub) that is authority-gated and audited, so
   an outward-facing post can't bypass governance.
7. As a brand operator, I want a `review_mode` (human-approval-first-N / always / never), so I control
   the human gate on the first outward-facing posts.
8. As an analyst, I want a `MetricsSource` port returning per-post metrics, normalized into a single
   composite engagement score (bps) from my KPI weights, so cross-platform performance is comparable.
9. As a strategist, I want winning formats/pillars to reweight the `SocialProfile` automatically, so
   the brand's plan improves from real performance.
10. As a portfolio owner, I want cross-brand winning patterns distilled via `ab_playbook`, so what
    works transfers between brands (aggregate-only, no leakage).
11. As finance, I want content-LLM cost metered to the ledger and boosts routed through `ab_ads`, so
    marketing spend is attributable and budget-enforced per business.
12. As an integrator, I want `ContentPublished` and `PostMetricsCollected` events on the bus
    (contract-tested), so downstream (obs, portfolio) integrates without reading ab_social's store.
13. As a platform owner, I want every external (LLM/image/publish/metrics) behind a port with a stub,
    so the whole loop runs in CI and real Postiz/ComfyUI/DSPy adapters drop in behind the interface.

## Implementation Decisions

- **New `src/ab_social/`** context. Pure cores (`ab_growth`/`ab_econ` style) + injected ports
  (`ChatClient`/`ledger` pattern). Money integer minor units; ratios in bps.
- **`SocialProfile`** (Pydantic, per `business_id`): voice, `pillars: list[(name, weight)]`,
  `platforms: list[(name, format_mix)]`, posting_rules (min_value_ratio, forbidden terms, required
  elements), `kpi_weights`, `review_mode`.
- **Deterministic cores**: `plan(profile, *, performance) -> list[ContentPlanItem]` (weighted
  selection); `qa(draft, profile) -> QaResult` (posting-rules + forbidden-terms gate + variant
  choice); `composite_score(metrics, kpi_weights) -> int` (bps); the optimization reweighting that
  turns concluded experiments into a new `SocialProfile`.
- **Ports** (Protocol + stub): `ContentGenerator.write(item, profile) -> Draft`; `Publisher.publish(
  post) -> PublishResult(platform_post_id)`; `MetricsSource.metrics(platform_post_id) -> PostMetrics`.
  Image generation reuses/mirrors the deployer-port shape.
- **Governance**: a publish routes an authority check via `ab_org.route`; `review_mode` decides
  whether it needs human approval; the act is audited. Content-LLM cost uses the gateway's
  `within_llm_budget` + `{business_id}:llm_spend`; boosts call `ab_ads`.
- **Optimization = ab_growth + ab_playbook**: a post variant → an `ab_growth.Experiment` arm;
  `ExperimentConcluded` (scale/pivot/kill) reweights the profile; `ab_playbook.extract_playbook`
  distils cross-brand winners.
- **Events**: `ContentPublished(business_id, platform, platform_post_id, format, variant, cost_minor)`
  and `PostMetricsCollected(business_id, platform_post_id, composite_score_bps, ...)` — contract-driven.

## Testing Decisions

- Good tests exercise the port/pure-function/event, not internals; expected values from independent
  literals/worked examples (prior art: `ab_growth`, `ab_econ`, `ab_ads`, `ab_sales`).
- Pure cores unit-tested infra-free in the CI suite; ports tested via their stubs; each event via the
  AsyncAPI contract test; a `make social` demo runs plan → generate(stub) → QA → publish(stub) →
  metrics(stub) → score → experiment outcome end-to-end.

## Out of Scope

Real Postiz/ComfyUI/content-LLM/analytics adapters; DSPy compilation; video generation; a LangGraph
runtime (the deterministic cores + the existing bus are the skeleton's orchestration); a web
dashboard.

## Further Notes

Sliced in `.scratch/social/` and built via `/tdd`, one behaviour at a time. The plan's
"self-optimizing autonomous loop" becomes: `plan → generate → QA → govern/publish → metrics → score
→ ab_growth experiment → reweight profile → ab_playbook distil` — deterministic where it must be, LLM
only for copy, governed at the outward edge.
