"""Exact (Clopper-Pearson) confidence intervals for reported rates."""

from __future__ import annotations

from scipy.stats import binomtest


def proportion_ci(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    if n == 0:
        return float("nan"), float("nan")
    ci = binomtest(int(k), int(n)).proportion_ci(confidence_level=confidence, method="exact")
    return float(ci.low), float(ci.high)


def fmt_rate(k: int, n: int) -> str:
    """'95% (75-100%)': rate with its exact 95% interval."""
    lo, hi = proportion_ci(k, n)
    return f"{k / n:.0%} ({lo:.0%}-{hi:.0%})" if n else "n/a"
