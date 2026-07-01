---
status: accepted
---

# ab_social — multichannel content generation & distribution (marketing module)

Adds the marketing domain's social-media capability described in `plan.md` (AetherSocial /
"autonomous social") as a **skeleton-native bounded context**, not the plan's standalone
LangGraph/DSPy/vLLM/ComfyUI/Postiz stack. Designed via `/grill-with-docs`; three decisions were
put to the owner, the rest follow the repo's existing rules (architecture/06 determinism boundary;
gateway cost metering; `ab_growth`/`ab_playbook`).

## Decisions (grilled)

1. **Skeleton-native `ab_social`, ports + stubs.** A new `src/ab_social/` bounded context following
   the model-provider pattern: heavy externals are injected **ports** with **stub adapters** by
   default, real adapters (Postiz, ComfyUI, a content LLM via the gateway, platform analytics) drop
   in behind the same interface. Runs end-to-end in CI on stubs. *Not* the standalone product.
2. **Self-optimization reuses `ab_growth` + `ab_playbook`.** A post variant **is an experiment arm**:
   engagement metrics feed `ab_growth`'s existing scale/pivot/kill decision; winning
   formats/pillars reweight the brand's `SocialProfile` deterministically; `ab_playbook` distils
   cross-brand patterns. **No DSPy** — the LLM only writes copy behind a port.
3. **Publishing is a governed action.** The `Publisher` port is business-scoped, authority-gated via
   `ab_org` (escalates above the agent's level), audited; the `SocialProfile.review_mode`
   (`human_approval_first_n` default / `always` / `never`) implements the plan's "optional human
   review gates". Content-LLM cost is metered to the ledger (existing `within_llm_budget` /
   `{business_id}:llm_spend`); boost spend flows through `ab_ads`.

## Determinism split (from architecture/06, not grilled)

- **Deterministic** (pure cores, like `ab_growth`): the **content plan** (pillar/format/platform/
  timing chosen from the `SocialProfile` + recent performance), the **QA / brand-safety gate**
  (posting-rules + forbidden-terms validation), **variant selection**, the **composite engagement
  KPI score** (from `kpi_weights`, integer basis points), budget/boost decisions, and the
  optimization/reweighting loop.
- **LLM, behind a port** (never a money/identity/access decision): the creative **copy/caption**
  text and the **image prompt** only.
- **Governed**: publishing (outward-facing, irreversible).

## Ports (stub default, real adapter behind the same interface)

- `ContentGenerator` — copy/caption from a plan item (real: content LLM via the gateway).
- `ImagePrompter`/image gen — brand-consistent visual prompt/asset (real: ComfyUI).
- `Publisher` — post/schedule to a platform, returns a platform post id (real: Postiz / native SDKs).
- `MetricsSource` — per-post engagement metrics (real: platform analytics).

## Config & events

- **`SocialProfile`** (per `business_id`): voice, content pillars + weights, platforms + format mix,
  posting rules (min value ratio, forbidden terms, required elements), `kpi_weights`, `review_mode`.
  Its own Pydantic config (social-specific), distinct from `ab_growth.Blueprint` (economics).
- **Events**: `ContentPublished`, `PostMetricsCollected` (business-scoped, financial/internal),
  added to `events.asyncapi.yaml` — the ADR-0037 contract test drives each.

## Shipped

- **Slice 64 (tracer bullet):** `SocialProfile` config (voice, weighted pillars, platforms +
  format mix, posting rules, kpi_weights, review_mode); deterministic `plan(profile, *, count)`
  (largest-remainder pillar allocation, platform cycling, top-share format); `ContentGenerator` port
  + `StubContentGenerator`; `qa(draft, profile)` brand-safety gate (forbidden terms + required
  elements); governed `Publisher` port + `StubPublisher`; `publish_content` (QA-gate → publish →
  `ContentPublished` event). `make social` runs plan → generate → QA → publish for one brand. 7 pure
  tests; AsyncAPI contract green.

- **Slice 65 (metrics + scoring):** `PostMetrics` + `MetricsSource` port + `StubMetricsSource`;
  `composite_score(metrics, kpi_weights) -> int` blends normalized KPIs into one basis-points score;
  `collect_metrics` + `PostMetricsCollected` event. `make social` now scores each published post
  (linkedin 625 bps vs x 200 bps). 4 pure tests; contract green.

- **Slice 66 (self-optimization):** the loop that makes the brand improve — a content variant is an
  `ab_growth` experiment arm (engagements = conversions); `run_optimization` decides scale/pivot/kill
  and `reweight`s the winning pillar in the `SocialProfile` (SCALE ×1.5 / KILL ×0.5), changing future
  plans; `distil_winning_pillars` distils cross-brand leads the ab_playbook way. `make social` runs
  the whole loop (Productivity 665bps beats Insights 200bps → SCALE → weight 0.5→0.75). 3 pure tests.

## Deferred (real adapters — need credentials/infra)

Real Postiz/ComfyUI/content-LLM/analytics adapters; DSPy prompt compilation; video generation;
LangGraph orchestration (the deterministic cores + the existing bus are the skeleton's equivalent).
