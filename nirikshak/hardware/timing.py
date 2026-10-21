"""Timing match between circuits with and without an attack.

On hardware, Eve's mid-circuit operations make every qubit wait at the barrier, and idle qubits
dephase (batch 1: X-basis error on rounds Eve never touched rose from 0.6% to 4-11%). A real
eavesdropper would not slow down Bob's other rounds, so all circuits in a batch are padded to the
same slot duration: the only difference left between circuits is Eve herself.
"""

from __future__ import annotations


def slot_duration(isa, backend) -> int:
    """Critical-path duration (dt) of the operations between the two barriers of an ISA template."""
    target = backend.target
    idx = [i for i, inst in enumerate(isa.data) if inst.operation.name == "barrier"]
    if len(idx) < 2:
        raise ValueError("expected the two slot barriers of a BB84 template")
    t: dict[int, float] = {}
    for inst in isa.data[idx[0] + 1:idx[1]]:
        qs = [isa.find_bit(q).index for q in inst.qubits]
        name = inst.operation.name
        if name == "delay":
            dur = inst.operation.duration if inst.operation.unit == "dt" else inst.operation.duration / target.dt
        else:
            dur = (target[name][tuple(qs)].duration or 0.0) / target.dt
        start = max(t.get(q, 0.0) for q in qs)
        for q in qs:
            t[q] = start + dur
    return int(round(max(t.values(), default=0.0)))
