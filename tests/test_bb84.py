import numpy as np
import pytest

from nirikshak.attacks import EntanglingProbe, InterceptResend
from nirikshak.features import block_features
from nirikshak.protocol import Rounds, build_template, qber
from nirikshak.sim import make_simulator, run

N_ROUNDS, N_BINDINGS, SHOTS = 16, 40, 64


def _run(attack=None, seed=1):
    rng = np.random.default_rng(seed)
    t = build_template(N_ROUNDS, attack)
    r = Rounds.random(N_BINDINGS, N_ROUNDS, rng)
    out = run(t, r, shots=SHOTS, backend=make_simulator(seed=seed))
    return r, out


def test_no_attack_is_error_free():
    r, out = _run()
    assert out["bob"].shape == (N_BINDINGS, SHOTS, N_ROUNDS)
    assert qber(r, out["bob"])["qber"] == 0.0


def test_full_intercept_resend_gives_quarter_qber():
    r, out = _run(InterceptResend(fraction=1.0))
    q = qber(r, out["bob"])["qber"]
    # Exact conditional expectation for the drawn bases: error prob 1/2 when Eve's basis differs.
    sifted = r.alice_bases == r.bob_bases
    expected = 0.5 * (r.eve_bases != r.alice_bases)[sifted].mean()
    assert q == pytest.approx(expected, abs=0.01)
    assert q == pytest.approx(0.25, abs=0.05)


def test_partial_intercept_stays_under_textbook_alarm():
    r, out = _run(InterceptResend(fraction=0.25))
    q = qber(r, out["bob"])["qber"]
    assert q == pytest.approx(0.0625, abs=0.02)
    assert q < 0.11  # the 11% threshold misses it


def test_entangling_probe_disturbs_less_than_full_intercept():
    r, out = _run(EntanglingProbe(strength=np.pi / 4))
    q = qber(r, out["bob"])["qber"]
    assert 0.0 < q < 0.25


def test_block_features_shape():
    r, out = _run(InterceptResend(fraction=1.0))
    df = block_features(r, out["bob"])
    assert len(df) == N_BINDINGS
    assert {"qber", "qber_z", "qber_x", "basis_asymmetry"} <= set(df.columns)
