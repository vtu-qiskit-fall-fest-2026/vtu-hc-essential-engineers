import numpy as np
import pytest
from qiskit_ibm_runtime.fake_provider import FakeKingston

from nirikshak.attacks import EntanglingProbe, InterceptResend
from nirikshak.features import round_features
from nirikshak.hardware.calibration import calibration_snapshot, pick_layout
from nirikshak.hardware.runner import compile_template, signal_qubits
from nirikshak.protocol import Rounds, build_template


@pytest.fixture(scope="module")
def backend():
    return FakeKingston()


def _neighbours(backend):
    return {tuple(sorted(e)) for e in backend.coupling_map.get_edges()}


def test_layout_is_spread_and_respects_exclude(backend):
    t = build_template(16, InterceptResend(fraction=0.5))
    first = pick_layout(backend, t)
    layout = pick_layout(backend, t, exclude=first[:3])
    assert len(set(layout)) == 16 and not set(first[:3]) & set(layout)
    edges = _neighbours(backend)
    assert not any(tuple(sorted((a, b))) in edges for a in layout for b in layout if a < b)


def test_ancilla_layout_pairs_are_coupled(backend):
    t = build_template(8, EntanglingProbe())
    layout = pick_layout(backend, t)
    edges = _neighbours(backend)
    assert all(tuple(sorted((layout[i], layout[8 + i]))) in edges for i in range(8))


def test_compiled_circuit_uses_picked_qubits(backend):
    t = build_template(16)
    isa = compile_template(t, backend, seed=1)
    assert signal_qubits(isa, 16) == pick_layout(backend, t)
    snap = calibration_snapshot(backend, signal_qubits(isa, 16))
    assert len(snap["qubits"]) == 16 and "readout_error" in snap["qubits"][0]


def test_round_features_flags_a_bad_qubit():
    rng = np.random.default_rng(0)
    r = Rounds.random(30, 4, rng)
    bob = np.broadcast_to(r.alice_bits[:, None, :], (30, 50, 4)).copy()
    bob[..., 2] = rng.integers(0, 2, size=(30, 50))  # round 2 is pure noise
    df = round_features(r, bob, qubits=[10, 11, 12, 13])
    assert df.loc[[0, 1, 3], "qber"].eq(0).all()
    assert df.loc[2, "qber"] == pytest.approx(0.5, abs=0.05)
    assert df["qubit"].tolist() == [10, 11, 12, 13]
