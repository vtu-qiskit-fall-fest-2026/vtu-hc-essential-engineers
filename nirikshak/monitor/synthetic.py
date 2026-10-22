"""Synthetic QKD links for the network monitor demo (simulated, not real operator data).

Each block's error count is binomial: sifted ~ Binomial(rounds, 1/2), errors ~ Binomial(sifted, q).
q is the link's noise floor at that time (base + drift), shared by key and reference blocks; on key
blocks an intercept-resend attack on a fraction f of rounds adds what our hardware showed: touched
rounds err at about 25% plus half the noise floor. The hardware-replay link uses real ibm_kingston
blocks instead (see `hardware_replay`).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from nirikshak.monitor.telemetry import BlockRecord, from_session_table

START = "2026-10-22T00:00:00+05:30"


@dataclass(frozen=True)
class LinkScenario:
    link_id: str
    description: str
    base_qber: float = 0.017
    drift: Callable[[float], float] | None = None   # extra QBER as a function of hours since start
    attack_start_h: float | None = None
    attack_fraction: float = 0.0

    def noise(self, h: float) -> float:
        return self.base_qber + (self.drift(h) if self.drift else 0.0)

    def attacked(self, h: float) -> bool:
        return self.attack_start_h is not None and h >= self.attack_start_h


def default_scenarios() -> list[LinkScenario]:
    return [
        LinkScenario("L1", "stable link"),
        LinkScenario("L2", "slow drift, recalibrated at 20:00",
                     drift=lambda h: 0.025 * min(h, 20) / 20 if h < 20 else 0.0),
        LinkScenario("L3", "tapped from 14:00, 1 of 16 rounds", base_qber=0.02, attack_start_h=14, attack_fraction=1 / 16),
        LinkScenario("L4", "daily temperature cycle, tapped from 08:00, 2 of 16 rounds",
                     drift=lambda h: 0.008 * (1 + np.sin(2 * np.pi * (h - 6) / 24)), attack_start_h=8,
                     attack_fraction=2 / 16),
    ]


def synthetic_stream(scenarios: list[LinkScenario], hours: int = 24, window: int = 20, rounds: int = 1024,
                     start: str = START, seed: int = 0) -> list[BlockRecord]:
    """One window per hour per link, `window` reference and `window` key blocks interleaved."""
    rng = np.random.default_rng(seed)
    t0 = pd.Timestamp(start)
    step = pd.Timedelta(hours=1) / (2 * window)
    out = []
    for w in range(hours):
        for i in range(2 * window):
            t = t0 + w * pd.Timedelta(hours=1) + (i + 1) * step
            h = (t - t0) / pd.Timedelta(hours=1)
            kind = "ref" if i % 2 == 0 else "key"
            for sc in scenarios:
                q0 = sc.noise(h)
                q = q0
                if kind == "key" and sc.attacked(h):
                    q = (1 - sc.attack_fraction) * q0 + sc.attack_fraction * (0.25 + 0.5 * q0)
                n = int(rng.binomial(rounds, 0.5))
                out.append(BlockRecord(sc.link_id, t.isoformat(), kind, n, int(rng.binomial(n, q))))
    return out


def hardware_replay(hw_dir: str | Path, link_id: str = "L5", start: str = START) -> list[BlockRecord]:
    """Real ibm_kingston spin-echo sessions, one per hour, in batch and session order."""
    parts = []
    for p in sorted(Path(hw_dir).glob("*.parquet")):
        df = pd.read_parquet(p)
        if "timing" in df and df["timing"].iloc[0] == "echo" and df["backend_name"].iloc[0] == "ibm_kingston":
            parts.append(df)
    if not parts:
        return []
    table = pd.concat(sorted(parts, key=lambda d: d["batch"].iloc[0]), ignore_index=True)
    return from_session_table(table, link_id, start, pd.Timedelta(hours=1))


def hardware_replay_labels(hw_dir: str | Path) -> pd.DataFrame:
    """What actually happened in each replayed window (for scoring the demo)."""
    rows = []
    for p in sorted(Path(hw_dir).glob("*.parquet")):
        df = pd.read_parquet(p)
        if "timing" in df and df["timing"].iloc[0] == "echo" and df["backend_name"].iloc[0] == "ibm_kingston":
            for sid, g in df.groupby("session_id", sort=False):
                rows.append({"batch": g["batch"].iloc[0], "session_id": sid, "attack": g["attack"].iloc[0],
                             "attacked_fraction": g["attacked_fraction"].iloc[0], "strength": g["strength"].iloc[0]})
    return pd.DataFrame(rows).sort_values("batch", kind="stable").reset_index(drop=True)


def demo_network(hw_dir: str | Path | None = None, hours: int = 24, seed: int = 0) -> tuple[list[BlockRecord], pd.DataFrame]:
    """All demo links merged in time order, and a description per link."""
    scenarios = default_scenarios()
    records = synthetic_stream(scenarios, hours=hours, seed=seed)
    links = [{"link_id": s.link_id, "description": s.description, "source": "simulated"} for s in scenarios]
    if hw_dir is not None:
        replay = hardware_replay(hw_dir)
        if replay:
            records += replay
            links.append({"link_id": "L5", "description": "replay of real ibm_kingston sessions, one per hour "
                          "(honest and attacked, attacks run by us)", "source": "IBM hardware"})
    records.sort(key=lambda r: pd.Timestamp(r.t))
    return records, pd.DataFrame(links)
