import numpy as np
import pandas as pd
import pytest

from nirikshak.detectors import SessionTest
from nirikshak.detectors.session_test import permutation_pvalue
from nirikshak.protocol import SHOR_PRESKILL_QBER, bb84_key_rate
from nirikshak.scorecard.stats import fmt_rate, proportion_ci


def test_key_rate_vanishes_at_eleven_percent():
    assert SHOR_PRESKILL_QBER == pytest.approx(0.110, abs=5e-4)
    assert bb84_key_rate(0.0) == pytest.approx(1.0)
    assert bb84_key_rate(SHOR_PRESKILL_QBER) == pytest.approx(0.0, abs=1e-9)
    assert bb84_key_rate(0.2) == 0.0 and 0 < bb84_key_rate(0.05) < 1


def test_exact_interval_contains_rate():
    lo, hi = proportion_ci(19, 20)
    assert lo < 0.95 < hi and hi <= 1.0
    assert fmt_rate(0, 60).startswith("0% (0%-")


def test_permutation_test_is_calibrated_and_sensitive():
    rng = np.random.default_rng(0)
    null = [permutation_pvalue(rng.normal(0.02, 0.005, 20), rng.normal(0.02, 0.005, 20), n_perm=999, seed=i)
            for i in range(300)]
    assert np.mean(np.array(null) < 0.05) <= 0.08
    assert permutation_pvalue(rng.normal(0.025, 0.005, 20), rng.normal(0.02, 0.005, 20), n_perm=999) < 0.05


def test_session_test_table():
    rows = [{"session_id": "s", "kind": k, "qber": q, "attack": "intercept_resend", "attacked_fraction": 0.0625,
             "strength": 0.0, "is_attack": k == "key"}
            for k, q in [("key", 0.05)] * 20 + [("ref", 0.01)] * 20]
    out = SessionTest(n_perm=999).predict_table(pd.DataFrame(rows))
    assert len(out) == 1 and out.alarm.iloc[0] and out.p_value.iloc[0] < 0.01
