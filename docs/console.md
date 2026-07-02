# ab_console — operator guide & verification report

The human control plane for the autonomous-business fleet. UI: daisyUI + Tailwind (vendored, no build step, no CDN), dark/light toggle in the top bar. Design: ADR-0056; requirements: PRD 0006;
issues: `.scratch/gui/`.

## Running it

```
make console          # CI render smoke — proves the page + design system render (no infra)
make console-serve    # run it live at http://localhost:8600
```

**Every route requires an authenticated operator** (VULN-001 / ADR-0057). In production a trusted
reverse proxy authenticates the human (OIDC) and forwards signed identity headers
(`X-Operator-Id` / `X-Operator-Role` / `X-Operator-Sig = HMAC-SHA256(AB_OPERATOR_AUTH_SECRET,
"id:role")`); the console verifies them and default-denies (401) otherwise. Mutations (halt,
approve/reject) additionally need a mutating role (`operator`/`security`/`admin`) and are recorded
against the real operator id. `/metrics` is the one exception (Prometheus scrape; restrict it at the
network layer). To reach it locally without the proxy, send the three headers — get a signature from
`python -c "from ab_console.auth import sign_identity; print(sign_identity('you','operator'))"`.

The MVP ships with deterministic sample providers so every screen renders with no infra. A live
deployment replaces the providers in `ab_console/app.py` (each is a FastAPI dependency) with real
reads: ledger → `ab_obs` snapshots, `ab_monitor` checks, the kill-switch table, `ab_growth`
outcomes, and the `decisions` table.

## Screens

| Route | What it's for |
|---|---|
| `/` | **Fleet Dashboard** — totals, per-business health rows (attention first), alerts, kill-switch state |
| `/business/<id>` | **Business Detail** — unit economics (CAC, margin, LTV, payback), its checks, its experiments |
| `/decisions` | **Decision OS workspace** — pending high-stakes decisions (authority-first) with evidence; approve/reject through the governed `ApprovalPort` (note required to reject, audited) |
| `/feed` | **Live feed** — domain events streamed over SSE (native `EventSource`; stub replays samples, live = bus consumer) |
| `/experiments` | **Experiments** — decisions with the statistics visible (p-value, lift, control→variant); `?business_id=` filters |
| `/audit` | **Audit & Decision Explorer** — filterable decisions (agent, authority L0–L5, approval), hash-chain-intact indicator |
| `/killswitch` | **Kill Switch** — deliberate halt: blast-radius scopes, required audited reason, typed `HALT` confirm |

**Interventions are governed.** The kill-switch POST dispatches through `KillSwitchPort`; the real
adapter (`HttpKillSwitchPort`, `AB_KILLSWITCH_URL`, default `http://localhost:18002`) posts to the
existing kill-switch service, which persists, publishes the priority event, and audits — the console
can do nothing an agent couldn't.

## Verification report

**Automated (runs in CI, every push):**
- 23 console tests: pure view-model units (aggregation, filters, money formatting, attention-first
  sort), route tests via `TestClient` (every screen's happy path, the empty-fleet onboarding state,
  the kill-switch banner, the calm 404, all three kill-switch error paths 400/400/502), a render
  smoke pinning `make console`, and an integration test that reaches the live kill-switch service
  (skips without it). Full repo suite green; ruff + mypy strict clean.
- Server-rendered pages, no client JS: render cost is one template pass (sub-millisecond in the
  smoke); zero layout shift by construction.

**Accessibility (by construction, in the design system):**
- Semantic landmarks (`header`/`nav`/`main`), `lang`, labeled form controls, table `scope` headers,
  `role="alert"` on banners, `aria-current` nav state.
- `:focus-visible` rings on every interactive element; the whole UI is keyboard-operable (links,
  form fields, radio scopes, submit).
- Dark-first palette with WCAG-AA-contrast text tiers; light `prefers-color-scheme` counterpart;
  `prefers-reduced-motion` disables transitions; tabular numerals for scannable figures.

**Honest gaps (deferred, per ADR-0056):**
- No visual-regression pipeline or browser E2E (would need a Node toolchain); golden coverage is
  content-assertion based.
- No live usability sessions with the three personas yet — the success metrics in PRD 0006
  (land-to-understanding < 5s; struggling-business-to-cause < 3 clicks) are designed-for but
  unmeasured. Run them when the console meets real operators.
- An automated axe-style a11y audit is not wired in; the checklist above is enforced by review +
  template tests, not tooling.

## Post-MVP (from PRD 0006)

Portfolio analytics + capital-allocation surfaces, policy/config management, approval workflows on
the authority matrix, custom dashboards, live-updating (HTMX/websocket) providers.
