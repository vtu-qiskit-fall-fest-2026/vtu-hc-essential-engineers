"""Nirikshak end to end: python -m src.main

1. Live demo on the simulator: an honest session and a session where Eve touches 2 of 16 rounds.
2. Stress test from the committed datasets (results/stress_test.md).
3. Scorecard with session verdicts, key rates and confidence intervals (results/scorecard.md).
4. README figures (results/figures/*.png).
5. JSON for the web frontend (web/src/results/).

    python -m src.main             # steps 1-5, a few minutes, no IBM account needed
    python -m src.main --demo      # step 1 only
    python -m src.main --regenerate  # also regenerate the simulated datasets first (about 25 min)

Hardware batches need an IBM key in .env: python scripts/collect.py --help
"""

from __future__ import annotations

import argparse
import runpy
import sys
import time
from pathlib import Path

import pandas as pd

from nirikshak.detectors import QBERThreshold, ReferenceConformal, SessionTest
from nirikshak.noise import simple_noise
from nirikshak.protocol import bb84_key_rate
from nirikshak.session import SessionSpec, simulate_session
from nirikshak.sim import make_simulator

ROOT = Path(__file__).resolve().parents[1]


def demo() -> None:
    print("== 1. Simulator demo: honest session vs Eve on 2 of 16 rounds (readout error 1.5%)")
    nm = simple_noise(readout=0.015, readout_1to0=0.03)
    table = pd.concat([
        simulate_session(SessionSpec(attack="none", seed=1), backend=make_simulator(nm), session_id="demo:honest"),
        simulate_session(SessionSpec(attack="intercept_resend", fraction=2 / 16, seed=2),
                         backend=make_simulator(nm), session_id="demo:attacked"),
    ], ignore_index=True)
    key = ReferenceConformal(0.05).predict_table(table)
    key["rule"] = QBERThreshold().predict(key["qber"])
    verdict = SessionTest(0.05).predict_table(table).set_index("session_id")
    for sid, g in key.groupby("session_id", sort=False):
        v = verdict.loc[sid]
        print(f"  {sid:14s} key QBER {g.qber.mean():6.2%} | reference {v.ref_mean:6.2%} | key rate "
              f"{float(bb84_key_rate(g.qber.mean())):.2f} | blocks flagged: Nirikshak {g.alarm.mean():4.0%}, "
              f"11% rule {g.rule.mean():4.0%} | session p = {v.p_value:.4f} -> {'ATTACK' if v.alarm else 'clean'}")
    print("  The session verdict is the decision (5% false-alarm budget per session). Block alarms point to\n"
          "  where in the session to look; on honest sessions they average about 5% but vary between sessions.")


def run_script(name: str, *args: str) -> None:
    sys.argv = [name, *args]
    runpy.run_path(str(ROOT / "scripts" / name), run_name="__main__")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--demo", action="store_true", help="simulator demo only")
    ap.add_argument("--regenerate", action="store_true", help="regenerate simulated datasets first")
    args = ap.parse_args()
    t0 = time.time()
    demo()
    if args.demo:
        return
    if args.regenerate:
        print("\n== Regenerating simulated datasets (about 25 min)")
        run_script("make_sim_dataset.py")
        run_script("make_sim_dataset.py", "--regimes", "train", "--seed", "1", "--suffix", "_test")
        run_script("make_sim_dataset.py", "--regimes", "drift", "--seed", "2", "--honest-only", "40", "--suffix", "_honest")
        run_script("make_sim_dataset.py", "--regimes", "train", "--seed", "3", "--honest-only", "40", "--suffix", "_honest")
    print("\n== 2. Stress test (sim-trained detectors vs Nirikshak) -> results/stress_test.md")
    run_script("stress_test.py")
    print("\n== 3. Scorecard (session verdicts, key rates, 95% intervals) -> results/scorecard.md")
    run_script("scorecard.py")
    print("\n== 4. Figures -> results/figures/")
    run_script("figures.py")
    print("\n== 5. Web frontend data -> web/src/results/ (simulator grid: scripts/export_web.py --sim)")
    run_script("export_web.py")
    print(f"\nDone in {time.time() - t0:.0f} s. Web app: cd web && npm install && npm run dev")


if __name__ == "__main__":
    main()
