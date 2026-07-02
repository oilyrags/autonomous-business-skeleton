---
status: accepted
---

# ab_console — GUI control plane (architecture + design system)

Plans and founds the human control plane from `gui-engineering-prompt.md` — the interface operators
use to govern, observe, and intervene in a fleet of autonomous businesses. Designed via
`/grill-with-docs`; the stack/fit decision was grilled, the rest follows the repo's rules
(determinism boundary; governed actions through the gateway; `business_id` multi-tenancy).

## Decisions (grilled)

- **Skeleton-native `ab_console`, not a separate React/Next stack.** A new `src/ab_console/` FastAPI
  service serving a hand-crafted server-rendered UI. The **view-model layer is a deterministic pure
  core** (like every other context): it aggregates the existing read-models (`ab_obs.fleet_overview`
  /`fleet_totals`, `ab_portfolio.allocate`, `ab_econ`, `ab_monitor.demo_suite`, kill-switch, audit)
  into presentation-ready shapes. Jinja2 templates render them; a hand-built **Apple-HIG design
  system in CSS** provides the craft. Runs in the repo's Python CI — view-models unit-tested, routes
  via `TestClient`, no foreign toolchain. A React frontend can later consume the same view-models as
  JSON, but is out of scope.

## Determinism & governance (not grilled)

- **Read-first, deterministic.** Every view-model is a pure function over injected read-models — no
  business logic in templates, no money/identity decision in the GUI. Fully testable.
- **Interventions are governed, never bypassed.** Kill switch, approvals, and overrides go through
  the **existing gateway** (policy + authority + audit), so the console cannot do anything an agent
  couldn't; every GUI action that mutates is audited (the prompt's "audit everything the user does").
  MVP is read-only + the kill-switch/approval surfaces wired to the governed path.
- **Multi-tenancy.** `business_id` is a first-class route + view-model dimension throughout.

## Design system (Apple HIG — dark-first, calm, accessible)

A single CSS custom-property token set (`ab_console/static/console.css`), no framework:

- **Color (dark-first, light counterparts via `prefers-color-scheme`)**: layered surfaces
  (`--bg-base #0b0c0e`, `--bg-elev #16181d`, `--bg-raised #1e2127`), text tiers
  (`--fg #f2f3f5`/`--fg-2 rgba(255,255,255,.62)`/`--fg-3 rgba(255,255,255,.40)`), a single calm
  accent (`--accent #0a84ff`), and restrained semantics (`--ok #30d158`, `--warn #ff9f0a`,
  `--crit #ff453a`). WCAG 2.2 AA contrast on every text/surface pair.
- **Type**: system stack (`-apple-system, "SF Pro Text", Inter, …`); scale 12/13/15/17/22/28/34;
  weights 400/500/600; generous line-height. Data is the hero (deference).
- **Space**: 4px grid (4/8/12/16/24/32/48). **Radius**: 8/12/16. **Motion**: 160–220ms ease,
  `prefers-reduced-motion` honored (no motion when asked).
- **Components**: card, stat, status pill (ok/warn/crit), data table, top bar, empty/loading/error
  states — each intentional. Keyboard-navigable, focus-visible rings, semantic HTML + ARIA.

## Plan shape

The plan is PRD 0006 + issues in `.scratch/gui/`. MVP screens: **G1 Fleet Dashboard** (tracer
bullet), **G2 Business Detail**, **G3 Kill Switch / Intervention** (governed + audited), **G4
Experiments**, **G5 Audit & Decision Explorer**. Post-MVP: portfolio analytics, policy/config,
approval workflows, custom dashboards.

## Shipped

- **G1 (Fleet Dashboard, tracer bullet):** pure `viewmodels.fleet(...)` → `FleetView` (totals via
  `ab_obs.fleet_totals`, per-business rows with the worst `ab_monitor` status, attention-first sort,
  alert count, kill-switch state) + `fmt_money` (integer minor units → money); FastAPI `GET /`
  rendering `templates/fleet.html` (injectable fleet provider → empty/kill-switch states testable);
  `static/console.css` design system (HIG tokens, top bar, nav, stats, pills, table, banner, empty
  state; light `prefers-color-scheme` + `prefers-reduced-motion` honored); `make console` render
  smoke (CI) + `make console-serve`. `CONTEXT.md` + map link. 10 tests (5 view-model + 5 route/smoke).

- **G2 (Business Detail):** pure `business_detail(business_id, snapshots, economics, checks,
  experiments) -> BusinessView | None` — unit economics (`ab_econ`: CAC, gross margin, LTV,
  payback), the business's own monitor checks and experiments (never another's), worst status;
  `GET /business/{id}` renders it; an unknown id renders a calm 404 (`notfound.html`).
- **G3 (Kill Switch / Intervention):** the deliberate control — scope options with **blast-radius
  text**, a **required, audited reason**, and a **typed confirm phrase** (`HALT`); the POST parses
  the form with the stdlib (no python-multipart dep) and dispatches through the **`KillSwitchPort`**
  (stub records; `HttpKillSwitchPort` targets the real governed service at `:18002`, which persists,
  publishes the priority event, and audits). Missing reason → 400; wrong phrase → 400; port failure
  → 502 with a calm explanation. An integration test reaches the live service and skips without it.
- **G4 (Experiments):** `experiment_row(exp, decision)` shapes `ab_growth` outcomes;
  `experiments_view(rows, business_id=…)` filters; `GET /experiments` shows decision pills +
  p-value/lift/control→variant — the evidence, legible, numbers un-hidden.
- **G5 (Audit & Decision Explorer):** `audit_view(rows, business_id=…, agent_id=…,
  integrity_intact=…)` — filterable decision rows (agent, authority level, approval status,
  business deep-link) under a **hash-chain-intact** indicator; `GET /audit` with query-param filters
  and a filter form.
- **Chrome:** every page shares the top bar (kill-switch state + alert count) and nav with
  `aria-current` via a `Chrome` dataclass; all providers are injectable dependencies.
- Totals: 22 infra-free console tests + 1 skipping integration test.

- **v0.2 (review response — command center):** **KPI sparklines** on the fleet rows (pure
  `sparkline_points` → inline SVG polyline, no chart library; profit-colored, aria-labelled);
  **Live feed** (`/feed` + `/events/stream`) — Server-Sent Events consumed by the browser's native
  `EventSource` (zero client framework/toolchain); the event source is an injectable provider (stub
  replays samples and ends; live = a bus consumer on the same seam); **Decision OS workspace**
  (`/decisions`) — the pending high-stakes queue, highest authority first, with evidence (kind,
  maker, amount, business link) and approve/reject through an **`ApprovalPort`** (stub records; a
  gateway-backed adapter lands with the backend approval queue) — a rejection requires an audited
  note; 400/400/502 error paths. Nav gains Decisions + Live feed. 11 new tests (33 console total).

## Considered: Webstudio (open-source visual builder)

Offered by the owner as a possible accelerator. Declined for the console: Webstudio is a
React-runtime visual site builder with its own Node toolchain/publishing — adopting it would
reintroduce the parallel stack decision #1 rejected, and the console is data-driven server-rendered
views, not authored pages. Where it *is* a good fit later: a real `ab_mvp` deployer adapter could
publish generated landing pages to a self-hosted Webstudio behind the existing `Deployer` port.

## Deferred / out of scope

A React/Next frontend + its toolchain (Playwright/Storybook/Chromatic); real-time websockets (MVP
polls / HTMX); mobile-native companion; the full visual-regression pipeline (the design system + a
few golden-HTML tests stand in). These need a Node toolchain the Python CI doesn't run.
