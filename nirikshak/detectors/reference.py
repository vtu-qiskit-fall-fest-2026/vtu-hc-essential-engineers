"""Nirikshak detector: per-session conformal threshold from that session's honest reference blocks.

Reference blocks are measured in the same job, on the same qubits, as the key blocks, so under
no attack they are exchangeable with the key blocks even when the device drifts. Split-conformal
calibration on them then bounds the false-alarm rate by alpha in every session, without a
fixed threshold and without trusting a simulator.
"""

from __future__ import annotations

import pandas as pd

from nirikshak.detectors.conformal import ConformalThreshold


class ReferenceConformal:
    def __init__(self, alpha: float = 0.05, score: str = "qber"):
        self.alpha = alpha
        self.score = score

    def predict_table(self, table: pd.DataFrame, session_col: str = "session_id") -> pd.DataFrame:
        """Key-block rows of `table` with `threshold` and `alarm` columns added."""
        out = []
        for _, g in table.groupby(session_col, sort=False):
            ref = g.loc[g["kind"] == "ref", self.score].dropna().to_numpy()
            det = ConformalThreshold(self.alpha).fit(ref)
            key = g[g["kind"] == "key"].copy()
            key["threshold"] = det.threshold_
            key["alarm"] = det.predict(key[self.score].to_numpy())
            out.append(key)
        return pd.concat(out)


class FixedConformal:
    """Baseline: one conformal threshold calibrated once (e.g. on simulator honest data) and
    then applied everywhere. Valid only while new data looks like the calibration data."""

    def __init__(self, alpha: float = 0.05, score: str = "qber"):
        self.alpha = alpha
        self.score = score
        self.threshold_: float | None = None

    def fit(self, honest_table: pd.DataFrame) -> "FixedConformal":
        self.threshold_ = ConformalThreshold(self.alpha).fit(honest_table[self.score].dropna()).threshold_
        return self

    def predict(self, table: pd.DataFrame):
        if self.threshold_ is None:
            raise RuntimeError("call fit() first")
        return table[self.score].to_numpy() > self.threshold_
