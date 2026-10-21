"""Entangling probe: Eve weakly couples an ancilla to the signal and measures the ancilla.

strength = pi gives a full copy in Eve's basis (equivalent to intercept-resend for that basis);
smaller values leak less information and cause less disturbance.
"""

from __future__ import annotations

import numpy as np

from nirikshak.attacks.base import Attack


class EntanglingProbe(Attack):
    name = "entangling_probe"
    ancillas_per_round = 1
    uses_eve_register = True

    def __init__(self, strength: float = np.pi / 4, fraction: float = 1.0, seed: int = 0):
        super().__init__(fraction=fraction, seed=seed)
        self.strength = strength

    def apply(self, qc, i, qubit, e_basis, eve, ancilla):
        if not self.attacked_mask(len(eve))[i]:
            return
        qc.ry(e_basis, qubit)
        qc.cry(self.strength, qubit, ancilla)
        qc.ry(-e_basis, qubit)
        qc.measure(ancilla, eve[i])
