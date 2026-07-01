"""ab_factory — the Business Factory: instantiate a business from a Blueprint + capital.

Registers a business, gates it behind a real readiness check (capital funded, kill-switch
clear, compliance clear), and decides whether it may spend. Deterministic; capital is real
ledger money (see the store). Multi-tenancy via business_id (architecture P1)."""
