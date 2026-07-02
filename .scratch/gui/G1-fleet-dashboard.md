# G1 — Fleet Dashboard (tracer bullet)

**Parent:** PRD 0006 / ADR-0056. **Triage:** ready-for-agent.

## What to build
The thin end-to-end path of ab_console: a deterministic fleet view-model aggregating existing
read-models, rendered as the Fleet Dashboard through the Apple-HIG design system.
- `viewmodels.fleet(...)` (pure): from `ab_obs` fleet snapshots + `fleet_totals`, `ab_monitor`
  check results, and kill-switch status → a `FleetView` (totals, per-business rows with verdict +
  worst monitor status, open-alert count, global kill-switch state). Money formatted from minor units.
- FastAPI `GET /` renders `templates/fleet.html` with the view-model; `static/console.css` is the
  design system (dark-first HIG tokens, cards, stat, status pills, table).
- States: loading is server-rendered (no spinner needed); empty (no businesses → calm onboarding);
  degraded (a read-model missing → a muted card, never blank).

## Acceptance criteria
- [ ] `fleet(...)` is pure, returns a FleetView with totals + per-business rows + alert count +
      kill-switch state; unit-tested with independent literals (healthy fleet, a bleeding business).
- [ ] `GET /` returns 200, includes the fleet totals + each business row + status pills; tested via
      TestClient.
- [ ] Empty fleet renders the onboarding empty state (tested).
- [ ] `console.css` ships the HIG token set + components; dark-first with a light `prefers-color-scheme`
      counterpart; focus-visible + semantic landmarks (header/nav/main).
- [ ] `make console` runs the app OR a render smoke; ruff + mypy strict clean; a11y basics (lang,
      landmarks, contrast tokens).
- [ ] `src/ab_console/CONTEXT.md` created + linked from `CONTEXT-MAP.md`.

## Blocked by
None — can start immediately.
