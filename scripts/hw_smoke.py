"""Small hardware smoke test: honest + 50% intercept-resend BB84 in one Sampler job.

    python scripts/hw_smoke.py                 # dry run: same ISA circuits on FakeKingston noise (free)
    python scripts/hw_smoke.py --submit        # real job on IBM hardware (uses quantum time)
    python scripts/hw_smoke.py --exclude 0 9   # also avoid these physical qubits

Qubits are picked from live calibration (spread out, no neighbours), not 0..15.
Results go to data/raw/ (gitignored): <job_id>.json (metadata, layout, calibration snapshot,
per-round table, usage) and <job_id>.npz (bits).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from qiskit_ibm_runtime.fake_provider import FakeKingston

from nirikshak.attacks import InterceptResend
from nirikshak.features import round_features
from nirikshak.hardware.calibration import calibration_snapshot
from nirikshak.hardware.runner import compile_template, signal_qubits, submit
from nirikshak.protocol import Rounds, build_template, qber
from nirikshak.sim import bits_to_array

N_ROUNDS, N_BINDINGS, SHOTS, SEED = 16, 25, 64, 2026
OUT = Path(__file__).resolve().parents[1] / "data" / "raw"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--exclude", type=int, nargs="*", default=[], help="physical qubits to avoid")
    args = ap.parse_args()

    if args.submit:
        from nirikshak.hardware import DEFAULT_BACKEND, get_service
        backend = get_service().backend(DEFAULT_BACKEND)
        print(f"{backend.name}: pending jobs {backend.status().pending_jobs}")
    else:
        backend = FakeKingston()

    rng = np.random.default_rng(SEED)
    cases = {"honest": None, "intercept_resend_50": InterceptResend(fraction=0.5, seed=SEED)}
    pubs, rounds, layouts = [], {}, {}
    for name, attack in cases.items():
        t = build_template(N_ROUNDS, attack)
        rounds[name] = Rounds.random(N_BINDINGS, N_ROUNDS, rng)
        isa = compile_template(t, backend, exclude=args.exclude, seed=SEED)
        layouts[name] = signal_qubits(isa, N_ROUNDS)
        pubs.append((isa, t.parameter_values(rounds[name])))
        print(f"{name:22s} qubits {layouts[name]}")

    used = sorted({q for qs in layouts.values() for q in qs})
    n_exec = len(pubs) * N_BINDINGS * SHOTS
    print(f"executions: {n_exec}, IBM quick estimate: {2 + 0.00035 * n_exec:.1f} s")

    meta = {"backend": backend.name, "hardware": args.submit, "n_rounds": N_ROUNDS,
            "n_bindings": N_BINDINGS, "shots": SHOTS, "seed": SEED, "cases": list(cases),
            "exclude": args.exclude, "layouts": layouts,
            "calibration_at_submit": calibration_snapshot(backend, used)}
    job = submit(pubs, backend, shots=SHOTS)
    meta["job_id"] = job.job_id()
    meta["submitted"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    print("job id:", meta["job_id"])
    path = OUT / f"{meta['job_id']}.json"
    if args.submit:
        OUT.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(meta, indent=2))  # saved before waiting

    result = job.result()
    arrays, per_round = {}, {}
    for (name, r), pub_result in zip(rounds.items(), result):
        bob = bits_to_array(pub_result.data.bob)
        arrays[f"{name}_bob"] = bob
        for field in ("alice_bits", "alice_bases", "bob_bases", "eve_bases"):
            arrays[f"{name}_{field}"] = getattr(r, field)
        q = qber(r, bob)
        meta[f"{name}_qber"] = float(q["qber"])
        print(f"{name:22s} QBER {q['qber']:.4f}  (Z {q['qber_z']:.4f}, X {q['qber_x']:.4f})")
        df = round_features(r, bob, layouts[name])
        per_round[name] = df.to_dict(orient="records")
        if name == "honest":
            print(df[["round", "qubit", "qber", "err_z_sent0", "err_z_sent1"]].round(3).to_string(index=False))
    meta["per_round"] = per_round

    if args.submit:
        meta["usage_seconds"] = job.usage()
        meta["calibration_after"] = calibration_snapshot(backend, used, refresh=True)
        print(f"quantum time used: {meta['usage_seconds']} s")
        path.write_text(json.dumps(meta, indent=2))
        np.savez_compressed(OUT / f"{meta['job_id']}.npz", **arrays)
        print("saved to", OUT)


if __name__ == "__main__":
    main()
