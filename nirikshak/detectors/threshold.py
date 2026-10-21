"""Baseline: the textbook fixed QBER alarm."""

from __future__ import annotations

import numpy as np


class QBERThreshold:
    def __init__(self, threshold: float = 0.11):
        self.threshold = threshold

    def predict(self, qber: np.ndarray) -> np.ndarray:
        """True = alarm (attack suspected)."""
        return np.asarray(qber) > self.threshold
