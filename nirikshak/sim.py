"""Run BB84 templates on the local Aer simulator through the same Sampler V2 interface as IBM hardware."""

from __future__ import annotations

import numpy as np
from qiskit import transpile
from qiskit.primitives import BackendSamplerV2
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel

from nirikshak.protocol.bb84 import BB84Template, Rounds


def make_simulator(noise_model: NoiseModel | None = None, seed: int | None = None) -> AerSimulator:
    # Rounds are unentangled (or entangled in pairs for probes), so matrix-product-state
    # simulation stays cheap even with many parallel rounds per circuit.
    return AerSimulator(method="matrix_product_state", noise_model=noise_model, seed_simulator=seed)


def run(template: BB84Template, rounds: Rounds, shots: int = 64,
        backend: AerSimulator | None = None) -> dict[str, np.ndarray]:
    """Returns bool arrays of shape (n_bindings, shots, n_rounds) per classical register."""
    backend = backend or make_simulator()
    tqc = transpile(template.circuit, backend)
    sampler = BackendSamplerV2(backend=backend)
    result = sampler.run([(tqc, template.parameter_values(rounds))], shots=shots).result()[0]
    return {name: bits_to_array(getattr(result.data, name))
            for name in ("bob", "eve") if hasattr(result.data, name)}


def bits_to_array(bit_array) -> np.ndarray:
    """BitArray -> bool array (..., shots, num_bits) where index j is classical bit j."""
    return bit_array.to_bool_array(order="little")
