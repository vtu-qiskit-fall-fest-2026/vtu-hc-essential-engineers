"""Sifting and error-rate estimation from Bob's results."""

from __future__ import annotations

import numpy as np

from nirikshak.protocol.bb84 import Rounds


def qber(rounds: Rounds, bob_bits: np.ndarray) -> dict[str, float]:
    """bob_bits: shape (n_bindings, shots, n_rounds). Choices broadcast over shots."""
    alice = rounds.alice_bits[:, None, :]
    sifted = (rounds.alice_bases == rounds.bob_bases)[:, None, :]
    sifted = np.broadcast_to(sifted, bob_bits.shape)
    errors = (bob_bits != alice) & sifted
    basis = np.broadcast_to(rounds.alice_bases[:, None, :], bob_bits.shape)

    def rate(mask):
        n = mask.sum()
        return float(errors[mask].sum() / n) if n else float("nan")

    return {
        "qber": rate(sifted),
        "qber_z": rate(sifted & (basis == 0)),
        "qber_x": rate(sifted & (basis == 1)),
        "sifted_fraction": float(sifted.mean()),
        "n_sifted": int(sifted.sum()),
    }
