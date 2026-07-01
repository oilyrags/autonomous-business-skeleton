"""Deterministic statistics for experiment decisioning — stdlib only, no external deps.

A two-proportion z-test compares a variant's conversion rate against control. We use the
normal approximation (fine for the sample sizes a paid-acquisition test reaches) and the
stdlib error function for the normal CDF, so the p-value is exact and reproducible.
"""

from __future__ import annotations

import math


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def two_proportion_p_value(conv_a: int, n_a: int, conv_b: int, n_b: int) -> float:
    """Two-sided p-value for H0: rate_a == rate_b. Returns 1.0 (no evidence) when a rate is
    undefined (zero exposure) or the pooled variance is degenerate."""
    if n_a <= 0 or n_b <= 0:
        return 1.0
    p_a = conv_a / n_a
    p_b = conv_b / n_b
    pooled = (conv_a + conv_b) / (n_a + n_b)
    se = math.sqrt(pooled * (1.0 - pooled) * (1.0 / n_a + 1.0 / n_b))
    if se == 0.0:
        return 1.0
    z = (p_b - p_a) / se
    return 2.0 * (1.0 - normal_cdf(abs(z)))


def significant(conv_a: int, n_a: int, conv_b: int, n_b: int, *, alpha: float, min_exposure: int) -> bool:
    """Significant only when each arm has enough exposure (so the normal approximation holds)
    AND the two-sided p-value is below alpha — guards against spurious wins on tiny samples."""
    if n_a < min_exposure or n_b < min_exposure:
        return False
    return two_proportion_p_value(conv_a, n_a, conv_b, n_b) < alpha
