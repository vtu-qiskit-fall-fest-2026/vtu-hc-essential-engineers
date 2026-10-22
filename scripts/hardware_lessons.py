"""Per-batch hardware summary from raw bits: honest QBER and rounds Eve did / did not touch.

    python scripts/hardware_lessons.py

Needs data/raw/<job>.json and <job>_bits.npz (git-ignored, on the machine that collected the
batch). Writes results/hardware_lessons.csv (committed), which the dashboard reads.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from nirikshak.hardware.batch import sessions_from_json

ROOT = Path(__file__).resolve().parents[1]
RAW, HW, RESULTS = ROOT / "data" / "raw", ROOT / "data" / "hardware", ROOT / "results"
TIMING = {"none": "not matched", "delay": "matched, plain idle", "echo": "matched, spin echo"}


def rates(session, bob, cols, basis=None):
    r = session.key_rounds
    sift = np.broadcast_to((r.alice_bases == r.bob_bases)[:, None, :], bob.shape)
    if basis is not None:
        sift = sift & np.broadcast_to((r.alice_bases == basis)[:, None, :], bob.shape)
    err = (bob != r.alice_bits[:, None, :]) & sift
    return float(err[..., cols].sum() / sift[..., cols].sum())


def main() -> None:
    rows = []
    for p in sorted(HW.glob("*.parquet")):
        job = p.stem
        meta = json.loads((RAW / f"{job}.json").read_text())
        sessions = sessions_from_json(meta["specs"])
        bits = np.load(RAW / f"{job}_bits.npz")
        timing = meta.get("timing", "delay" if meta.get("slot_dt") else "none")
        honest = [i for i, s in enumerate(sessions) if s.spec.attack == "none"]
        allr = np.arange(sessions[0].spec.n_rounds)
        untouched, touched = [], []
        for i, s in enumerate(sessions):
            if s.spec.attack == "intercept_resend":
                m = s.key.attack.attacked_mask(s.spec.n_rounds)
                untouched.append(rates(s, bits[f"{i}_key_bob"], np.flatnonzero(~m)))
                touched.append(rates(s, bits[f"{i}_key_bob"], np.flatnonzero(m)))
        rows.append({
            "batch": meta["batch"], "job_id": job, "backend": meta["backend"], "submitted": meta.get("submitted"), "timing": TIMING[timing],
            "slot_us": meta.get("slot_dt", 0) * 4e-3,  # dt = 4 ns on Heron backends (ibm_kingston, ibm_fez)
            "quantum_seconds": meta.get("usage_seconds"),
            "honest_qber": np.mean([rates(sessions[i], bits[f"{i}_key_bob"], allr) for i in honest]),
            "honest_qber_x": np.mean([rates(sessions[i], bits[f"{i}_key_bob"], allr, 1) for i in honest]),
            "untouched_min": min(untouched), "untouched_max": max(untouched),
            "touched_min": min(touched), "touched_max": max(touched),
        })
    df = pd.DataFrame(rows).sort_values("batch")
    RESULTS.mkdir(exist_ok=True)
    df.to_csv(RESULTS / "hardware_lessons.csv", index=False)
    print(df.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
