# Operationalization Phase 0+1 — issues (PRD 0009 / ADR-0061)

Vertical slices; dependency order S1 → S3 → S2 → S4 → S5 → S6.

- **S1** selection seam + fail-closed prod (tracer bullet): `ab_common.select_adapter(port, stub=, real=, critical=)` reading `AB_<PORT>_PROVIDER`; prod refuses a stubbed critical port. Convert `providers.served()`.
- **S3** eval suites for `ideation`/`product_spec`/social profiles (prereq: LLM seams can't promote without them).
- **S2** persisted model promotion: `model_promotions` table + `PromotionRegistry` reads/writes; `eval-promote` command records audited `ModelPromoted`; gateway reads persisted registry.
- **S4** console read providers → live (in-process) behind `AB_CONSOLE_PROVIDER=live|sample`.
- **S5** `growth.experiment_design_agent` Keycloak client + Vault secret + per-agent `token_provider`; `HttpGrowthPort` default via `AB_GROWTH_PORT_PROVIDER=http`.
- **S6** flip remaining Phase-1 seams by config (killswitch http, ideation/product model, icinga2) + a `live` env profile.

Deferred: Phase 2 (revenue/ads/social), Phase 3 (sandbox/deployers/approvals) — own PRDs.
