"""Sim-to-real stress test: detectors trained/calibrated on simulation, tested on shifted and hardware data.

    python scripts/stress_test.py

Inputs: data/sim/train.parquet (training), test sets data/sim/{train_test,drift,kingston}.parquet
and data/hardware/*.parquet. Every detector gets the same false-alarm budget (alpha = 5%), set on
simulated honest data, except Nirikshak, which sets it per session from that session's reference
rounds. Writes results/stress_test.csv and results/stress_test.md.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from nirikshak.detectors import FixedConformal, QBERThreshold, ReferenceConformal
from nirikshak.detectors.ml import SimTrainedClassifier

ROOT = Path(__file__).resolve().parents[1]
SIM, HW, RESULTS = ROOT / "data" / "sim", ROOT / "data" / "hardware", ROOT / "results"
ALPHA = 0.05


def load_test_sets() -> dict[str, pd.DataFrame]:
    sets = {}
    for name, label in (("train_test", "sim: training conditions"), ("drift", "sim: drifted noise"),
                        ("kingston", "sim: Kingston noise snapshot")):
        p = SIM / f"{name}.parquet"
        if p.exists():
            sets[label] = pd.read_parquet(p)
    for p in sorted(HW.glob("*.parquet")):
        df = pd.read_parquet(p)
        timed = "slot_dt" in df and (df["slot_dt"] > 0).all()
        sets[f"hardware: {df['backend_name'].iloc[0]} batch {df['batch'].iloc[0]}"
             f" ({'timing matched' if timed else 'timing NOT matched'})"] = df
    return sets


def condition(row) -> str:
    if row["attack"] == "none":
        return "honest (false alarms)"
    if row["attack"] == "intercept_resend":
        return f"intercept {round(row['attacked_fraction'] * 16)}/16 rounds"
    return "entangling probe (all)"


def main() -> None:
    train = pd.read_parquet(SIM / "train.parquet")
    detectors = {
        "11% rule": None,
        "sim-calibrated threshold": FixedConformal(ALPHA).fit(train[(train.kind == "key") & ~train.is_attack]),
        "Random Forest (sim-trained)": SimTrainedClassifier("rf", ALPHA).fit(train),
        "XGBoost (sim-trained)": SimTrainedClassifier("xgb", ALPHA).fit(train),
        "XGBoost + reference features": SimTrainedClassifier("xgb", ALPHA, relative=True).fit(train),
        "Nirikshak": ReferenceConformal(ALPHA),
    }
    rows = []
    for set_name, table in load_test_sets().items():
        table = table.reset_index(drop=True)
        key = table[table.kind == "key"].copy()
        for det_name, det in detectors.items():
            if det_name == "11% rule":
                alarms = QBERThreshold().predict(key["qber"])
            elif det_name == "Nirikshak":
                alarms = det.predict_table(table)["alarm"].reindex(key.index).to_numpy()
            else:
                alarms = det.predict(table) if isinstance(det, SimTrainedClassifier) else det.predict(key)
            key[det_name] = np.asarray(alarms, dtype=bool)
        key["condition"] = key.apply(condition, axis=1)
        rates = key.groupby("condition")[list(detectors)].mean()
        for cond, r in rates.iterrows():
            rows.append({"test_set": set_name, "condition": cond, **r.to_dict()})
    out = pd.DataFrame(rows)
    RESULTS.mkdir(exist_ok=True)
    out.to_csv(RESULTS / "stress_test.csv", index=False)

    order = ["honest (false alarms)"] + [f"intercept {k}/16 rounds" for k in (1, 2, 4, 8)] + ["entangling probe (all)"]
    lines = [f"# Stress test: alarm rates per condition (alpha = {ALPHA:.0%})", "",
             "Honest rows are false-alarm rates (target <= 5%); other rows are detection rates.",
             "All detectors except Nirikshak were trained or calibrated on `data/sim/train.parquet`.", ""]
    for set_name, g in out.groupby("test_set", sort=False):
        g = g.set_index("condition").reindex([c for c in order if c in set(g.condition)])
        lines += [f"## {set_name}", "", "| Condition | " + " | ".join(detectors) + " |",
                  "| :--- |" + " :-: |" * len(detectors)]
        for cond, r in g.iterrows():
            lines.append(f"| {cond} | " + " | ".join(f"{r[d]:.0%}" for d in detectors) + " |")
        lines.append("")
    (RESULTS / "stress_test.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
