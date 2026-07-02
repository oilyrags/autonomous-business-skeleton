# G3 — Kill Switch / Intervention (governed + audited)

**Parent:** PRD 0006 / ADR-0056.

## What to build
The high-stakes control, done right. A deliberate UI: choose scope (global/context/agent/business),
a REQUIRED reason, and an explicit confirm that states the blast radius. The action routes through
the EXISTING governed path (gateway/killswitch), so the console can do nothing an agent couldn't;
every activation is audited. Status (active/clear + reason + who/when) is shown wherever relevant.
Read the current kill-switch state into the top bar (from G1).

## Acceptance criteria
- [ ] A pure `intervention_viewmodel(...)` for the confirm screen (scope options, blast-radius text,
      current state); unit-tested.
- [ ] POST activation routes through the governed path (not the context directly), requires a reason,
      and produces an audit record; denied-by-policy renders a calm explanation. Integration test
      skips fast without infra.
- [ ] Confirmation is deliberate (typed/explicit), reversible-where-possible messaging; the control
      is keyboard-operable and screen-reader clear.
- [ ] ruff + mypy strict clean.

## Blocked by
- G1 (design system + top-bar state).
