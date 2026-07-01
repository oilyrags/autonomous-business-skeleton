"""The two-proportion significance test — deterministic, matches known values."""

from ab_growth.stats import normal_cdf, significant, two_proportion_p_value


def test_normal_cdf_reference_points() -> None:
    assert abs(normal_cdf(0.0) - 0.5) < 1e-9
    assert abs(normal_cdf(1.96) - 0.975) < 1e-3


def test_large_true_effect_is_significant() -> None:
    p = two_proportion_p_value(100, 1000, 150, 1000)  # 10% vs 15%
    assert p < 0.001


def test_small_effect_small_sample_is_not_significant() -> None:
    assert two_proportion_p_value(10, 100, 11, 100) > 0.05


def test_identical_rates_give_no_evidence() -> None:
    assert two_proportion_p_value(50, 500, 50, 500) == 1.0


def test_zero_exposure_is_safe() -> None:
    assert two_proportion_p_value(0, 0, 5, 100) == 1.0


def test_min_exposure_guard_blocks_tiny_sample_wins() -> None:
    # A huge apparent effect on 5 users each must NOT be called significant.
    assert significant(0, 5, 3, 5, alpha=0.05, min_exposure=30) is False
    # Same effect size with adequate exposure can be significant.
    assert significant(100, 1000, 150, 1000, alpha=0.05, min_exposure=1000) is True
