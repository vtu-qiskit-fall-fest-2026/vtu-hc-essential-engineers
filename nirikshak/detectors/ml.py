"""Simulation-trained ML detectors (Random Forest, XGBoost) on per-block features.

The alarm threshold on the model's attack probability is set on held-out simulated honest blocks
so the false-alarm rate is alpha in simulation. The stress test then asks whether that budget
and the detection rate survive shifted noise and real hardware.

relative=True subtracts each session's reference-block mean from every feature, giving the
model Nirikshak's reference rounds as context.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

FEATURES = ["qber", "qber_z", "qber_x", "basis_asymmetry", "err_z_sent0", "err_z_sent1"]


def add_reference_features(table: pd.DataFrame, session_col: str = "session_id") -> pd.DataFrame:
    """Adds <feature>_rel = feature - mean of that session's reference blocks."""
    out = table.copy()
    ref_means = out[out["kind"] == "ref"].groupby(session_col)[FEATURES].mean()
    for f in FEATURES:
        out[f + "_rel"] = out[f] - out[session_col].map(ref_means[f])
    return out


def _make_model(kind: str, seed: int):
    if kind == "rf":
        from sklearn.ensemble import RandomForestClassifier
        return RandomForestClassifier(n_estimators=300, min_samples_leaf=3, n_jobs=-1, random_state=seed)
    if kind == "xgb":
        from xgboost import XGBClassifier
        return XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.9,
                             eval_metric="logloss", random_state=seed, n_jobs=4)
    raise ValueError(kind)


class SimTrainedClassifier:
    def __init__(self, kind: str = "rf", alpha: float = 0.05, relative: bool = False, seed: int = 0):
        self.kind, self.alpha, self.relative, self.seed = kind, alpha, relative, seed
        self.cols = [f + "_rel" for f in FEATURES] if relative else list(FEATURES)

    def _X(self, table: pd.DataFrame) -> np.ndarray:
        t = add_reference_features(table) if self.relative else table
        key = t[t["kind"] == "key"]
        X = key[self.cols].copy()
        # Small blocks can lack Z-basis rounds with a given sent bit; fall back to the block QBER.
        fallback = key["qber_rel" if self.relative else "qber"]
        for c in X.columns:
            X[c] = X[c].fillna(fallback)
        return X.to_numpy(dtype=float)

    def fit(self, train: pd.DataFrame, holdout_fraction: float = 0.3) -> "SimTrainedClassifier":
        """Fit on a random 70% of sessions; set the alarm threshold on the other 30%'s honest blocks."""
        rng = np.random.default_rng(self.seed)
        sessions = train["session_id"].unique()
        hold = set(rng.choice(sessions, size=int(len(sessions) * holdout_fraction), replace=False))
        fit_t = train[~train["session_id"].isin(hold)]
        hold_t = train[train["session_id"].isin(hold)]
        y = fit_t.loc[fit_t["kind"] == "key", "is_attack"].to_numpy(dtype=int)
        self.model_ = _make_model(self.kind, self.seed).fit(self._X(fit_t), y)
        hk = hold_t[hold_t["kind"] == "key"]
        honest_p = self.model_.predict_proba(self._X(hold_t))[:, 1][~hk["is_attack"].to_numpy(dtype=bool)]
        n = len(honest_p)
        k = int(np.ceil((n + 1) * (1 - self.alpha)))
        self.threshold_ = float(np.sort(honest_p)[min(k, n) - 1])
        return self

    def predict(self, table: pd.DataFrame) -> np.ndarray:
        """Alarms for the key rows of `table`, in table order."""
        return self.model_.predict_proba(self._X(table))[:, 1] > self.threshold_
