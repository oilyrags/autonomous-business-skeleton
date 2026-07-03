"""The BusinessCharter (PRD 0008 P1a): a per-`business_id` design language + tech identity that every
addition to a business must conform to, so a business stays consistent across design, architecture,
and tech — by construction, not convention.

Two pure pieces: `render_theme` turns the design tokens into a **unique daisyUI theme** (CSS custom
properties, vendored, no build step — exactly like the console's `business`/`corporate` themes,
ADR-0056 v0.3); `charter_conformance` fails any addition that doesn't use the business's theme, the
mandated stack + architecture rules, or reference the charter version. Additions **extend** the
charter (a new version, append-only) — they can grow the language, never contradict it.
"""

from __future__ import annotations

import hashlib
import re

from pydantic import BaseModel, Field, field_validator

# The architecture rules the skeleton mandates for every product (baked into a charter's defaults).
_DEFAULT_RULES = frozenset({"business_id_tenancy", "ports_and_stubs", "single_governed_ingress"})
_DEFAULT_DEPS = frozenset({"fastapi", "uvicorn", "jinja2", "pydantic", "psycopg"})

# A token value flows verbatim into the generated theme's CSS. Restrict it to characters valid in a
# CSS colour / font-stack / keyword so it can never carry the `;{}<>"'` metacharacters that would
# break out of the declaration or the surrounding <style> element (defence in depth with the HTML
# escaping the Scaffolder also applies). Allows hex, rgb()/oklch(), named colours, and font stacks.
_CSS_SAFE = re.compile(r"^[A-Za-z0-9 #%.,()-]+$")
# business_id becomes the daisyUI theme-name — a CSS attribute-selector value AND an HTML attribute —
# so it must be a slug (which is exactly what `classify` mints and what the ledger stores).
_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class DesignTokens(BaseModel):
    """The business's visual language: colours (any CSS colour), corner radius, type, density."""

    primary: str
    secondary: str
    accent: str
    neutral: str
    base_100: str  # base background surface
    radius_rem: float = Field(gt=0)
    font_family: str
    density: str = "comfortable"  # comfortable | compact

    @field_validator("primary", "secondary", "accent", "neutral", "base_100", "font_family", "density")
    @classmethod
    def _css_safe(cls, value: str) -> str:
        if not _CSS_SAFE.fullmatch(value):
            raise ValueError(f"token value is not CSS-safe: {value!r}")
        return value


class TechCharter(BaseModel):
    """The mandated stack + architecture rules + allowed dependency set. Append-only across versions."""

    stack: str = "fastapi+daisyui"
    architecture_rules: frozenset[str] = _DEFAULT_RULES
    allowed_dependencies: frozenset[str] = _DEFAULT_DEPS


class BusinessCharter(BaseModel):
    """A versioned, `business_id`-scoped charter. `theme_name` is the daisyUI data-theme id."""

    business_id: str = Field(min_length=1)
    version: int = Field(ge=1)
    tokens: DesignTokens
    tech: TechCharter = TechCharter()

    @field_validator("business_id")
    @classmethod
    def _slug_only(cls, value: str) -> str:
        if not _SLUG.fullmatch(value):
            raise ValueError(f"business_id must be a slug ([a-z0-9-]): {value!r}")
        return value

    @property
    def theme_name(self) -> str:
        return self.business_id

    def extend(
        self, *, add_dependencies: frozenset[str] = frozenset(), add_rules: frozenset[str] = frozenset()
    ) -> BusinessCharter:
        """A new charter version that grows the tech charter (append-only) but keeps the design
        language identical — an addition extends the business, it never contradicts it."""
        return BusinessCharter(
            business_id=self.business_id,
            version=self.version + 1,
            tokens=self.tokens,  # the design language is immutable across versions
            tech=TechCharter(
                stack=self.tech.stack,
                architecture_rules=self.tech.architecture_rules | add_rules,
                allowed_dependencies=self.tech.allowed_dependencies | add_dependencies,
            ),
        )


