"""Streaming Nirikshak: per-link alarms from telemetry, as blocks arrive.

Per link, two outputs:
- Window verdict (the decision): every `window` key blocks, a one-sided permutation test of the
  window's key blocks against the reference blocks received in the same window. Under no attack
  P(alarm) <= alpha per window, however the link drifts.
- Block alarms (where to look): each key block against a split-conformal threshold from the last
  `ref_history` reference blocks.

For comparison each link also tracks two fixed rules: the 11% QBER limit, and a commissioning
threshold, calibrated once on the first reference blocks and then frozen (what a static
monitoring rule does when the link drifts).

alpha is per link and window: with many links, expect about alpha x links x windows false alarms
in total, or pass a smaller alpha.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from nirikshak.detectors.conformal import ConformalThreshold
from nirikshak.detectors.session_test import permutation_pvalue
from nirikshak.monitor.telemetry import BlockRecord
from nirikshak.protocol.keyrate import SHOR_PRESKILL_QBER


@dataclass
class Verdict:
    link_id: str
    t_start: str
    t_end: str
    key_blocks: int
    ref_blocks: int
    key_qber: float
    ref_qber: float
    p_value: float
    alarm: bool
    blocks_flagged: int          # Nirikshak block alarms in the window
    blocks_flagged_frozen: int   # commissioning threshold
    blocks_flagged_11: int       # 11% rule


@dataclass
class LinkMonitor:
    link_id: str
    alpha: float = 0.05
    window: int = 20
    ref_history: int = 20
    n_perm: int = 9999
    _ref_hist: deque = field(init=False, repr=False)
    _key: list = field(default_factory=list, init=False, repr=False)
    _ref: list = field(default_factory=list, init=False, repr=False)
    _t_start: str | None = field(default=None, init=False, repr=False)
    _counts: list = field(default_factory=lambda: [0, 0, 0], init=False, repr=False)
    frozen_threshold: float | None = field(default=None, init=False)
    n_windows: int = field(default=0, init=False)

    def __post_init__(self):
        self._ref_hist = deque(maxlen=self.ref_history)

    def threshold(self) -> float | None:
        """Current block threshold, or None while fewer reference blocks than alpha needs."""
        try:
            return ConformalThreshold(self.alpha).fit(np.fromiter(self._ref_hist, float)).threshold_
        except ValueError:
            return None

    def update(self, rec: BlockRecord) -> dict | Verdict | None:
        """Feed one record. Returns a block event (key blocks), a Verdict when a window closes, else None."""
        if rec.link_id != self.link_id:
            raise ValueError(f"record for {rec.link_id} sent to monitor {self.link_id}")
        self._t_start = self._t_start or rec.t
        q = rec.qber
        if rec.kind == "ref":
            self._ref.append(q)
            self._ref_hist.append(q)
            if self.frozen_threshold is None:
                self.frozen_threshold = self.threshold()
            return self._maybe_close(rec.t)
        thr = self.threshold()
        event = {"link_id": self.link_id, "t": rec.t, "qber": q, "threshold": thr,
                 "alarm": thr is not None and q > thr,
                 "alarm_frozen": self.frozen_threshold is not None and q > self.frozen_threshold,
                 "alarm_11": q > SHOR_PRESKILL_QBER}
        self._key.append(q)
        for i, k in enumerate(("alarm", "alarm_frozen", "alarm_11")):
            self._counts[i] += event[k]
        return self._maybe_close(rec.t) or event

    def _maybe_close(self, t: str) -> Verdict | None:
        if len(self._key) < self.window or len(self._ref) < self.window:
            return None
        key, ref = np.array(self._key), np.array(self._ref)
        p = permutation_pvalue(key, ref, self.n_perm, seed=self.n_windows)
        v = Verdict(self.link_id, self._t_start, t, len(key), len(ref), float(key.mean()), float(ref.mean()),
                    p, p < self.alpha, *self._counts)
        self._key, self._ref, self._t_start, self._counts = [], [], None, [0, 0, 0]
        self.n_windows += 1
        return v


class NetworkMonitor:
    """One LinkMonitor per link, created on first sight; keeps the verdict and block logs."""

    def __init__(self, alpha: float = 0.05, window: int = 20, ref_history: int = 20, n_perm: int = 9999):
        self.params = dict(alpha=alpha, window=window, ref_history=ref_history, n_perm=n_perm)
        self.links: dict[str, LinkMonitor] = {}
        self.verdicts: list[Verdict] = []
        self.blocks: list[dict] = []

    def update(self, rec: BlockRecord) -> Verdict | None:
        mon = self.links.get(rec.link_id) or self.links.setdefault(rec.link_id, LinkMonitor(rec.link_id, **self.params))
        out = mon.update(rec)
        if isinstance(out, Verdict):
            self.verdicts.append(out)
            return out
        if out is not None:
            self.blocks.append(out)
        return None

    def run(self, records) -> "NetworkMonitor":
        for r in records:
            self.update(r)
        return self

    def verdict_table(self) -> pd.DataFrame:
        return pd.DataFrame([v.__dict__ for v in self.verdicts])

    def alarm_log(self) -> pd.DataFrame:
        v = self.verdict_table()
        return v[v["alarm"]] if len(v) else v

    def status(self) -> pd.DataFrame:
        v = self.verdict_table()
        rows = []
        for link, mon in self.links.items():
            lv = v[v["link_id"] == link] if len(v) else v
            last = lv.iloc[-1] if len(lv) else None
            rows.append({"link_id": link, "windows": len(lv), "alarms": int(lv["alarm"].sum()) if len(lv) else 0,
                         "status": "warming up" if last is None else "ALARM" if last.alarm else "ok",
                         "last_p_value": None if last is None else last.p_value,
                         "last_key_qber": None if last is None else last.key_qber,
                         "last_ref_qber": None if last is None else last.ref_qber})
        return pd.DataFrame(rows)
