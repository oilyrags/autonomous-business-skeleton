# Common (shared infrastructure)

Shared technical plumbing used by every context: Postgres access + schema bootstrap, the event bus client, settings, and secrets. Not a domain — no ubiquitous language of its own; it hosts the cross-cutting terms defined in CONTEXT-MAP.md.

## Language

_No domain-specific vocabulary._ This is a support package (db, bus, config, secrets). Cross-cutting
terms it deals in — **Minor Units**, **Domain Event / Envelope**, **business_id** — are defined in
`CONTEXT-MAP.md`; the event models themselves live in `ab_schemas`.
