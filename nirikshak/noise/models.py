"""Noise and drift models for simulation."""

from __future__ import annotations

from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error


def simple_noise(p1: float = 0.001, p2: float = 0.01, readout: float = 0.01) -> NoiseModel:
    """Depolarizing gate noise plus symmetric readout error."""
    nm = NoiseModel()
    if p1 > 0:
        nm.add_all_qubit_quantum_error(depolarizing_error(p1, 1), ["rx", "ry"])
    if p2 > 0:
        nm.add_all_qubit_quantum_error(depolarizing_error(p2, 2), ["cry"])
    if readout > 0:
        nm.add_all_qubit_readout_error(ReadoutError([[1 - readout, readout], [readout, 1 - readout]]))
    return nm


def drift_schedule(n_blocks: int, start: float, end: float) -> list[float]:
    """Linear drift of a noise parameter across blocks (benign, not an attack)."""
    if n_blocks == 1:
        return [start]
    step = (end - start) / (n_blocks - 1)
    return [start + k * step for k in range(n_blocks)]
