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


def condition_report(key_table, alarm_cols: list[str],
                     by: tuple[str, ...] = ("attack", "attacked_fraction", "strength")):
    """Per attack condition: false-alarm rate (honest conditions) or detection rate (attacked),
    for each alarm column. Expects key-block rows with an `is_attack` column."""
    import pandas as pd

    rows = []
    for cond, g in key_table.groupby(list(by), sort=True):
        row = dict(zip(by, cond if isinstance(cond, tuple) else (cond,)))
        row["blocks"] = len(g)
        attacked = bool(g["is_attack"].any())
        for col in alarm_cols:
            rate = float(g[col].mean())
            row[col] = rate
        row["metric"] = "detection_rate" if attacked else "false_alarm_rate"
        rows.append(row)
    return pd.DataFrame(rows)
