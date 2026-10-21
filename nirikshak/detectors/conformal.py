"""Split-conformal alarm threshold with a stated false-alarm rate.

Fit on anomaly scores from honest (no-attack) calibration blocks. If future honest
blocks are exchangeable with the calibration blocks, P(false alarm) <= alpha.
Drift breaks exchangeability, which is why Nirikshak recalibrates on interleaved
honest reference rounds rather than on a one-off simulator calibration.
"""

from __future__ import annotations

import numpy as np


class ConformalThreshold:
    def __init__(self, alpha: float = 0.05):
        if not 0 < alpha < 1:
            raise ValueError("alpha must be in (0, 1)")
        self.alpha = alpha
        self.threshold_: float | None = None

    def fit(self, honest_scores: np.ndarray) -> "ConformalThreshold":
        s = np.sort(np.asarray(honest_scores, dtype=float))
        n = len(s)
        k = int(np.ceil((n + 1) * (1 - self.alpha)))
        if k > n:
            raise ValueError(f"need at least {int(np.ceil(1 / self.alpha)) - 1} calibration blocks for alpha={self.alpha}")
        self.threshold_ = float(s[k - 1])
        return self

    def predict(self, scores: np.ndarray) -> np.ndarray:
        if self.threshold_ is None:
            raise RuntimeError("call fit() first")
        return np.asarray(scores) > self.threshold_
