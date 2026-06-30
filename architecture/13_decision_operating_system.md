# 13 — Decision Operating System

The mechanism that turns autonomous activity into accountable governance. Every material decision is a first-class, auditable record tied to data, a framework, an owner, and a review.

## 1. Decision registry (the record)

Append-only store of `Decision` records. Schema (also in master prompt):

```json
{
  "decisionId": "decision_2026_001",
  "title": "Increase paid acquisition budget for Segment A",
  "boundedContexts": ["CRM and Marketing", "Finance", "Executive Strategy and Decision Intelligence"],
  "problem": "Growth target is behind plan while Segment A payback remains under threshold.",
  "context": "Q3 plan gap; cash runway 14 months; Segment A payback 8 months.",
  "options": ["hold_budget", "increase_budget_10_percent", "increase_budget_25_percent"],
  "dataUsed": ["cac_by_channel", "ltv_by_segment", "cash_forecast"],
  "sourceProvenance": ["semantic_layer.metric.cac", "semantic_layer.metric.ltv", "finance.forecast"],
  "frameworksApplied": ["LTV:CAC", "payback_period", "expected_value"],
  "expectedValue": "calculated_by_deterministic_model",
  "risks": ["channel_saturation", "forecast_error", "brand_risk"],
  "complianceImpact": "none (no new personal-data use)",
  "customerImpact": "increased reach to Segment A",
  "financialImpact": "+€X spend, projected payback 8mo",
  "securityImpact": "none",
  "reversibility": "high (spend can be cut next cycle)",
  "confidence": 0.72,
  "authorityLevel": 3,
  "approvalStatus": "approved",
  "dissent": ["CFO Agent: cash runway sensitivity noted"],
  "owner": "cmo_agent",
  "reviewDate": "2026-09-30",
  "outcomeReview": "pending"
}
```

## 2. Decision workflow (how a decision is made)

```
1. Frame      → Problem + context + boundedContexts (any agent may open a Decision)
2. Evidence   → dataUsed pulled from semantic layer ONLY (provenance attached); freshness gate
3. Options    → ≥2 real options (status-quo always included)
4. Analyze    → frameworksApplied; expectedValue computed by DETERMINISTIC model (no LLM math)
5. Risk       → risks + impact dimensions + reversibility + confidence
6. Dissent    → relevant C-agents may record dissent (never suppressed)
7. Authorize  → authority matrix (06) decides: autonomous_within_policy OR approval saga (Workflow)
8. Decide     → approvalStatus set; AgentDecisionMade emitted; Art.22 screen (09)
9. Review     → reviewDate scheduled; outcomeReview captured → learning loop
```

**Hard rules:** no decision without data + provenance + framework; expected value never computed by an LLM; safety/compliance/ethics are hard constraints (not tradeable); every decision has a review date.

## 3. Frameworks library (when each applies)

| Domain | Frameworks |
|---|---|
| Strategy/portfolio | OKRs, Porter's Five Forces, Value Chain, Three Horizons, JTBD, Real Options, McKinsey 7-S, BCG/GE portfolio matrix |
| Capital/finance | Expected value, risk-adjusted return, DCF/NPV, unit economics, contribution margin, working capital, payback |
| Growth/marketing | STP, 4Ps/7Ps, AARRR, LTV:CAC, cohort retention, MMM, attribution |
| Sales | MEDDIC/BANT, value-based selling, pipeline coverage, price elasticity, willingness-to-pay |
| Product | JTBD, opportunity scoring, RICE-style prioritization, experiment-driven |

Each decision must name the framework(s) it applied; the registry validates that a framework was cited.

## 4. Operating cadences (agentic C-suite)

| Cadence | Frequency | Owner | Inputs | Output |
|---|---|---|---|---|
| Continuous operating monitor | always-on | COO Agent | live metrics, SLOs, alerts | anomalies → decisions/incidents |
| Daily operating review | daily | COO | yesterday's KPIs, blockers | priority adjustments |
| Weekly strategy review | weekly | CEO | OKR progress, pipeline, experiments | course corrections |
| Monthly financial review | monthly | CFO | three-statement, forecast vs actual | budget/forecast decisions |
| Quarterly planning | quarterly | CEO + all | strategy, portfolio, capital | OKRs, capital allocation |
| Portfolio review | quarterly | CEO/CPO | venture gates, unit economics | scale/pivot/kill decisions |
| Risk & compliance review | monthly | CISO + CLO | risk register, DSAR/DPIA status, audit | risk acceptance, gates |
| Incident review | per incident | CTO/COO | postmortems | action items, control changes |

Each cadence reads from the **semantic layer** (one definition per KPI) and writes **Decision** records; nothing is decided on un-provenanced numbers.

## 5. Learning loop

- At `reviewDate`, the owner agent fills `outcomeReview`: did the expected value materialize? variance? what to adjust?
- Outcome reviews aggregate into a **decision-quality KPI** (Executive) and feed episodic memory (`11`) so future similar decisions are better-calibrated.
- Systematic miscalibration (confidence vs outcomes) triggers model/prompt review in the AI Platform.

## 6. Guardrails (binding)

1. Every material decision cites data, framework, assumptions, risks, dissent, review date.
2. No fabricated sources or numbers (provenance enforced; citations verifiable).
3. Safety, compliance, ethics are hard constraints, not optimization tradeoffs.
4. Expected value / financial math is deterministic, not LLM-generated.
