"""ab_portfolio — the Executive/portfolio context: capital allocation across businesses.

A deterministic, recommend-only engine that recycles capital from losing businesses into
winners within a portfolio budget cap. Money never moves here (human-in-the-loop, arch/06);
it emits CapitalReallocationRecommended for review. Multi-tenancy via business_id (P1)."""
