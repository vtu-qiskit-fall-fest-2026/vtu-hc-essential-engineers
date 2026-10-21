"""Load IBM Quantum credentials from .env (gitignored), falling back to a saved account."""

from __future__ import annotations

import os
from pathlib import Path

from qiskit_ibm_runtime import QiskitRuntimeService

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


def load_env(path: Path = ENV_PATH) -> None:
    """Minimal KEY=VALUE reader. Existing environment variables take precedence."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def get_service() -> QiskitRuntimeService:
    """Use IBM_QUANTUM_TOKEN from .env if set, else the account saved with save_account()."""
    load_env()
    token = os.environ.get("IBM_QUANTUM_TOKEN")
    if not token:
        return QiskitRuntimeService()
    return QiskitRuntimeService(
        channel=os.environ.get("IBM_QUANTUM_CHANNEL") or "ibm_quantum_platform",
        token=token,
        instance=os.environ.get("IBM_QUANTUM_INSTANCE") or None,
    )


def default_backend_name(fallback: str = "ibm_kingston") -> str:
    load_env()
    return os.environ.get("IBM_BACKEND") or fallback
