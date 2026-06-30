"""audit service — the immutable, hash-chained evidence backbone.

Append-only writer (each row hash-links the previous) plus a read API; also
consumes AgentDecisionMade to record receipt. Placeholder for slice 00;
implemented in slice 01 (and tamper test in slice 04).
"""
