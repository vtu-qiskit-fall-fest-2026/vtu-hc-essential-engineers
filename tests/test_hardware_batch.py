from qiskit_ibm_runtime.fake_provider import FakeKingston

from nirikshak.hardware.batch import compile_sessions, rounds_arrays, sessions_from_json, specs_to_json
from nirikshak.hardware.timing import slot_duration
from nirikshak.session import SessionSpec, build_session


def test_key_and_reference_share_qubits_and_specs_roundtrip():
    sessions = [build_session(SessionSpec(attack=a, fraction=f, key_blocks=2, ref_blocks=2, block_size=2, seed=i))
                for i, (a, f) in enumerate([("none", 0.0), ("entangling_probe", 0.5)])]
    pubs, layouts, slot_dt = compile_sessions(sessions, FakeKingston(), timing="none", seed=1)
    assert len(pubs) == 4 and all(len(l) == 16 for l in layouts) and slot_dt == 0
    rebuilt = sessions_from_json(specs_to_json(sessions))
    a, b = rounds_arrays(sessions), rounds_arrays(rebuilt)
    assert a.keys() == b.keys() and all((a[k] == b[k]).all() for k in a)


def test_timing_match_gives_every_circuit_the_same_slot():
    backend = FakeKingston()
    sessions = [build_session(SessionSpec(attack=a, fraction=f, key_blocks=2, ref_blocks=2, block_size=2, seed=i))
                for i, (a, f) in enumerate([("none", 0.0), ("intercept_resend", 0.25), ("entangling_probe", 0.5)])]
    measure_dt = backend.target["measure"][(0,)].duration / backend.target.dt
    for timing in ("delay", "echo"):
        pubs, _, slot_dt = compile_sessions(sessions, backend, seed=1, timing=timing)
        assert slot_dt > measure_dt  # at least Eve's mid-circuit measurement
        assert {slot_duration(isa, backend) for isa, _ in pubs} == {slot_dt}
        n_x = sum(1 for inst in pubs[1][0].data if inst.operation.name == "x")  # reference circuit
        assert n_x == (32 if timing == "echo" else 0)  # two echo pulses on each of 16 qubits
