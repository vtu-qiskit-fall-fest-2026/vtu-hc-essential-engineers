import numpy as np
import pandas as pd
import pytest

from nirikshak.conditions import standard_conditions
from nirikshak.detectors import FixedConformal, ReferenceConformal
from nirikshak.session import SessionSpec, build_session, simulate_session
from nirikshak.sim import make_simulator

SMALL = dict(key_blocks=4, ref_blocks=4, block_size=4, shots=8)


def test_noiseless_session_reference_is_clean_and_attack_shows_in_key_only():
    df = simulate_session(SessionSpec(attack="intercept_resend", fraction=1.0, **SMALL),
                          backend=make_simulator(), session_id="s")
    ref, key = df[df.kind == "ref"], df[df.kind == "key"]
    assert len(ref) == 4 and len(key) == 4
    assert (ref.qber == 0).all() and not ref.is_attack.any()
    assert key.is_attack.all() and key.qber.mean() == pytest.approx(0.25, abs=0.08)
    assert (df.attacked_fraction == 1.0).all()


def test_session_choices_are_reproducible_from_seed():
    a, b = build_session(SessionSpec(seed=7)), build_session(SessionSpec(seed=7))
    assert np.array_equal(a.key_rounds.alice_bits, b.key_rounds.alice_bits)
    assert np.array_equal(a.ref_rounds.bob_bases, b.ref_rounds.bob_bases)


def test_standard_conditions_have_unique_seeds():
    specs = standard_conditions(seed0=1000)
    assert len({s.seed for s in specs}) == len(specs) == 10
    assert sum(s.attack == "none" for s in specs) == 3


def _synthetic(n_sessions=200, n_blocks=20, shift=0.0, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for s in range(n_sessions):
        level = rng.uniform(0.01, 0.05)  # drift between sessions
        for kind in ("ref", "key"):
            q = rng.normal(level + (shift if kind == "key" else 0), 0.005, n_blocks)
            rows += [{"session_id": s, "kind": kind, "qber": v} for v in q]
    return pd.DataFrame(rows)


def test_reference_conformal_holds_false_alarm_rate_under_drift():
    key = ReferenceConformal(alpha=0.05).predict_table(_synthetic())
    assert key.alarm.mean() <= 0.06


def test_reference_conformal_detects_shift_that_fixed_threshold_misses():
    attacked = _synthetic(shift=0.02, seed=1)
    nk = ReferenceConformal(alpha=0.05).predict_table(attacked).alarm.mean()
    fixed = FixedConformal(alpha=0.05).fit(_synthetic(seed=2).query("kind == 'ref'"))
    fx = fixed.predict(attacked[attacked.kind == "key"]).mean()
    assert nk > 0.9 and nk > fx
