"""ab_growth — the Experimentation & Growth context: the revenue-discovery loop.

Deterministic experiment decisioning (scale / pivot / kill / continue) gated on statistical
significance + guardrail metrics (CAC, budget), scoped per business (Blueprint / business_id).
LLMs may propose experiments; this deterministic engine decides what to do with the evidence.
"""
