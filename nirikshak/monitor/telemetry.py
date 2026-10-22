"""Vendor-neutral QKD link telemetry: one record per block of rounds.

A record holds only what any BB84 link can export without revealing key material:

    link_id   which link (any string)
    t         when the block finished (ISO 8601)
    kind      "key": sifted rounds of the key exchange (parameter-estimation sample)
              "ref": local reference/test states at the receiver that never cross the channel
    sifted    number of sifted rounds in the block
    errors    how many of them disagreed

Stored as JSON Lines, one record per line, e.g.
    {"link_id": "L3", "t": "2026-10-22T14:05:00+05:30", "kind": "key", "sifted": 512, "errors": 9}
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator

import numpy as np
import pandas as pd

KINDS = ("key", "ref")


@dataclass(frozen=True)
class BlockRecord:
    link_id: str
    t: str
    kind: str
    sifted: int
    errors: int

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError(f"kind must be one of {KINDS}, got {self.kind!r}")
        if self.sifted <= 0 or not 0 <= self.errors <= self.sifted:
            raise ValueError(f"need sifted > 0 and 0 <= errors <= sifted, got {self.sifted}, {self.errors}")

    @property
    def qber(self) -> float:
        return self.errors / self.sifted


def write_jsonl(records: Iterable[BlockRecord], path: str | Path) -> int:
    n = 0
    with open(path, "w") as f:
        for r in records:
            f.write(json.dumps(asdict(r)) + "\n")
            n += 1
    return n


def read_jsonl(path: str | Path) -> Iterator[BlockRecord]:
    with open(path) as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                yield BlockRecord(str(d["link_id"]), str(d["t"]), d["kind"], int(d["sifted"]), int(d["errors"]))


def from_session_table(table: pd.DataFrame, link_id: str, start: str, window: pd.Timedelta,
                       session_col: str = "session_id") -> list[BlockRecord]:
    """Replay a block table (simulated or hardware) as telemetry: one session per time window,
    reference and key blocks interleaved, in the order the sessions appear."""
    out = []
    t0 = pd.Timestamp(start)
    for w, (_, g) in enumerate(table.groupby(session_col, sort=False)):
        ref = g[g["kind"] == "ref"].sort_values("block")
        key = g[g["kind"] == "key"].sort_values("block")
        rows = [r for pair in zip(ref.itertuples(), key.itertuples()) for r in pair]
        step = window / len(rows)
        for i, r in enumerate(rows):
            if not r.n_sifted > 0 or np.isnan(r.qber):
                continue
            t = t0 + w * window + (i + 1) * step
            out.append(BlockRecord(link_id, t.isoformat(), r.kind, int(r.n_sifted), int(round(r.qber * r.n_sifted))))
    return out
