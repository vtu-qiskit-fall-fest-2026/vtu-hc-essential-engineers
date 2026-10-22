"""Static README figures from the committed results.

    python scripts/figures.py

Reads results/sessions.csv, results/stress_test.csv and results/hardware_lessons.csv
(run scorecard.py, stress_test.py and hardware_lessons.py first). Writes results/figures/*.png.
"""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUT = RESULTS / "figures"

BLUE, ORANGE, GRAY = "#2a78d6", "#eb6834", "#898781"
INK, MUTED, GRID = "#1f1f1e", "#5f5e5a", "#e4e3df"

plt.rcParams.update({
    "font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": MUTED, "axes.titlecolor": INK,
    "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "xtick.color": MUTED, "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.dpi": 160,
})


def order_key(lbl: str):
    kind = 0 if lbl == "honest" else 1 if lbl.startswith("intercept") else 2
    nums = [int(m) for m in re.findall(r"(\d+)/16", lbl)]
    return (kind, "pi/8" not in lbl, nums[0] if nums else 0)


def pretty(lbl: str) -> str:
    return lbl.replace("pi/", "π/")


def detection() -> None:
    s = pd.read_csv(RESULTS / "sessions.csv")
    s = s[s["set"].str.startswith("hardware") & (s["timing"] == "echo")]
    g = s.groupby("condition")[["nirikshak_blocks", "rule_11_blocks"]].mean()
    g = g.loc[sorted(g.index, key=order_key)[::-1]]
    n_batches = s["job_id"].nunique()

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    y = range(len(g))
    h = 0.36
    ax.barh([i + h / 2 + 0.02 for i in y], g["nirikshak_blocks"], h, color=BLUE, label="Nirikshak")
    ax.barh([i - h / 2 - 0.02 for i in y], g["rule_11_blocks"], h, color=GRAY, label="11% rule")
    for i, (a, b) in enumerate(zip(g["nirikshak_blocks"], g["rule_11_blocks"])):
        ax.text(a + 0.01, i + h / 2 + 0.02, f"{a:.0%}", va="center", fontsize=8, color=INK)
        ax.text(b + 0.01, i - h / 2 - 0.02, f"{b:.0%}", va="center", fontsize=8, color=MUTED)
    ax.set_yticks(list(y), [pretty(c) + (" (false alarms)" if c == "honest" else "") for c in g.index])
    ax.set_xlim(0, 1.1)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1], ["0%", "25%", "50%", "75%", "100%"])
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("share of key blocks flagged")
    ax.set_title(f"Real hardware (ibm_kingston, {n_batches} batches): blocks flagged")
    ax.legend(loc="upper right", frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "detection.png")
    plt.close(fig)


def stress() -> None:
    d = pd.read_csv(RESULTS / "stress_test.csv")
    honest = d[d["condition"].str.startswith("honest")].set_index("test_set").drop(columns="condition")
    shifted = honest[~honest.index.str.startswith("sim: training")]
    worst = shifted.max().sort_values()
    where = shifted.idxmax()

    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    colors = [BLUE if c == "Nirikshak" else GRAY for c in worst.index]
    ax.barh(range(len(worst)), worst.values, 0.6, color=colors)
    for i, (det, v) in enumerate(worst.items()):
        src = re.sub(r"^hardware: \S+ ", "hardware ", where[det].split(" (")[0]).replace("sim: ", "sim, ")
        ax.text(v + 0.01, i, f"{v:.0%}  ({src})", va="center", fontsize=8, color=INK if v > 0 else MUTED)
    ax.axvline(0.05, color=ORANGE, lw=1.5, ls=(0, (4, 3)))
    ax.text(0.058, -0.75, "5% budget", color=MUTED, fontsize=8)
    ax.set_yticks(range(len(worst)), worst.index)
    ax.set_xlim(0, 1.3)
    ax.set_ylim(-0.9, len(worst) - 0.5)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1], ["0%", "25%", "50%", "75%", "100%"])
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("share of honest blocks flagged, worst test set")
    ax.set_title("Worst-case false alarms outside training conditions")
    fig.tight_layout()
    fig.savefig(OUT / "stress_test.png")
    plt.close(fig)


def drift() -> None:
    s = pd.read_csv(RESULTS / "sessions.csv")
    lessons = pd.read_csv(RESULTS / "hardware_lessons.csv")[["job_id", "batch", "backend", "submitted"]]
    s = s[s["set"].str.startswith("hardware") & (s["timing"] == "echo") & (s["condition"] == "honest")]
    s = s.drop(columns="set").merge(lessons, on="job_id")
    jobs = lessons[lessons["job_id"].isin(s["job_id"])].assign(t=lambda d: pd.to_datetime(d["submitted"]))
    jobs = jobs.sort_values("t").reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    kw = dict(s=48, edgecolors="white", linewidths=1.5, zorder=3)
    for i, job in jobs.iterrows():
        b = s[s["job_id"] == job["job_id"]]
        ax.scatter([i - 0.1] * len(b), b["key_qber"], color=BLUE, label="key rounds" if i == 0 else None, **kw)
        ax.scatter([i + 0.1] * len(b), b["ref_qber"], color=ORANGE, label="reference rounds" if i == 0 else None, **kw)
    ax.set_xticks(range(len(jobs)), [f"{j.backend.replace('ibm_', '')} batch {j.batch}\n{j.t:%d %b %H:%M}"
                                     for j in jobs.itertuples()])
    ax.tick_params(axis="x", colors=INK)
    ax.set_xlim(-0.6, len(jobs) - 0.4)
    ax.set_ylim(0, max(0.03, s[["key_qber", "ref_qber"]].max().max() * 1.25))
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=1))
    ax.grid(axis="x", visible=False)
    ax.set_ylabel("QBER, honest sessions")
    ax.set_title("Honest sessions: reference rounds track key rounds over time")
    ax.legend(loc="lower right", frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "drift.png")
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    detection()
    stress()
    drift()
    print(f"wrote {', '.join(p.name for p in sorted(OUT.glob('*.png')))} to {OUT}")


if __name__ == "__main__":
    main()
