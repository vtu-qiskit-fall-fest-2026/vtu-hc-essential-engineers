"""Export results as JSON for the React frontend (web/src/results/, bundled into the build).

    python scripts/export_web.py           # everything except the simulator grid (seconds)
    python scripts/export_web.py --sim     # also the precomputed simulator grid (a few minutes)

Reads data/hardware, results/ (run scorecard.py, stress_test.py, hardware_lessons.py first) and
runs the monitor demo network. The frontend only reads these files; Python stays the source of truth.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd

from nirikshak.detectors import QBERThreshold, ReferenceConformal, SessionTest
from nirikshak.monitor import NetworkMonitor
from nirikshak.monitor.synthetic import default_scenarios, demo_network, hardware_replay_labels
from nirikshak.protocol import SHOR_PRESKILL_QBER, bb84_key_rate
from nirikshak.scorecard.stats import proportion_ci

ROOT = Path(__file__).resolve().parents[1]
HW, RESULTS = ROOT / "data" / "hardware", ROOT / "results"
OUT = ROOT / "web" / "src" / "results"
ALPHA = 0.05


def label(attack: str, frac: float, strength: float) -> str:
    if attack == "none":
        return "honest"
    rounds = round(frac * 16)
    if attack == "intercept_resend":
        return f"intercept {rounds}/16"
    return f"probe {'π/8' if strength < 0.5 else 'π/4'}, {rounds}/16"


def order_key(lbl: str):
    kind = 0 if lbl == "honest" else 1 if lbl.startswith("intercept") else 2
    nums = [int(m) for m in re.findall(r"(\d+)/16", lbl)]
    return (kind, "π/8" not in lbl, nums[0] if nums else 0)


def clean(obj):
    """JSON-safe: NaN/inf -> None, numpy scalars -> Python, floats rounded."""
    if isinstance(obj, dict):
        return {k: clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        return None if not math.isfinite(obj) else round(float(obj), 6)
    return obj


def write(name: str, data) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(clean(data), separators=(",", ":"), ensure_ascii=False))
    print(f"wrote {name} ({(OUT / name).stat().st_size / 1024:.0f} KB)")


def rate(k: int, n: int) -> dict:
    lo, hi = proportion_ci(k, n)
    return {"k": k, "n": n, "rate": k / n if n else None, "lo": lo, "hi": hi}


def score_blocks(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    key = ReferenceConformal(ALPHA).predict_table(df)
    key["rule"] = QBERThreshold().predict(key["qber"])
    key["session"] = key["session_id"].str.split(":").str[-1].astype(int)
    key["condition"] = [label(a, f, s) for a, f, s in zip(key.attack, key.attacked_fraction, key.strength)]
    sess = SessionTest(ALPHA).predict_table(df)
    sess["session"] = sess["session_id"].str.split(":").str[-1].astype(int)
    sess["condition"] = [label(a, f, s) for a, f, s in zip(sess.attack, sess.attacked_fraction, sess.strength)]
    return key, sess


def export_hardware() -> None:
    lessons = pd.read_csv(RESULTS / "hardware_lessons.csv")
    batches, pooled_blocks, pooled_sessions = [], [], []
    for p in sorted(HW.glob("*.parquet")):
        df = pd.read_parquet(p)
        key, sess = score_blocks(df)
        ref = df[df["kind"] == "ref"].assign(session=lambda d: d["session_id"].str.split(":").str[-1].astype(int))
        les = lessons[lessons["job_id"] == p.stem].iloc[0].to_dict() if p.stem in set(lessons["job_id"]) else {}
        timing = df["timing"].iloc[0] if "timing" in df else "delay" if "slot_dt" in df and (df["slot_dt"] > 0).all() else "none"
        sessions = []
        for r in sess.sort_values("session").itertuples():
            g = key[key["session"] == r.session].sort_values("block")
            rf = ref[ref["session"] == r.session].sort_values("block")
            sessions.append({
                "session": r.session, "condition": r.condition, "is_attack": r.is_attack,
                "key_qber": r.key_mean, "ref_qber": r.ref_mean, "key_rate": float(bb84_key_rate(r.key_mean)),
                "p_value": r.p_value, "verdict": r.alarm, "threshold": g["threshold"].iloc[0],
                "blocks_flagged": int(g["alarm"].sum()), "blocks_rule": int(g["rule"].sum()), "blocks": len(g),
                "key_blocks": g["qber"].round(5).tolist(), "ref_blocks": rf["qber"].round(5).tolist(),
            })
        batches.append({"job_id": p.stem, "batch": int(df["batch"].iloc[0]), "backend": df["backend_name"].iloc[0],
                        "submitted": les.get("submitted") or df.get("submitted", pd.Series([None])).iloc[0],
                        "timing": timing, "honest_qber": les.get("honest_qber"),
                        "honest_qber_x": les.get("honest_qber_x"), "untouched": [les.get("untouched_min"), les.get("untouched_max")],
                        "touched": [les.get("touched_min"), les.get("touched_max")],
                        "quantum_seconds": les.get("quantum_seconds"), "slot_us": les.get("slot_us"),
                        "sessions": sessions})
        if timing == "echo":
            pooled_blocks.append(key.assign(backend=df["backend_name"].iloc[0]))
            pooled_sessions.append(sess.assign(backend=df["backend_name"].iloc[0]))
    batches.sort(key=lambda b: b["batch"])

    pooled = {}
    if pooled_blocks:
        blocks, sess = pd.concat(pooled_blocks), pd.concat(pooled_sessions)
        for backend in sorted(blocks["backend"].unique()):
            b, s = blocks[blocks.backend == backend], sess[sess.backend == backend]
            rows = []
            for cond, g in sorted(b.groupby("condition"), key=lambda t: order_key(t[0])):
                sg = s[s.condition == cond]
                rows.append({"condition": cond, "is_attack": cond != "honest",
                             "key_qber": [float(sg.key_mean.min()), float(sg.key_mean.max())],
                             "key_rate": [float(bb84_key_rate(sg.key_mean.max())), float(bb84_key_rate(sg.key_mean.min()))],
                             "nirikshak": rate(int(g.alarm.sum()), len(g)), "rule": rate(int(g.rule.sum()), len(g)),
                             "sessions": rate(int(sg.alarm.sum()), len(sg))})
            att, hon = s[s.is_attack], s[~s.is_attack]
            pooled[backend] = {"batches": sorted(b["session_id"].str.split(":").str[0].unique().tolist()),
                               "conditions": rows, "attacked_sessions": rate(int(att.alarm.sum()), len(att)),
                               "honest_sessions": rate(int(hon.alarm.sum()), len(hon)),
                               "max_attacked_p": float(att.p_value.max()) if len(att) else None}

    sim = {}
    sessions_csv = pd.read_csv(RESULTS / "sessions.csv")
    for name in ("sim train_honest", "sim drift_honest"):
        g = sessions_csv[sessions_csv["set"] == name]
        if len(g):
            sim[name.replace("sim ", "")] = rate(int(g.session_alarm.sum()), len(g))
    write("hardware.json", {"alpha": ALPHA, "rule_11": SHOR_PRESKILL_QBER, "batches": batches, "pooled": pooled,
                            "sim_session_false_alarms": sim})


def export_stress() -> None:
    d = pd.read_csv(RESULTS / "stress_test.csv")
    detectors = [c for c in d.columns if c not in ("test_set", "condition")]
    sets = list(dict.fromkeys(d["test_set"]))
    rows = [{"test_set": r["test_set"], "condition": r["condition"], "rates": {k: r[k] for k in detectors}}
            for _, r in d.iterrows()]
    honest = d[d["condition"].str.startswith("honest")].set_index("test_set")[detectors]
    shifted = honest[~honest.index.str.startswith("sim: training")]
    worst = [{"detector": k, "rate": float(shifted[k].max()), "where": shifted[k].idxmax()} for k in detectors]
    write("stress.json", {"alpha": ALPHA, "detectors": detectors, "test_sets": sets, "rows": rows,
                          "worst_false_alarms": worst})


def export_monitor(seed: int = 0) -> None:
    records, links = demo_network(HW, seed=seed)
    mon = NetworkMonitor(alpha=ALPHA)
    for r in records:
        mon.update(r)
    v = mon.verdict_table()
    v["window"] = v.groupby("link_id").cumcount()
    starts = {sc.link_id: sc.attack_start_h for sc in default_scenarios()}
    labels = hardware_replay_labels(HW)
    truth = []
    for link, w in zip(v.link_id, v.window):
        if link in starts:
            truth.append("attacked" if starts[link] is not None and w >= starts[link] else "honest")
        else:
            r = labels.iloc[w]
            truth.append("honest" if r.attack == "none" else label(r.attack, r.attacked_fraction, r.strength))
    v["truth"] = truth
    blocks = pd.DataFrame(mon.blocks)
    t0 = pd.Timestamp(records[0].t)
    blocks["h"] = (pd.to_datetime(blocks["t"]) - t0) / pd.Timedelta(hours=1)
    per_link = {}
    for link, g in blocks.groupby("link_id"):
        per_link[link] = {"h": g["h"].round(4).tolist(), "qber": g["qber"].round(5).tolist(),
                          "threshold": g["threshold"].round(5).tolist(), "alarm": g["alarm"].astype(int).tolist(),
                          "alarm_frozen": g["alarm_frozen"].astype(int).tolist(),
                          "frozen_threshold": mon.links[link].frozen_threshold}
    verdicts = [{"link_id": r.link_id, "window": r.window,
                 "h": (pd.Timestamp(r.t_start) - t0) / pd.Timedelta(hours=1), "start": r.t_start, "end": r.t_end,
                 "key_qber": r.key_qber, "ref_qber": r.ref_qber, "p_value": r.p_value, "alarm": r.alarm,
                 "blocks_flagged": r.blocks_flagged, "blocks_flagged_frozen": r.blocks_flagged_frozen,
                 "blocks_flagged_11": r.blocks_flagged_11, "truth": r.truth} for r in v.itertuples()]
    write("monitor.json", {"alpha": ALPHA, "start": records[0].t, "seed": seed,
                           "links": links.to_dict("records"), "verdicts": verdicts, "blocks": per_link,
                           "telemetry_example": [r.__dict__ for r in records[:4]]})


def export_simulator() -> None:
    from nirikshak.noise import simple_noise
    from nirikshak.session import SessionSpec, simulate_session
    from nirikshak.sim import make_simulator

    grid = []
    readouts = (0.005, 0.015, 0.03, 0.05)
    rounds = (0, 1, 2, 4, 8)
    for i, ro in enumerate(readouts):
        nm = simple_noise(readout=ro, readout_1to0=2 * ro)
        for j, k in enumerate(rounds):
            spec = SessionSpec(attack="intercept_resend" if k else "none", fraction=k / 16, seed=100 * i + j)
            t = simulate_session(spec, backend=make_simulator(nm), session_id="sim:0")
            key, sess = score_blocks(t)
            s = sess.iloc[0]
            ref = t[t["kind"] == "ref"].sort_values("block")
            grid.append({"readout": ro, "rounds": k, "key_qber": s.key_mean, "ref_qber": s.ref_mean,
                         "key_rate": float(bb84_key_rate(s.key_mean)), "p_value": s.p_value, "verdict": s.alarm,
                         "threshold": key["threshold"].iloc[0], "blocks_flagged": int(key.alarm.sum()),
                         "blocks_rule": int(key.rule.sum()), "key_blocks": key.sort_values("block")["qber"].round(5).tolist(),
                         "ref_blocks": ref["qber"].round(5).tolist()})
            print(f"  readout {ro:.1%}, {k}/16 rounds: key {s.key_mean:.2%}, p = {s.p_value:.4f}")
    write("simulator.json", {"alpha": ALPHA, "readouts": readouts, "rounds": rounds, "grid": grid})


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sim", action="store_true", help="also regenerate the simulator grid")
    args = ap.parse_args()
    export_hardware()
    export_stress()
    export_monitor()
    if args.sim:
        export_simulator()


if __name__ == "__main__":
    main()
