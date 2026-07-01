"""The content-generation port: the copy/caption writer. The stub is a deterministic on-brand
template (no LLM); a real adapter calls a content LLM through the gateway (governed + cost-metered)
and implements the same ``write`` — the planner and QA gate never change.
"""

from __future__ import annotations

from typing import Protocol

from ab_social.core import ContentPlanItem, Draft
from ab_social.profile import SocialProfile


class ContentGenerator(Protocol):
    """Write a platform-native draft for a plan item, in the brand's voice."""

    def write(self, item: ContentPlanItem, profile: SocialProfile) -> Draft: ...


class StubContentGenerator:
    """Deterministic on-brand draft for tests + the demo. Same item+profile → same draft. Produces
    a CTA/question and hashtags so it satisfies the standard posting rules; a real content-LLM
    adapter (via the gateway) implements the same ``write``."""

    def write(self, item: ContentPlanItem, profile: SocialProfile) -> Draft:
        body = (
            f"{item.key_message}. What's your take? "
            f"Here's a quick, actionable idea for {item.pillar.lower()}."
        )
        hashtags = (f"#{item.pillar.replace(' ', '')}", f"#{item.platform}")
        return Draft(
            business_id=item.business_id,
            platform=item.platform,
            format=item.format,
            pillar=item.pillar,
            body=body,
            hashtags=hashtags,
            has_cta=True,
        )
