"""Qubit selection and calibration snapshots from backend.properties().

The smoke test (job dbcalg9gv2cc73e9unp0) showed the reported calibration can disagree with
what a qubit actually does during the run, so selection here is only a first filter: per-round
features on honest reference rounds are what flag bad qubits at run time (pass them as `exclude`).
"""

from __future__ import annotations

import math
from collections.abc import Iterable

from nirikshak.protocol.bb84 import BB84Template


def _prop(props, q: int, name: str) -> float:
    try:
        return float(props.qubit_property(q, name)[0])
    except Exception:  # property missing for this qubit
        return math.nan


def qubit_score(props, q: int) -> float:
    """Lower is better: readout error + SX error. Inf if non-operational or uncalibrated."""
    if not props.is_qubit_operational(q):
        return math.inf
    try:
        score = props.readout_error(q) + props.gate_error("sx", q)
    except Exception:
        return math.inf
    return score if math.isfinite(score) else math.inf


def pick_layout(backend, template: BB84Template, exclude: Iterable[int] = (), spread: bool = True) -> list[int]:
    """Physical qubits for the template's virtual qubits (signal register first, then ancillas).

    Greedy by calibration score. With spread=True no chosen qubit neighbours a qubit used by
    another round, to limit crosstalk from mid-circuit measurements.
    """
    props = backend.properties()
    n = template.n_rounds
    n_anc = template.circuit.num_qubits - n
    neighbours: dict[int, set[int]] = {q: set() for q in range(backend.num_qubits)}
    for a, b in backend.coupling_map.get_edges():
        neighbours[a].add(b)
        neighbours[b].add(a)
    banned = set(exclude)
    score = {q: (math.inf if q in banned else qubit_score(props, q)) for q in range(backend.num_qubits)}

    if n_anc == 0:
        units = sorted(((score[q], (q,)) for q in score if math.isfinite(score[q])))
    elif n_anc == n:  # one ancilla per round, must be coupled to its signal qubit
        units = sorted(((score[s] + score[a], (s, a)) for s in score for a in neighbours[s]
                        if math.isfinite(score[s] + score[a])))
    else:
        raise ValueError(f"unsupported ancilla count {n_anc} for {n} rounds")

    used: set[int] = set()
    blocked: set[int] = set()
    chosen: list[tuple[int, ...]] = []
    for _, unit in units:
        if any(q in used or q in blocked for q in unit):
            continue
        chosen.append(unit)
        used.update(unit)
        if spread:
            for q in unit:
                blocked.update(neighbours[q])
        if len(chosen) == n:
            break
    if len(chosen) < n:
        raise RuntimeError(f"only {len(chosen)} usable qubit units for {n} rounds; try spread=False")
    return [u[0] for u in chosen] + [u[1] for u in chosen if len(u) > 1]


def calibration_snapshot(backend, qubits: Iterable[int], refresh: bool = False) -> dict:
    """Reported calibration for the given physical qubits, to store with each job."""
    props = backend.properties(refresh=refresh)
    rows = []
    for q in qubits:
        try:
            sx = props.gate_error("sx", q)
        except Exception:
            sx = math.nan
        rows.append({
            "qubit": int(q),
            "readout_error": _prop(props, q, "readout_error"),
            "prob_meas1_prep0": _prop(props, q, "prob_meas1_prep0"),
            "prob_meas0_prep1": _prop(props, q, "prob_meas0_prep1"),
            "t1_us": _prop(props, q, "T1") * 1e6,
            "t2_us": _prop(props, q, "T2") * 1e6,
            "sx_error": sx,
            "operational": bool(props.is_qubit_operational(q)),
        })
    return {"last_update_date": str(props.last_update_date), "qubits": rows}
