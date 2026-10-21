"""Attack interface. An attack inserts operations on a signal qubit between Alice and Bob."""

from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Clbit, Parameter, Qubit


class Attack:
    name = "base"
    ancillas_per_round = 0
    uses_eve_register = False

    def __init__(self, fraction: float = 1.0, seed: int = 0):
        if not 0.0 <= fraction <= 1.0:
            raise ValueError("fraction must be in [0, 1]")
        self.fraction = fraction
        self.seed = seed
        self._mask: np.ndarray | None = None

    def attacked_mask(self, n_rounds: int) -> np.ndarray:
        """Which rounds Eve touches. Fixed per template so the circuit is static."""
        if self._mask is None or len(self._mask) != n_rounds:
            rng = np.random.default_rng(self.seed)
            k = int(round(self.fraction * n_rounds))
            mask = np.zeros(n_rounds, dtype=bool)
            mask[rng.choice(n_rounds, size=k, replace=False)] = True
            self._mask = mask
        return self._mask

    def apply(self, qc: QuantumCircuit, i: int, qubit: Qubit, e_basis: Parameter,
              eve: list[Clbit] | None, ancilla: Qubit | None) -> None:
        raise NotImplementedError


class NoAttack(Attack):
    name = "none"

    def __init__(self):
        super().__init__(fraction=0.0)

    def apply(self, qc, i, qubit, e_basis, eve, ancilla):
        return
