# Product Engineering

Promotes a validated growth initiative into a shipped, monitored, business-wired product — as a new
business (`business_id`) or an extension of one — through a deterministic, gated SDLC. The LLM
proposes specs and design tokens; deterministic code classifies, scaffolds, themes, gates, and
ships. Design: PRD 0008 / ADR-0059; the instantiation guide's stages 8–9 made real.

## Language

**Business Charter**:
A versioned, `business_id`-scoped record of a business's identity: its design tokens (→ a unique daisyUI theme) and its tech charter (mandated stack, architecture rules, allowed dependencies). Every addition must conform; additions extend it (a new version, append-only), never contradict it.
_Avoid_: config, theme (a theme is only the rendered CSS), brand guide

**Design Tokens**:
The business's visual language as data — primary/secondary/accent/neutral colours, corner radius, type, density — rendered deterministically into a daisyUI theme (CSS custom properties, vendored, no build).
_Avoid_: styles, CSS, palette (informally)

**Tech Charter**:
The mandated stack (FastAPI + vendored daisyUI), architecture rules (`business_id` tenancy, ports+stubs, single governed ingress), and allowed dependency set a business's code must obey. Append-only across versions.
_Avoid_: tech stack, standards (when you mean this enforced record)

**Charter Conformance**:
The pure check that an addition uses the business's theme, stays within the allowed dependencies, honours every mandated architecture rule, and references a valid charter version. A failed check blocks the addition (CI + the launch gate).
_Avoid_: lint, review (this is the deterministic gate)

**Consistent Extension**:
A new charter version that grows the tech charter (rules/deps as supersets) while keeping the design language identical — the only legal way a business changes. A recoloured theme or a dropped rule is a contradiction, not an extension.
_Avoid_: update, migration

**Product Initiative**:
A validated growth outcome promoted for engineering (title, hypothesis, features, constraints; a business_id when extending). The unit the pipeline drives.
_Avoid_: ticket, feature request

**Classification**:
The deterministic decision — new business (mint a business_id) vs extension of an existing one. Never an LLM decision.
_Avoid_: routing, triage

**Product Blueprint**:
The typed engineering spec the LLM fills through a port (features, screens, design tokens); deterministically validated before the Scaffolder uses it.
_Avoid_: spec, plan (informally)

**Scaffolder**:
The deterministic generator that writes a business_id-scoped, charter-conformant FastAPI + vendored-daisyUI service from a blueprint + charter. The LLM never writes this code.
_Avoid_: generator, codegen (when you mean this pure component)

**Stage / Gate**:
A step in the gated SDLC (intake → spec → design → dpia → blueprint → scaffold → qa → launch → launched) and the deterministic-or-human condition that admits it. A failed gate halts the initiative.
_Avoid_: phase, step (loosely)

**DPIA Gate**:
The human Data Protection Impact Assessment gate. A personal-data initiative cannot reach launch until a human DPIA sign-off is recorded; a non-personal-data one auto-clears deterministically.
_Avoid_: privacy check, review

**Launch Gate**:
The human launch approval (CEO/CISO) that ships a product. The last gate before `launched`.
_Avoid_: release, deploy (deploy is the mechanical step after launch)
