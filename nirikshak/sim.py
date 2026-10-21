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
    return run_many([(template, rounds)], shots=shots, backend=backend)[0]


def run_many(cases: list[tuple[BB84Template, Rounds]], shots: int = 64,
             backend: AerSimulator | None = None) -> list[dict[str, np.ndarray]]:
    """Run several templates as PUBs of one Sampler call (one job on hardware)."""
    backend = backend or make_simulator()
    pubs = [(transpile(t.circuit, backend), t.parameter_values(r)) for t, r in cases]
    result = BackendSamplerV2(backend=backend).run(pubs, shots=shots).result()
    return [{name: bits_to_array(getattr(res.data, name)) for name in ("bob", "eve") if hasattr(res.data, name)}
            for res in result]


def bits_to_array(bit_array) -> np.ndarray:
    """BitArray -> bool array (..., shots, num_bits) where index j is classical bit j."""
    return bit_array.to_bool_array(order="little")
