from qiskit_ibm_runtime.fake_provider import FakeKingston

from nirikshak.hardware.batch import compile_sessions, rounds_arrays, sessions_from_json, specs_to_json
from nirikshak.session import SessionSpec, build_session


def test_key_and_reference_share_qubits_and_specs_roundtrip():
    sessions = [build_session(SessionSpec(attack=a, fraction=f, key_blocks=2, ref_blocks=2, block_size=2, seed=i))
                for i, (a, f) in enumerate([("none", 0.0), ("entangling_probe", 0.5)])]
    pubs, layouts = compile_sessions(sessions, FakeKingston(), seed=1)
    assert len(pubs) == 4 and all(len(l) == 16 for l in layouts)
    rebuilt = sessions_from_json(specs_to_json(sessions))
    a, b = rounds_arrays(sessions), rounds_arrays(rebuilt)
    assert a.keys() == b.keys() and all((a[k] == b[k]).all() for k in a)
