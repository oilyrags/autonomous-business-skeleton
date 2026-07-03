"""BusinessCharter: a per-business design language (tokens → unique daisyUI theme) + a
machine-checkable tech charter, enforced by charter_conformance (PRD 0008 P1a). Pure, infra-free."""

from __future__ import annotations

from ab_product.charter import (
    Artifact,
    BusinessCharter,
    DesignTokens,
    TechCharter,
    charter_conformance,
    is_consistent_extension,
    render_theme,
)

_ALL_RULES = frozenset({"business_id_tenancy", "ports_and_stubs", "single_governed_ingress"})


def _artifact(**over: object) -> Artifact:
    base: dict[str, object] = {
        "theme_name": "rocketco",
        "dependencies": frozenset({"fastapi", "jinja2"}),
        "architecture_rules": _ALL_RULES,
        "charter_version": 1,
    }
    base.update(over)
    return Artifact(**base)  # type: ignore[arg-type]


def _charter(business_id: str, primary: str, *, version: int = 1) -> BusinessCharter:
    return BusinessCharter(
        business_id=business_id,
        version=version,
        tokens=DesignTokens(
            primary=primary,
            secondary="#1f2937",
            accent="#f59e0b",
            neutral="#111827",
            base_100="#0b0c0e",
            radius_rem=0.5,
            font_family="Inter, system-ui, sans-serif",
            density="comfortable",
        ),
        tech=TechCharter(),
    )


def test_render_theme_emits_a_distinct_daisyui_theme_per_business() -> None:
    rocket = render_theme(_charter("rocketco", "#0a84ff"))
    hedgehog = render_theme(_charter("hedgehog", "#e11d48"))

    assert '[data-theme="rocketco"]' in rocket
    assert "--color-primary: #0a84ff" in rocket
    assert '[data-theme="hedgehog"]' in hedgehog
    assert "--color-primary: #e11d48" in hedgehog
    assert rocket != hedgehog  # a distinct design language per business, by construction


def test_conformance_passes_a_conformant_artifact() -> None:
    report = charter_conformance(_artifact(), _charter("rocketco", "#0a84ff"))
    assert report.ok is True and report.violations == ()


def test_conformance_fails_when_the_business_theme_is_not_used() -> None:
    report = charter_conformance(_artifact(theme_name="generic"), _charter("rocketco", "#0a84ff"))
    assert report.ok is False
    assert any("business theme" in v for v in report.violations)


def test_conformance_fails_on_a_forbidden_dependency() -> None:
    art = _artifact(dependencies=frozenset({"fastapi", "requests"}))  # requests not in the charter
    report = charter_conformance(art, _charter("rocketco", "#0a84ff"))
    assert report.ok is False
    assert any("forbidden dependency: requests" in v for v in report.violations)


def test_conformance_fails_on_a_missing_architecture_rule() -> None:
    art = _artifact(architecture_rules=frozenset({"business_id_tenancy"}))  # drops two mandated rules
    report = charter_conformance(art, _charter("rocketco", "#0a84ff"))
    assert report.ok is False
    assert any("ports_and_stubs" in v for v in report.violations)


def test_conformance_fails_on_a_missing_charter_version() -> None:
    report = charter_conformance(_artifact(charter_version=0), _charter("rocketco", "#0a84ff"))
    assert report.ok is False
    assert any("charter-version" in v for v in report.violations)


def test_extend_bumps_the_version_append_only_and_stays_consistent() -> None:
    v1 = _charter("rocketco", "#0a84ff", version=1)
    v2 = v1.extend(add_dependencies=frozenset({"httpx"}), add_rules=frozenset({"audit_every_mutation"}))
    assert v2.version == 2
    assert {"fastapi", "httpx"} <= v2.tech.allowed_dependencies  # grew, kept the originals
    assert "audit_every_mutation" in v2.tech.architecture_rules
    assert v2.tokens == v1.tokens  # the design language is unchanged
    assert is_consistent_extension(v1, v2)


def test_a_recoloured_theme_is_not_a_consistent_extension() -> None:
    v1 = _charter("rocketco", "#0a84ff", version=1)
    recoloured = _charter("rocketco", "#ff0000", version=2)  # changed the primary colour
    assert is_consistent_extension(v1, recoloured) is False  # contradicts the design language
