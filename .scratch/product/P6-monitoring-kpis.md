# P6 — Monitoring + KPIs (Prometheus/Grafana + ab_data)

## Parent
PRD 0008 (`docs/prd/0008-product-engineering-domain.md`) · ADR-0059 (grilled decisions).

## What to build
Make the Product Engineering domain observable, reusing the M5 rail (one definition, two consumers).
A pure `ab_product` KPI projection over the initiatives store → per-`business_id` gauges
(`ab_product_initiatives` by stage, `ab_product_launched`, `ab_product_charter_conformance`), rendered
via the shared `ab_monitor.prometheus.gauge` helper and surfaced on the console `/metrics`; add
Grafana panels to the fleet dashboard. Project `ProductScaffolded`/`ProductDeployed` into `ab_data`.

## Acceptance criteria
- [ ] Pure `product_kpis` + `product_gauges` (business_id-labelled), infra-free tests with independent
      expected values; reuse the shared gauge renderer.
- [ ] `/metrics` surfaces `ab_product_*`; Grafana fleet dashboard gains product panels (JSON valid).
- [ ] Events projected into `ab_data`; `ruff` + `mypy` + `pytest` green.

## Blocked by
- P1b (events), P2 (stage data).
