# PRD 0009 — Operationalization Phase 0+1 (stub → real, config-selected)

> Triage: `ready-for-agent`. Source: a UAT bring-up that ran the full secure mesh + `make demo` and
> hand-wired the console to live state, surfacing every stub seam. Reconciled via `/ask-matt` →
> `/grill-with-docs` (5 decisions). Decisions: ADR-0061 (grilled). Builds on `ab_gateway`
> (`providers.served()`, `model_gateway` eval gate), `ab_evals`, `ab_console` (`_SAMPLE_` providers,
> `growth_port`/`killswitch_port`, VULN-001), `ab_monitor` (`icinga2`, M5), `config/keycloak`,
> `ab_common.config` (`_secret`/`AB_ENV`, VULN-005). Tracker: no `gh` → issues under `.scratch/ops/`.

## Problem statement

The skeleton is build-proven but runs on **stubs and sample data** by design (ports+stubs, infra-free
CI). To operate a live business it must select **real adapters** in a deployment — but only the model
provider has a stub↔real switch today (`AB_MODEL_PROVIDER`); every other port is hardcoded to its
`Stub*`, the console renders 10 `_SAMPLE_` providers, and the LLM seams abstain because **no model is
eval-promoted** (and `PromotionRegistry` is in-memory, so nothing sticks). There is no uniform,
safe way to go live incrementally without silently running money/egress paths on stubs.

## Solution

A **per-port env factory** (`AB_<PORT>_PROVIDER`) that selects stub vs real per seam, **fail-closed for
critical ports in prod**; a **persisted, eval-gated model promotion**; the console **read-in-process /
write-over-governed-HTTP**; and **one Keycloak client per fronted agent**. Phase 0 lights up the LLM
seams (the keystone); Phase 1 flips every seam whose real adapter already exists. Stubs remain the CI
default. Full rationale + rejected alternatives: ADR-0061.

## Grilled decisions (ADR-0061)

1. Selection = a per-port `served()`-style env factory (`AB_<PORT>_PROVIDER`, default `stub`), config
   via `ab_common.config` `_secret()`/`AB_ENV`.
2. Prod defaults **fail-closed** for critical seams (revenue, ads, social publish, sandbox, deployers);
   advisory/read seams may abstain/stub.
3. Model promotion is **persisted + explicit**: a promotions table + an ops/CI `eval-promote` run that
   records an audited `ModelPromoted`; needs an eval suite per LLM task-profile.
4. Console **reads in-process** (each context's read-only functions), **writes over governed HTTP**.
5. **One Keycloak client per fronted service-agent** (client-credentials, Vault secret, dual attribution).

## Slices (vertical, tracer-bullet first)

**S1 — The selection seam + fail-closed prod (tracer bullet).** A shared `ab_common` helper
`select_adapter(port_name, *, stub, real, critical)` reading `AB_<PORT>_PROVIDER` (default `stub`),
raising in `AB_ENV=prod` when a `critical` port is left on stub. Convert `providers.served()` to use it
(no behaviour change). One infra-free demo: a critical port on stub in prod raises; advisory abstains.

**S2 — Persisted model promotion + the `eval-promote` command.** A `model_promotions` table +
`PromotionRegistry` reads/writes it; `eval-promote <profile> --provider portkey` evaluates the live
model once against the profile's suite, and on a pass records `ModelPromoted` (audited). Gateway reads
the persisted registry at boot. (No live paid call in CI — the offline stub path stays; Portkey path is
exercised behind an opt-in env.)

**S3 — Eval suites for the LLM task-profiles.** Add `ideation`, `product_spec`, and social-content
eval sets to `ab_evals/suites.py` (capability + safety-canary dimensions, `min_score`), so those
profiles are promotable at all. Without this, S2 can't light up the LLM seams.

**S4 — Flip the console read providers to live (in-process).** Replace the 10 `_SAMPLE_` providers with
reads from the owning contexts (fleet→`ab_obs`, econ→`ab_econ`, checks→`ab_monitor`,
snapshots→`ab_factory`/`ab_portfolio`, audit/experiments/products→their stores) behind
`AB_CONSOLE_PROVIDER=live|sample`. (Folds in the UAT launcher's audit/kill-state/experiments/products
wiring.)

**S5 — Growth agent identity + `HttpGrowthPort` default.** Add a `growth.experiment_design_agent`
Keycloak client (client-credentials) to `config/keycloak/ab-realm.json` + seed its secret to Vault; a
console `token_provider` that mints per-agent tokens; select `HttpGrowthPort` when
`AB_GROWTH_PORT_PROVIDER=http`. The console's Propose then hits the **containerized** gateway as the
growth agent (operator as maker). Verified live.

**S6 — Flip the remaining Phase-1 seams by config.** `AB_KILLSWITCH_PORT_PROVIDER=http` →
`HttpKillSwitchPort` (default in a live profile); `AB_IDEATION_PROVIDER`/`AB_PRODUCT_MODEL_PROVIDER`
auto-light once S2/S3 promote a model; `AB_MONITOR_EXPORTER=icinga2` → `Icinga2RestExporter` (monitoring
compose profile + secret). A `live` env profile (compose/env file) that sets the Phase-1 seams together.

## Out of scope / follow-ups (own PRDs)

- **Phase 2** real adapters: `ab_revenue` (Stripe), `ab_ads` (Google/Meta), `ab_social`
  (content/publisher/metrics), `ab_growth` grounding (`ab_data`).
- **Phase 3** real adapters: `ab_sandbox` (isolated execution), `ab_mvp`/`ab_product` deployers
  (compose `ventures` → k8s/cloud) + scaffold writer, console approval/product ports (gateway-backed).
- Global/portfolio LLM-spend cap (per-business `llm_budget` is already enforced by the gateway).

## Success criteria

A deployment can go live **incrementally** by setting `AB_<PORT>_PROVIDER` + secrets: Phase 1 seams run
real (kill switch, growth propose, monitoring, console live reads) while un-built seams stay stubbed;
`AB_ENV=prod` refuses to start on a stubbed **critical** seam; a real model is promoted through an
audited, eval-gated, persisted decision and the LLM seams light up automatically. Stubs stay green in
infra-free CI; ruff + mypy-strict + pytest green; the determinism boundary is intact.
