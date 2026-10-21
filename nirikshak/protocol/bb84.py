"""BB84 circuits with many rounds in parallel, one round per signal qubit.

Encoding (Z basis = 0, X basis = 1):
    prepare: rx(pi * bit) then ry(pi/2 * basis)   -> |0>, |1>, |+>, |->
    measure: ry(-pi/2 * basis) then measure in Z

Everything is parameterized so one transpiled template can be swept over
many random bit/basis assignments (one Sampler PUB, many bindings).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit import ParameterVector

from nirikshak.attacks.base import Attack, NoAttack


@dataclass
class Rounds:
    """Random choices for a batch of bindings. Arrays have shape (n_bindings, n_rounds)."""

    alice_bits: np.ndarray
    alice_bases: np.ndarray
    bob_bases: np.ndarray
    eve_bases: np.ndarray

    @classmethod
    def random(cls, n_bindings: int, n_rounds: int, rng: np.random.Generator) -> "Rounds":
        def draw():
            return rng.integers(0, 2, size=(n_bindings, n_rounds), dtype=np.uint8)

        return cls(draw(), draw(), draw(), draw())


@dataclass
class BB84Template:
    circuit: QuantumCircuit
    n_rounds: int
    attack: Attack
    a_bit: ParameterVector
    a_basis: ParameterVector
    b_basis: ParameterVector
    e_basis: ParameterVector

    def parameter_values(self, rounds: Rounds) -> np.ndarray:
        """Map random choices to an array of shape (n_bindings, n_params) in circuit parameter order."""
        by_name = {}
        for vec, values in (
            (self.a_bit, rounds.alice_bits * np.pi),
            (self.a_basis, rounds.alice_bases * (np.pi / 2)),
            (self.b_basis, rounds.bob_bases * (-np.pi / 2)),
            (self.e_basis, rounds.eve_bases * (-np.pi / 2)),
        ):
            for i, p in enumerate(vec):
                by_name[p.name] = values[:, i]
        return np.stack([by_name[p.name] for p in self.circuit.parameters], axis=1)


def build_template(n_rounds: int, attack: Attack | None = None) -> BB84Template:
    attack = attack or NoAttack()
    a_bit = ParameterVector("a_bit", n_rounds)
    a_basis = ParameterVector("a_basis", n_rounds)
    b_basis = ParameterVector("b_basis", n_rounds)
    e_basis = ParameterVector("e_basis", n_rounds)

    signal = QuantumRegister(n_rounds, "sig")
    ancilla = QuantumRegister(attack.ancillas_per_round * n_rounds, "anc") if attack.ancillas_per_round else None
    bob = ClassicalRegister(n_rounds, "bob")
    regs = [signal] + ([ancilla] if ancilla else []) + [bob]
    if attack.uses_eve_register:
        regs.append(ClassicalRegister(n_rounds, "eve"))
    qc = QuantumCircuit(*regs)
    eve = qc.cregs[-1] if attack.uses_eve_register else None

    for i in range(n_rounds):
        qc.rx(a_bit[i], signal[i])
        qc.ry(a_basis[i], signal[i])
    qc.barrier()
    for i in range(n_rounds):
        anc = ancilla[i] if ancilla else None
        attack.apply(qc, i, signal[i], e_basis[i], eve, anc)
    qc.barrier()
    for i in range(n_rounds):
        qc.ry(b_basis[i], signal[i])
    qc.measure(signal, bob)

    # If the attack never touches e_basis, those parameters are absent from the circuit;
    # parameter_values() only emits parameters the circuit actually has.
    return BB84Template(qc, n_rounds, attack, a_bit, a_basis, b_basis, e_basis)