def is_consistent_extension(old: BusinessCharter, new: BusinessCharter) -> bool:
    """True iff `new` is a valid successor of `old`: same business + unchanged design language, a
    higher version, and a tech charter that only grew (rules/deps are supersets). A recoloured
    theme, a dropped rule, or a removed dependency is a contradiction, not an extension."""
    return (
        new.business_id == old.business_id
        and new.version > old.version
        and new.tokens == old.tokens
        and old.tech.architecture_rules <= new.tech.architecture_rules
        and old.tech.allowed_dependencies <= new.tech.allowed_dependencies
    )


class Artifact(BaseModel):
    """What an addition to a business declares, for the conformance gate: which theme it uses, its
    dependencies, the architecture rules it honours, and the charter version it was built against."""

    theme_name: str
    dependencies: frozenset[str]
    architecture_rules: frozenset[str]
    charter_version: int


class ConformanceReport(BaseModel):
    ok: bool
    violations: tuple[str, ...]


def charter_conformance(artifact: Artifact, charter: BusinessCharter) -> ConformanceReport:
    """Fail any addition that doesn't use the business's theme, stay within the allowed dependency
    set, honour every mandated architecture rule, or reference a valid charter version. Pure."""
    violations: list[str] = []
    if artifact.theme_name != charter.theme_name:
        violations.append(f"does not use the business theme '{charter.theme_name}'")
    for dep in sorted(artifact.dependencies - charter.tech.allowed_dependencies):
        violations.append(f"forbidden dependency: {dep}")
    for rule in sorted(charter.tech.architecture_rules - artifact.architecture_rules):
        violations.append(f"missing architecture rule: {rule}")
    if not 1 <= artifact.charter_version <= charter.version:
        violations.append("missing or invalid charter-version reference")
    return ConformanceReport(ok=not violations, violations=tuple(violations))


def _dark(hex6: str) -> str:
    """Darken a 6-hex colour toward black (halve each channel) so surfaces stay legible under light
    text — used for the neutral/base surfaces, which must be dark whatever the business's hue."""
    r, g, b = (int(hex6[i : i + 2], 16) // 3 for i in (0, 2, 4))
    return f"#{r:02x}{g:02x}{b:02x}"


def default_tokens(business_id: str) -> DesignTokens:
    """Deterministic, per-business design tokens — a distinct primary/secondary/accent and distinct
    (but always dark, for legibility) neutral/base surfaces, all seeded from the id. The default
    design language shared by the Scaffolder and the console's theme preview."""
    h = hashlib.sha256(business_id.encode()).hexdigest()
    return DesignTokens(
        primary=f"#{h[0:6]}",
        secondary=f"#{h[6:12]}",
        accent=f"#{h[12:18]}",
        neutral=_dark(h[18:24]),
        base_100=_dark(h[24:30]),
        radius_rem=0.5,
        font_family="Inter, system-ui, sans-serif",
        density="comfortable",
    )


def render_theme(charter: BusinessCharter) -> str:
    """Deterministically render the charter's tokens as a daisyUI theme block (CSS custom
    properties under `[data-theme="<business_id>"]`). Vendored — no build step."""
    t = charter.tokens
    return (
        f'[data-theme="{charter.theme_name}"] {{\n'
        f"  --color-primary: {t.primary};\n"
        f"  --color-secondary: {t.secondary};\n"
        f"  --color-accent: {t.accent};\n"
        f"  --color-neutral: {t.neutral};\n"
        f"  --color-base-100: {t.base_100};\n"
        f"  --radius-box: {t.radius_rem}rem;\n"
        f"  --radius-field: {t.radius_rem / 2}rem;\n"
        f"  --ab-font-family: {t.font_family};\n"
        f"  --ab-density: {t.density};\n"
        f"}}\n"
    )
