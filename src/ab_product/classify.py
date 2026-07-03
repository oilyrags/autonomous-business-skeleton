"""Classify a promoted initiative: NEW business (mint a business_id) vs EXTENSION of an existing one
(PRD 0008 P1b). Deterministic — the LLM never makes this call."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from ab_schemas.models import ProductInitiative


@dataclass(frozen=True)
class Classification:
    kind: Literal["new", "extension"]
    business_id: str
    rationale: str


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def classify(initiative: ProductInitiative) -> Classification:
    """A new business when the initiative names no existing one (a business_id is minted from the
    title); otherwise an extension of the named business."""
    if initiative.business_id:
        return Classification(
            kind="extension",
            business_id=initiative.business_id,
            rationale=f"extends the existing business '{initiative.business_id}'",
        )
    business_id = _slug(initiative.title)
    return Classification(
        kind="new",
        business_id=business_id,
        rationale=f"no existing business named; mint a new business '{business_id}'",
    )
