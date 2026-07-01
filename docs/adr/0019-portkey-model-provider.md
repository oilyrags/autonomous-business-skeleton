---
status: accepted
---

# Portkey as a model provider — vendor-swappable model selection & use

architecture/11 §1 calls for a gateway that "abstracts both open and managed providers
behind one OpenAI-compatible interface", with routing by **task profile**. Portkey
(portkey.ai) is exactly such an AI gateway (200+ models, OpenAI-compatible, configs for
fallback/load-balancing/retries, cloud or self-hostable OSS). This slice makes the model
gateway able to select and use models through Portkey — without disturbing the offline
default or the eval-gate governance.

## Decisions

- **Provider layer behind `model_gateway`.** Two providers implement the one
  `ab_evals.harness.Model` protocol, so either is eval-gated and served identically:
  `StubModel` (deterministic, offline — the default) and `PortkeyModel`.
- **Selection is a deployment choice**, not a code change: `AB_MODEL_PROVIDER=stub|portkey`
  (`providers.select_model()`). Default `stub`, so CI/tests/`make up` need no keys.
- **Routing by task profile → Portkey config/model** (`model_routes.ROUTES`). A route is a
  Portkey **config** id (which encodes provider/model/fallbacks on Portkey's side — the
  idiomatic mapping) or a direct **model + virtual key**. All env-overridable
  (`AB_PORTKEY_CONFIG_<PROFILE>` / `_MODEL_<PROFILE>` / `_VK_<PROFILE>`).
- **The eval gate still governs.** A Portkey model is just another candidate `Model`; it
  serves a profile only once promoted (ADR-0018). Auto-promotion at import is limited to
  offline-evaluable models (the stub); a live provider is promoted by an explicit eval run
  or `AB_EVAL_ON_BOOT=1`. So selecting Portkey **never bypasses governance** — an un-gated
  Portkey profile makes the gateway abstain, and it is never even called on that path.
- **Zero-cost by default.** The `portkey-ai` SDK is an optional `models` dependency group,
  imported lazily; the client is injectable. Nothing needs the package or network unless a
  real Portkey call is made. Kept out of the service images.

## Using it

- **Portkey cloud:** `uv sync --group models`; set `AB_MODEL_PROVIDER=portkey`,
  `AB_PORTKEY_API_KEY=…`, and per-profile `AB_PORTKEY_CONFIG_EXECUTIVE_REASONING=cf-…`
  (or `AB_PORTKEY_VK_…` + `AB_PORTKEY_MODEL_…`).
- **Self-hosted OSS gateway** (open-source-preferred): run `docker run -p 8787:8787
  portkeyai/gateway` and set `AB_PORTKEY_BASE_URL=http://<host>:8787/v1`. Verified: the
  image boots ("Ready for connections") and serves `/v1/chat/completions` (a keyless
  request is rejected with `x-portkey-provider header is required` — i.e. the router is
  live). Provider keys are supplied per-request via the virtual key / provider headers.

## Verified

- Infra-free tests (+6, injected fake client → no network): `PortkeyModel` routes a task
  profile to its model + params and parses the OpenAI-shaped response; an unrouted profile
  raises; `select_model()` picks stub by default and Portkey when configured; **a Portkey
  model must pass the eval gate** (echo model promoted; a canary-leaking model blocked on
  the critical safety case); and selecting Portkey **un-gated makes the gateway abstain
  without ever calling the model**. Existing gateway/eval tests still green; lint + mypy
  strict clean. Self-hosted OSS gateway image manually confirmed to boot and route.
- **Live end-to-end (real key + model).** Confirmed against a real model: task profile →
  Portkey Model Catalog slug `@…/z-ai/glm-5.2` → OpenRouter → GLM-5.2, then the **eval →
  promotion gate against the live model → PROMOTED (score 1.00)**. Two findings baked in:
  (1) provider credentials must live in the *saved* Portkey integration when a workspace sets
  `block_inline_config` (BYOK-from-client is refused by policy); (2) *reasoning* models return
  empty `content` if `max_tokens` is too small (budget spent "thinking") — routes now default
  `max_tokens=1024` (env `AB_PORTKEY_MAX_TOKENS`).

## Deferred

Persisting promotions from an offline eval run (MLflow/model cards); guardrails/cost-budgets
per route; Portkey observability/tracing wired to Langfuse/OTel.
