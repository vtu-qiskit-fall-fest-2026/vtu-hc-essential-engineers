"""Submit BB84 templates to IBM Quantum hardware (Open Plan: job or batch mode, no sessions).

Budget rules: test the exact template on the simulator first, submit one small job,
read its usage, then scale. At most 3 jobs may be queued or running per user.
"""

from __future__ import annotations

from collections.abc import Iterable

from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime import SamplerV2

from nirikshak.hardware.calibration import pick_layout
from nirikshak.hardware.credentials import default_backend_name, get_service
from nirikshak.protocol.bb84 import BB84Template

DEFAULT_BACKEND = default_backend_name()


def get_backend(name: str = DEFAULT_BACKEND):
    """Credentials from .env (IBM_QUANTUM_TOKEN), else the locally saved account."""
    return get_service().backend(name)


def compile_template(template: BB84Template, backend, layout: list[int] | str | None = "auto",
                     exclude: Iterable[int] = (), seed: int | None = None):
    """Transpile to the backend ISA. layout="auto" picks qubits from live calibration
    (see pick_layout); a list pins them; None lets the transpiler choose (defaults to 0..n-1)."""
    if layout == "auto":
        layout = pick_layout(backend, template, exclude=exclude)
    pm = generate_preset_pass_manager(optimization_level=1, backend=backend,
                                      initial_layout=layout, seed_transpiler=seed)
    return pm.run(template.circuit)


def signal_qubits(isa, n_rounds: int) -> list[int]:
    """Physical qubit measured into bob[i], for each round i."""
    return [int(q) for q in isa.layout.final_index_layout()[:n_rounds]]


def submit(pubs: list, backend, shots: int = 1000):
    """Submit ISA PUBs [(isa_circuit, parameter_values), ...] as one Sampler job."""
    return SamplerV2(mode=backend).run(pubs, shots=shots)
