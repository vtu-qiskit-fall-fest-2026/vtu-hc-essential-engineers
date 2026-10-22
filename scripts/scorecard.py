"""Scorecard: session verdicts, BB84 key rates and exact 95% confidence intervals.

    python scripts/scorecard.py

Block level: Nirikshak's per-block alarm (per-session conformal threshold) vs the 11% rule.
Session level: one permutation test per session, key blocks vs that session's reference blocks.
Key rate: asymptotic BB84 rate 1 - 2h(QBER) per sifted bit (0 = the protocol would abort).
Intervals are exact (Clopper-Pearson). Block intervals treat blocks as independent; blocks in a
session share a threshold, so their true uncertainty is somewhat larger.
Writes results/scorecard.md and results/sessions.csv.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from nirikshak.detectors import QBERThreshold, ReferenceConformal, SessionTest
from nirikshak.protocol import bb84_key_rate
from nirikshak.scorecard.stats import fmt_rate

ROOT = Path(__file__).resolve().parents[1]
SIM, HW, RESULTS = ROOT / "data" / "sim", ROOT / "data" / "hardware", ROOT / "results"
ALPHA = 0.05
TIMING = {"none": "timing not matched", "delay": "timing matched, plain idle", "echo": "timing matched, spin echo"}


def label(attack: str, frac: float, strength: float) -> str:
    if attack == "none":
        return "honest"
    rounds = round(frac * 16)
    if attack == "intercept_resend":
        return f"intercept {rounds}/16"
    return f"probe {'pi/8' if strength < 0.5 else 'pi/4'}, {rounds}/16"


def order_key(lbl: str):
    kind = 0 if lbl == "honest" else 1 if lbl.startswith("intercept") else 2
    nums = [int(m) for m in re.findall(r"(\d+)/16", lbl)]
    return (kind, "pi/8" not in lbl, nums[0] if nums else 0)


def timing_of(df: pd.DataFrame) -> str:
    if "timing" in df:
        return df["timing"].iloc[0]
    return "delay" if "slot_dt" in df and (df["slot_dt"] > 0).all() else "none"


def md_table(header: list[str], rows: list[list[str]]) -> list[str]:
    return ["| " + " | ".join(header) + " |", "| :--- |" + " :-: |" * (len(header) - 1),
            *["| " + " | ".join(r) + " |" for r in rows], ""]


def main() -> None:
    nk, rule, st = ReferenceConformal(ALPHA), QBERThreshold(), SessionTest(ALPHA)
    lines = ["# Nirikshak scorecard", "",
             f"False-alarm budget alpha = {ALPHA:.0%}. Rates show exact 95% intervals in brackets.",
             "Key rate: asymptotic BB84, secret bits per sifted bit; 0 means the protocol would abort.", ""]
    session_rows = []

    # ---- Hardware, per session
    hw = {p.stem: pd.read_parquet(p) for p in sorted(HW.glob("*.parquet"))}
    echo_blocks = []
    lines += ["## Real hardware, per session", ""]
    for job, df in sorted(hw.items(), key=lambda kv: kv[1]["batch"].iloc[0]):
        timing = timing_of(df)
        key = nk.predict_table(df)
        key["rule"] = rule.predict(key["qber"])
        sess = st.predict_table(df).set_index("session_id")
        rows = []
        for sid, g in key.groupby("session_id", sort=False):
            s = sess.loc[sid]
            lbl = label(s.attack, s.attacked_fraction, s.strength)
            q = g["qber"].mean()
            rate = float(bb84_key_rate(q))
            rows.append((order_key(lbl), [lbl, f"{q:.1%}", f"{s.ref_mean:.1%}", f"{rate:.2f}",
                                          f"{int(g.alarm.sum())}/{len(g)}", f"{int(g.rule.sum())}/{len(g)}",
                                          f"{s.p_value:.4f}", "**attack**" if s.alarm else "clean"]))
            session_rows.append({"set": f"hardware batch {df['batch'].iloc[0]}", "job_id": job, "timing": timing,
                                 "condition": lbl, "key_qber": q, "ref_qber": s.ref_mean, "key_rate": rate,
                                 "nirikshak_blocks": g.alarm.mean(), "rule_11_blocks": g.rule.mean(),
                                 "p_value": s.p_value, "session_alarm": bool(s.alarm), "is_attack": bool(s.is_attack)})
        if timing == "echo":
            key["condition"] = [label(a, f, s) for a, f, s in zip(key.attack, key.attacked_fraction, key.strength)]
            echo_blocks.append(key)
        lines += [f"### `{df['backend_name'].iloc[0]}` batch {df['batch'].iloc[0]} ({TIMING[timing]}, job `{job}`)", ""]
        if timing != "echo":
            lines += ["Not used for claims: " + ("rounds Eve did not touch picked up extra noise."
                      if timing == "none" else "plain idle raised the noise floor (superseded by spin echo)."), ""]
        lines += md_table(["Session", "Key QBER", "Reference QBER", "Key rate", "Nirikshak blocks",
                           "11% rule blocks", "Session p-value", "Session verdict"],
                          [r for _, r in sorted(rows, key=lambda t: t[0])])

    # ---- Hardware, pooled block-level rates (spin-echo batches only), one table per backend
    if echo_blocks:
        all_blocks = pd.concat(echo_blocks)
        all_sess = pd.DataFrame([r for r in session_rows if r["timing"] == "echo"])
        for backend, blocks in all_blocks.groupby("backend_name", sort=True):
            jobs = set(blocks["session_id"].str.split(":").str[0])
            sess_hw = all_sess[all_sess["job_id"].isin(jobs)]
            lines += [f"## Real hardware, `{backend}`, pooled over {len(jobs)} spin-echo batch(es)", ""]
            rows = []
            for lbl, g in sorted(blocks.groupby("condition"), key=lambda t: order_key(t[0])):
                sg = sess_hw[sess_hw.condition == lbl]
                rows.append([lbl, str(len(g)), fmt_rate(int(g.alarm.sum()), len(g)), fmt_rate(int(g.rule.sum()), len(g)),
                             fmt_rate(int(sg.session_alarm.sum()), len(sg))])
            lines += ["Honest row: false alarms. Other rows: detection.", ""]
            lines += md_table(["Condition", "Blocks", "Nirikshak, per block", "11% rule, per block",
                               "Nirikshak, per session"], rows)

    # ---- Simulation, session level
    lines += ["## Simulation, session verdict", "",
              "Honest rows: share of honest sessions wrongly flagged (target 5% or less).", ""]
    for name, title in (("train_test", "training conditions"), ("drift", "drifted noise"),
                        ("kingston", "Kingston noise snapshot"), ("drift_honest", "drifted noise, honest sessions only"),
                        ("train_honest", "training conditions, honest sessions only")):
        p = SIM / f"{name}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        sess = st.predict_table(df)
        sess["condition"] = [label(a, f, s) for a, f, s in zip(sess.attack, sess.attacked_fraction, sess.strength)]
        key = nk.predict_table(df)
        key["condition"] = [label(a, f, s) for a, f, s in zip(key.attack, key.attacked_fraction, key.strength)]
        rows = []
        for lbl, g in sorted(sess.groupby("condition"), key=lambda t: order_key(t[0])):
            kb = key[key.condition == lbl]
            rows.append([lbl, str(len(g)), fmt_rate(int(g.alarm.sum()), len(g)),
                         fmt_rate(int(kb.alarm.sum()), len(kb))])
            for _, s in g.iterrows():
                session_rows.append({"set": f"sim {name}", "condition": lbl, "key_qber": s.key_mean,
                                     "ref_qber": s.ref_mean, "key_rate": float(bb84_key_rate(s.key_mean)),
                                     "p_value": s.p_value, "session_alarm": bool(s.alarm), "is_attack": bool(s.is_attack)})
        lines += [f"### {title}", ""] + md_table(["Condition", "Sessions", "Session verdict", "Per block (Nirikshak)"], rows)

    RESULTS.mkdir(exist_ok=True)
    pd.DataFrame(session_rows).to_csv(RESULTS / "sessions.csv", index=False)
    (RESULTS / "scorecard.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
