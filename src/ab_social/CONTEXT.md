# Marketing & Social

Multichannel content generation & distribution: plan on-brand posts, generate copy (LLM behind a port), QA-gate them, publish (governed), measure, and self-optimise.

## Language

**SocialProfile**:
A business's social config (voice, weighted pillars, platforms + format mix, posting rules, KPI weights, review mode), scoped by business_id.
_Avoid_: brand_config, brand (a Brand is the identity; this is its social operating config)

**Content Pillar**:
A weighted theme a brand posts under; the planner draws format/platform choices against its weight.
_Avoid_: topic, category, theme (when you mean the weighted planning unit)

**Content Plan Item**:
A deterministic decision to post — pillar, platform, format, timing — produced before any copy is written.
_Avoid_: idea, draft, task

**Composite Engagement Score**:
A post's single deterministic score: a weighted blend of normalized KPIs (per `kpi_weights`), in basis points.
_Avoid_: engagement, performance (too vague), ER (too narrow)

**Review Mode**:
Whether a publish needs human approval: `human_approval_first_n`, `always`, or `never`.
_Avoid_: approval flag, moderation

**Publisher (port)**:
The seam that posts/schedules content to a platform and returns a platform post id; a publish is a governed action.
_Avoid_: poster, distributor
