"""Asymptotic BB84 secret key rate (Shor-Preskill, one-way error correction + privacy amplification).

r(Q) = 1 - 2 h(Q) secret bits per sifted bit, with h the binary entropy and Q the QBER. Errors are
all attributed to Eve. r reaches zero at Q = 11.0028%, the origin of the "11% rule". Asymptotic:
ignores finite-key effects and error-correction inefficiency, so real rates are lower.
"""

from __future__ import annotations

import numpy as np

SHOR_PRESKILL_QBER = 0.11002786443824933  # root of 1 - 2 h(Q) = 0


def binary_entropy(q):
    q = np.clip(np.asarray(q, dtype=float), 1e-15, 1 - 1e-15)
    return -q * np.log2(q) - (1 - q) * np.log2(1 - q)


def bb84_key_rate(qber):
    """Secret key bits per sifted bit; 0 where no key can be distilled (QBER >= 11%)."""
    return np.maximum(0.0, 1.0 - 2.0 * binary_entropy(qber))
