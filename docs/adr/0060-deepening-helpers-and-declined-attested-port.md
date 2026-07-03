---
status: accepted
---

# Cross-cutting deep helpers, and why a shared attested console port was declined

An `/improve-codebase-architecture` pass (deletion-test discipline from `/codebase-design`) produced a
ranked report of six deepening candidates. Three landed; three were declined. This ADR records the
landed helpers (so contexts reuse them instead of re-typing the ritual) and — the load-bearing part —
**why the "shared attested console HTTP port" was declined**, so a future review does not re-suggest it
without the missing precondition.

## Landed (reuse these)

1. **`ab_schemas.events.build(event_cls, *, subject, producer, data_classification=INTERNAL, **fields)`**
   (`063c2ce`) — the single place a domain event is constructed. Fills the six envelope fields
   (`event_name` from the class, a fresh `event_id`, `occurred_at`, `producer`, `data_classification`,
   `subject_ref` from a `(type, id)` tuple); domain fields pass through `**fields`. The parameter is
   named `data_classification` (not `classification`) so an event with a domain field literally called
   `classification` (`ProductScaffolded`) adopts it too. **Never hand-write `event_id=uuid.uuid4().hex`
   again.**
2. **`ab_common.bus.publish_event(topic, key, event)`** (`063c2ce`) — the single place the Envelope→bus
   wire contract (`model_dump_json(by_alias=True)`) lives.
3. **`ab_common.eventstore.persist_and_emit(sql, params, *, topic, key, event)`** (`471d147`) — the
   single place the "publish exactly when a row changed" invariant lives (the `ab_product.store.save`
   double-publish bug class, fixed under VULN review, is now unrepresentable). Runs an idempotent write
   (`INSERT ... ON CONFLICT DO NOTHING` or a guarded `UPDATE`), commits, and publishes `event()` iff
   `rowcount == 1`; `event` is a thunk built only when it will fire.
4. **`ab_gateway.tools._validated(model_cls, args, *, what)` and `_require_serves(principal,
   business_id)`** (`76b7d32`) — the validate→`ToolDenied(400)` and tenant-bind→`ToolDenied(403)`
   (VULN-002) steps every governed handler repeats.

A full `govern()` handler pipeline (candidate #2's original framing) was **rejected** in favour of the
two guards above: the handlers vary too much (`promote_initiative` classifies before it tenant-binds;
`write_decision` clamps authority and emits nothing), so a pipeline would need enough optional callbacks
to become a shallow wide-interface wrapper — the anti-pattern deepening is meant to avoid. Extract only
what repeats *uniformly*.

## Declined: a shared attested console service port (candidate #4)

**Decision: do not introduce a shared `AttestedServicePort` / `PortHttpClient` in `ab_console` now.**

The two real HTTP adapters look similar but **do not share their operator attestation** — each forwards
the human operator's identity the way its own remote service's contract demands:

- `HttpGrowthPort` calls `growth.experiment.create` under a **service bearer token**
  (`growth.experiment_design_agent`) and records the operator as `maker` in the **tool args metadata**
  (dual attribution; the gateway reads it from there).
- `HttpKillSwitchPort` forwards **signed `X-Operator-*` headers** (`operator_identity.sign`, VULN-004)
  so the kill-switch service can authorize the actor non-spoofably.

The only code the two genuinely share is a single `httpx.post(...) → status == 200` call. Applying the
deletion test: a shared client would concentrate no real complexity — it would move a one-liner behind
an indirection (**shallow**, fails the test). And unifying the attestation itself (e.g. moving the
growth path onto signed operator headers) is a **cross-service security-contract change** requiring the
gateway to accept and verify operator headers on `/tool-call` — a behaviour/security change, not a
mechanical deepening.

Two adapters exist, but they do not vary *uniformly* across the seam, so the seam is not yet real
("one adapter = hypothetical; don't introduce a seam unless something actually varies across it").

**Revisit when** either (a) a **third** console→service HTTP adapter lands, or (b) a deliberate decision
unifies operator attestation on signed `X-Operator-*` headers across the gateway and all console ports
(a security ADR in its own right). Until then, a shared port is premature abstraction.

Candidates #5 (a KPI fold-and-render aggregator — only two call sites, `ab_growth`/`ab_product`) and #6
(splitting the 355-line `ab_gateway/tools.py` per handler) were likewise **deferred** as premature: #5
is one adapter shy of a real seam; #6 is readable today and falls out naturally after any future
`govern()`-style work.
