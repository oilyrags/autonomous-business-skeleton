"""SocialProfile — a business's social configuration (per business_id): voice, weighted content
pillars, platforms + format mix, posting rules, KPI weights, and the human review mode. Distinct
from ``ab_growth.Blueprint`` (economics); this is the marketing operating config the planner and QA
gate read. Pure Pydantic — no I/O.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ReviewMode(StrEnum):
    HUMAN_APPROVAL_FIRST_N = "human_approval_first_n"  # gate the first N posts, then autonomous
    ALWAYS = "always"
    NEVER = "never"


class Pillar(BaseModel):
    name: str
    weight: float = Field(gt=0)


class PlatformConfig(BaseModel):
    name: str
    format_mix: dict[str, float]  # format -> share, e.g. {"carousel": 0.4, "text_post": 0.6}


class PostingRules(BaseModel):
    min_value_ratio: float = Field(default=0.7, ge=0, le=1)
    forbidden: tuple[str, ...] = ()  # terms that fail QA (case-insensitive)
    required_elements: tuple[str, ...] = ()  # e.g. "cta_or_question", "relevant_hashtags_or_keywords"


class SocialProfile(BaseModel):
    business_id: str
    voice: str
    pillars: tuple[Pillar, ...]
    platforms: tuple[PlatformConfig, ...]
    posting_rules: PostingRules = PostingRules()
    kpi_weights: dict[str, float] = Field(default_factory=dict)  # composite score weights
    review_mode: ReviewMode = ReviewMode.HUMAN_APPROVAL_FIRST_N
    review_first_n: int = Field(default=5, ge=0)  # posts gated when review_mode = human_approval_first_n
