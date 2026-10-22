"""Session verdict: is this session's key noisier than its own honest reference?

One-sided permutation test on mean block QBER, key blocks vs reference blocks of the same session.
Under no attack the key and reference blocks are exchangeable (same qubits, same job, same timing),
so P(false alarm) <= alpha exactly for every session, whatever the device noise. Pooling all of a
session's blocks makes it far more sensitive than flagging blocks one by one.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def permutation_pvalue(key: np.ndarray, ref: np.ndarray, n_perm: int = 9999, seed: int = 0) -> float:
    key, ref = np.asarray(key, float), np.asarray(ref, float)
    pooled = np.concatenate([key, ref])
    obs = key.mean() - ref.mean()
    rng = np.random.default_rng(seed)
    perms = rng.permuted(np.tile(pooled, (n_perm, 1)), axis=1)
    stats = perms[:, :len(key)].mean(axis=1) - perms[:, len(key):].mean(axis=1)
    return float((1 + np.sum(stats >= obs - 1e-12)) / (n_perm + 1))


class SessionTest:
    def __init__(self, alpha: float = 0.05, score: str = "qber", n_perm: int = 9999, seed: int = 0):
        self.alpha, self.score, self.n_perm, self.seed = alpha, score, n_perm, seed

    def predict_table(self, table: pd.DataFrame, session_col: str = "session_id") -> pd.DataFrame:
        """One row per session: means, p-value, alarm, plus the session's labels."""
        rows = []
        for sid, g in table.groupby(session_col, sort=False):
            key = g.loc[g["kind"] == "key", self.score].dropna().to_numpy()
            ref = g.loc[g["kind"] == "ref", self.score].dropna().to_numpy()
            p = permutation_pvalue(key, ref, self.n_perm, self.seed)
            first = g.iloc[0]
            rows.append({session_col: sid, "attack": first["attack"], "attacked_fraction": first["attacked_fraction"],
                         "strength": first["strength"], "is_attack": bool(g.loc[g["kind"] == "key", "is_attack"].any()),
                         "key_mean": key.mean(), "ref_mean": ref.mean(), "p_value": p, "alarm": p < self.alpha})
        return pd.DataFrame(rows)
