"""Generate the simulated BB84 block dataset (key + reference blocks per session).

    python scripts/make_sim_dataset.py                       # all regimes
    python scripts/make_sim_dataset.py --regimes train drift  # skip the slow FakeKingston regime
    python scripts/make_sim_dataset.py --regimes train --seed 1 --suffix _test   # independent test set

Regimes (one noise draw per session; the device "drifts" between sessions):
    train     readout 1-2%, symmetric, low gate noise: the clean world detectors are trained in
    drift     readout 1-6%, 1->0 twice as likely as 0->1, more gate noise: shifted conditions
    kingston  IBM Kingston noise snapshot (FakeKingston) on qubits 0..n-1, slow

Writes data/sim/<regime>.parquet (git-ignored; regenerate with this script).
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

from nirikshak.conditions import standard_conditions
from nirikshak.noise import simple_noise
from nirikshak.session import simulate_session
from nirikshak.sim import make_simulator

OUT = Path(__file__).resolve().parents[1] / "data" / "sim"
REPEATS = {"train": 10, "drift": 5, "kingston": 2}


def backend_for(regime: str, rng: np.random.Generator):
    # No fixed simulator seed: a fixed seed correlates noise across PUBs in one Sampler call.
    if regime == "train":
        ro = rng.uniform(0.01, 0.02)
        return make_simulator(simple_noise(p1=0.001, readout=ro)), {"readout": ro, "readout_1to0": ro, "p1": 0.001}
    if regime == "drift":
        ro, p1 = rng.uniform(0.01, 0.06), rng.uniform(0.001, 0.005)
        return make_simulator(simple_noise(p1=p1, readout=ro, readout_1to0=2 * ro)), {"readout": ro, "readout_1to0": 2 * ro, "p1": p1}
    if regime == "kingston":
        from qiskit_aer import AerSimulator
        from qiskit_ibm_runtime.fake_provider import FakeKingston
        return AerSimulator.from_backend(FakeKingston(), method="matrix_product_state"), {}
    raise ValueError(regime)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--regimes", nargs="*", default=list(REPEATS), choices=list(REPEATS))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--suffix", default="", help="output name suffix, e.g. _test -> train_test.parquet")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    for regime in args.regimes:
        r_idx = list(REPEATS).index(regime)  # stable seeds whichever regimes are selected
        rng = np.random.default_rng([args.seed, r_idx])
        tables, t0 = [], time.time()
        for rep in range(REPEATS[regime]):
            seed0 = args.seed * 1_000_000 + r_idx * 10_000 + rep * 100
            for spec in standard_conditions(seed0=seed0):
                backend, noise = backend_for(regime, rng)
                tables.append(simulate_session(spec, backend=backend, session_id=f"{regime}{args.suffix}:{spec.seed}",
                                               regime=regime, backend_name=backend.name, **noise))
            print(f"{regime}: repeat {rep + 1}/{REPEATS[regime]} done, {time.time() - t0:.0f}s", flush=True)
        df = pd.concat(tables, ignore_index=True)
        df.to_parquet(OUT / f"{regime}{args.suffix}.parquet", index=False)
        print(f"{regime}: {df.session_id.nunique()} sessions, {len(df)} blocks -> {OUT / f'{regime}{args.suffix}.parquet'}", flush=True)


if __name__ == "__main__":
    main()
