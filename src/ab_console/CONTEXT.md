# Console

The human control plane: a server-rendered web UI over the fleet. Deterministic view-models
aggregate the existing read-models; templates + a hand-crafted Apple-HIG design system render them.
Read-first — any mutating action routes through the governed gateway and is audited.

## Language

**View-Model**:
A pure, presentation-ready shape aggregated from the domain read-models (no logic in templates); the testable seam between the domain and the UI.
_Avoid_: DTO, model (a Model is a domain aggregate), context (a Jinja context is the render dict)

**Fleet View**:
The dashboard view-model — fleet totals + per-business rows (verdict + worst health) + alert count + kill-switch state, surfaced attention-first.
_Avoid_: dashboard data, summary

**Design System**:
The single token set + components (dark-first HIG: surfaces, text tiers, one accent, semantics; type/space/motion) in `static/console.css`.
_Avoid_: theme, stylesheet (informally), CSS (when you mean the system)

**Status Pill**:
The compact ok/warning/critical indicator; the calm signal of a row's health.
_Avoid_: badge, chip, tag

**Intervention**:
A high-stakes governed action from the UI (kill switch, approval, override) — deliberate, audited, and unable to exceed what an agent could do.
_Avoid_: action, command (informally)
