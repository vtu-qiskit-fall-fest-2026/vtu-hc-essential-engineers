"""Collect one hardware batch: honest, intercept-resend and entangling-probe sessions in one job.

    python scripts/collect.py --batch 1                  # plan only: compiles against the live backend, free
    python scripts/collect.py --batch 1 --submit         # submit (uses quantum time), returns immediately
    python scripts/collect.py --fetch <job_id>           # download results when the job is done
    python scripts/collect.py --batch 0 --fake --small   # full flow locally on FakeKingston noise, free

Each teammate uses a different --batch number (it sets the random seeds) and their own .env key.
Files: data/raw/<job_id>.json + _rounds.npz (metadata, git-ignored), data/hardware/<job_id>.parquet
(block table, the dataset), data/raw/<job_id>_bits.npz (raw bits, git-ignored).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

from nirikshak.conditions import standard_conditions
from nirikshak.hardware.batch import compile_sessions, decode, rounds_arrays, sessions_from_json, specs_to_json
from nirikshak.hardware.calibration import calibration_snapshot
from nirikshak.session import build_session

ROOT = Path(__file__).resolve().parents[1]
RAW, HW = ROOT / "data" / "raw", ROOT / "data" / "hardware"


def estimate_seconds(n_exec: int) -> float:
    return 2 + 0.00035 * n_exec  # IBM's quick estimate (no error mitigation, default rep_delay)


def plan(args):
    small = dict(key_blocks=20, ref_blocks=20, block_size=2, shots=4) if args.small else {}
    specs = standard_conditions(seed0=args.batch * 1000, honest_repeats=args.honest_repeats, **small)
    sessions = [build_session(s) for s in specs]
    if args.fake:
        from qiskit_ibm_runtime.fake_provider import FakeKingston
        backend, service = FakeKingston(), None
    else:
        from nirikshak.hardware import DEFAULT_BACKEND, get_service
        service = get_service()
        backend = service.backend(DEFAULT_BACKEND)
    pubs, layouts, slot_dt = compile_sessions(sessions, backend, exclude=args.exclude, seed=args.batch,
                                              timing=args.timing)
    shots = {s.spec.shots for s in sessions}
    assert len(shots) == 1, "all sessions in a job must use the same shots"
    n_exec = sum(s.spec.executions for s in sessions)
    print(f"backend {backend.name} | {len(sessions)} sessions, {len(pubs)} PUBs | {n_exec} executions "
          f"| IBM quick estimate {estimate_seconds(n_exec):.1f} s | slot {slot_dt} dt ({slot_dt * backend.target.dt * 1e6:.2f} us)")
    for s, lay in zip(sessions, layouts):
        print(f"  seed {s.spec.seed:6d}  {s.spec.attack:17s} fraction {s.attacked_fraction:.4f}  qubits {lay}")
    return sessions, pubs, layouts, backend, service, shots.pop(), n_exec, slot_dt


def submit(args):
    sessions, pubs, layouts, backend, service, shots, n_exec, slot_dt = plan(args)
    est = estimate_seconds(n_exec)
    if service is not None:
        remaining = service.usage().get("usage_remaining_seconds")
        print(f"quantum time remaining on this account: {remaining} s")
        if remaining is not None and est > remaining:
            sys.exit("estimate exceeds remaining quantum time; not submitting")
        if est > args.max_seconds:
            sys.exit(f"estimate {est:.1f} s exceeds --max-seconds {args.max_seconds}; not submitting")
        if pubs and backend.status().pending_jobs is not None:
            print(f"pending jobs on {backend.name}: {backend.status().pending_jobs}")
    if not args.submit and not args.fake:
        print("plan only. Add --submit to run on hardware.")
        return

    from qiskit_ibm_runtime import SamplerV2
    mode = backend
    if args.fake:  # same ISA circuits, but MPS: Aer's automatic method is slow on 32 spread-out qubits
        from qiskit_aer import AerSimulator
        mode = AerSimulator.from_backend(backend, method="matrix_product_state")
    job = SamplerV2(mode=mode).run(pubs, shots=shots)
    job_id = job.job_id()
    meta = {"job_id": job_id, "backend": backend.name, "batch": args.batch, "fake": args.fake,
            "submitted": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "shots": shots, "executions": n_exec,
            "estimate_seconds": est, "exclude": args.exclude, "layouts": layouts, "slot_dt": slot_dt, "timing": args.timing,
            "specs": specs_to_json(sessions),
            "calibration_at_submit": calibration_snapshot(backend, sorted({q for l in layouts for q in l}))}
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"{job_id}.json").write_text(json.dumps(meta, indent=2))
    np.savez_compressed(RAW / f"{job_id}_rounds.npz", **rounds_arrays(sessions))
    print(f"submitted job {job_id}; metadata saved to {RAW / (job_id + '.json')}")
    if args.fake:  # local job: results are ready, decode now
        save_results(meta, sessions, job.result(), usage=None, backend=backend)
    else:
        print(f"fetch later with: python scripts/collect.py --fetch {job_id}")


def save_results(meta, sessions, result, usage, backend):
    regime = "fake_kingston" if meta.get("fake") else "hardware"
    table, bits = decode(sessions, result, meta["layouts"], job_id=meta["job_id"], batch=meta["batch"],
                         backend_name=meta["backend"], regime=regime, submitted=meta["submitted"],
                         slot_dt=meta.get("slot_dt", 0),
                         timing=meta.get("timing", "delay" if meta.get("slot_dt") else "none"))
    out_dir = RAW if meta.get("fake") else HW
    out_dir.mkdir(parents=True, exist_ok=True)
    table.to_parquet(out_dir / f"{meta['job_id']}.parquet", index=False)
    np.savez_compressed(RAW / f"{meta['job_id']}_bits.npz", **bits)
    meta["usage_seconds"] = usage
    if not meta.get("fake"):
        qubits = sorted({q for l in meta["layouts"] for q in l})
        meta["calibration_after"] = calibration_snapshot(backend, qubits, refresh=True)
    (RAW / f"{meta['job_id']}.json").write_text(json.dumps(meta, indent=2))
    summary = table[table.kind == "key"].groupby(["attack", "attacked_fraction", "strength"]).qber.mean()
    ref = table[table.kind == "ref"].qber.mean()
    print(f"saved {len(table)} blocks to {out_dir / (meta['job_id'] + '.parquet')} | usage {usage} s")
    print(f"reference QBER {ref:.4f}; key QBER by condition:\n{summary.round(4).to_string()}")


def fetch(job_id: str):
    meta = json.loads((RAW / f"{job_id}.json").read_text())
    sessions = sessions_from_json(meta["specs"])
    saved = np.load(RAW / f"{job_id}_rounds.npz")
    for k, v in rounds_arrays(sessions).items():
        if not np.array_equal(saved[k], v):
            sys.exit(f"regenerated random choices differ from saved ones ({k}); refusing to decode")
    from nirikshak.hardware import get_service
    service = get_service()
    job = service.job(job_id)
    status = job.status()
    print(f"job {job_id}: {status}")
    if str(status).upper() not in ("DONE", "JOBSTATUS.DONE"):
        return
    save_results(meta, sessions, job.result(), usage=job.usage(), backend=service.backend(meta["backend"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=1, help="batch number; sets the random seeds")
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--fetch", metavar="JOB_ID")
    ap.add_argument("--fake", action="store_true", help="run locally on FakeKingston (free)")
    ap.add_argument("--small", action="store_true", help="tiny sessions (for testing)")
    ap.add_argument("--honest-repeats", type=int, default=3)
    ap.add_argument("--exclude", type=int, nargs="*", default=[], help="physical qubits to avoid")
    ap.add_argument("--timing", choices=["echo", "delay", "none"], default="echo",
                    help="echo (default): matched slot with spin echo; delay: batch 2; none: batch 1")
    ap.add_argument("--max-seconds", type=float, default=60, help="refuse to submit above this estimate")
    args = ap.parse_args()
    if args.fetch:
        fetch(args.fetch)
    else:
        submit(args)


if __name__ == "__main__":
    main()
