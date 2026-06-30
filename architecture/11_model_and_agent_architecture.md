# 11 — Model & Agent Architecture

The substrate every agent runs on: a vendor-swappable model gateway, a governed tool registry, an agent runtime with memory, and an evals/tracing loop. **LLMs reason; deterministic systems execute.**

## 1. Model Gateway (single ingress to all models)

- **All model access goes through the gateway** — no agent calls a vendor SDK directly. This is the swappability boundary.
- Routing is by **Task Profile**, not by model name. An agent declares `taskProfile` (e.g. `financial_reasoning`); the gateway maps it to a model + parameters + a `fallbackProfile`.

```
TaskProfile → {primaryModel, params, guardrails, fallbackProfile, costBudget, evalGate}
```

| Task profile (examples) | Primary (open-weight default) | Managed alt | Fallback profile |
|---|---|---|---|
| executive_reasoning | Llama-3.x-70B / Qwen-2.5-72B | Claude/GPT-class | structured_decision_template |
| financial_reasoning | Qwen-2.5-72B | managed frontier | **deterministic_finance_workflow** |
| code_generation | Qwen-Coder / DeepSeek-Coder | managed frontier | human_engineer_review |
| customer_reasoning (RAG) | Llama-3.x-8B/70B | managed | escalate_to_human |
| compliance_workflow | Llama-3.x-70B | managed | human_dpo_review |
| classification/extraction | Mistral / Gemma small | managed | rules_engine |
| embeddings | bge/e5 open models | managed embeddings | n/a |

- **Serving:** vLLM/TGI for open-weight; gateway abstracts both open and managed providers behind one OpenAI-compatible interface.
- **Fallbacks:** on guardrail failure, eval-gate failure, low confidence, or provider outage → deterministic fallback or human escalation. **Never a silent best-guess** on money/legal/irreversible paths.
- **Cost/latency budgets** per profile; exceeding budget trips a circuit breaker (`10`).

## 2. Tool Registry (governed capabilities)

- Every tool registered with: JSON-schema signature, permission scope (data classes it touches), side-effect class (read / write / money / PII / irreversible), and required authority level.
- **Unregistered tools are uncallable.** Registering a money/PII/irreversible-scoped tool needs human approval (`06` AM via Security/AI-Platform).
- The gateway injects only the tools an agent's principal is authorized for; sensitive tools fail closed under untrusted-input flows (`10`).

## 3. Agent runtime & orchestration

- **Orchestration:** LangGraph (stateful graphs) for agent control flow; **Temporal** for durable, long-running, approval-bearing workflows (the two compose: LangGraph for reasoning steps, Temporal for durable saga + approvals).
- **Agent loop:** perceive (events/inputs) → retrieve (grounded context) → reason (LLM via gateway) → propose action → guardrail + authZ → execute (deterministic tool or sub-workflow) → audit → learn.
- **Memory:**
  - *Working memory* (per task, ephemeral).
  - *Episodic memory* (decisions/outcomes; feeds learning loop) — provenance-tagged.
  - *Semantic/long-term* via Knowledge Management + vector store (approved, provenance-bearing only).
  - PII in memory is classified + access-scoped + erasable (DSAR reaches memory stores).

## 4. RAG grounding (anti-hallucination)

- Customer-facing and decision-grounding generations must be **grounded in approved KnowledgeArtifacts** (`03` Knowledge) with citations.
- Retrieval returns provenance; if no sufficiently-relevant approved source → **escalate / abstain**, never fabricate.
- Grounding metric tracked per task profile; below threshold blocks the profile from customer-facing use.

## 5. Evals & quality gates (LLMOps)

- **Eval sets** per task profile: capability (task accuracy), safety (jailbreak/prompt-injection resistance), grounding (citation faithfulness), fairness/bias (for significant-decision profiles), and regression.
- **Promotion gate:** a model/prompt version reaches production only if it passes the eval thresholds; failures emit `ModelEvaluationFailed` and block (`ModelPromoted` only on pass).
- Tools: MLflow (registry/experiments), Evidently (drift), custom eval harness, Langfuse (LLM traces + scores).

## 6. Tracing & observability

- Every agent invocation is **traced** (OpenTelemetry + Langfuse): inputs (PII-redacted), retrieved context + provenance, model + params, tool calls, guardrail results, output, cost, latency.
- Drift detection on quality/grounding/cost; alerts to Model-Ops Agent.
- Traces are retention-bound + PII-redacted at ingestion (`08`).

## 7. Model risk controls

- **Model cards** (intended use, limits, eval results, training-data provenance for open weights) in the registry — evidence for Compliance.
- Bias/fairness monitoring for significant-automated-decision profiles (`09`).
- Hallucination controls: grounding gate + abstention + deterministic fallback.
- Provider diversity: at least one open-weight + one managed option per critical profile to avoid lock-in (`12` exit paths).

## Determinism boundary (non-negotiable)

| LLMs MAY | Deterministic systems MUST |
|---|---|
| reason, draft, summarize, classify, retrieve, recommend | calculations, ledger changes, permissions, policy enforcement, contractual gates, money movement |

The gateway, tool registry, and authority matrix jointly enforce this: a profile like `deterministic_finance_workflow` is **not an LLM** — it is a coded workflow the gateway routes to when financial math is required.
