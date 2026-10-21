"""Scorecard metrics: report misses at a fixed false-alarm budget, not just accuracy."""

from __future__ import annotations

import numpy as np


def false_alarm_rate(alarms: np.ndarray, is_attack: np.ndarray) -> float:
    honest = ~np.asarray(is_attack, dtype=bool)
    return float(np.asarray(alarms)[honest].mean()) if honest.any() else float("nan")


def miss_rate(alarms: np.ndarray, is_attack: np.ndarray) -> float:
    attack = np.asarray(is_attack, dtype=bool)
    return float((~np.asarray(alarms)[attack]).mean()) if attack.any() else float("nan")


def scorecard(alarms: np.ndarray, is_attack: np.ndarray) -> dict[str, float]:
    return {
        "false_alarm_rate": false_alarm_rate(alarms, is_attack),
        "miss_rate": miss_rate(alarms, is_attack),
    }
