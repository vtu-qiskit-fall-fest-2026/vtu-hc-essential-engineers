"""Per-block features for detectors. One block = one binding (all its shots)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from nirikshak.protocol.bb84 import Rounds


def block_features(rounds: Rounds, bob_bits: np.ndarray) -> pd.DataFrame:
    """bob_bits: (n_bindings, shots, n_rounds). Returns one row per binding."""
    alice = rounds.alice_bits[:, None, :]
    sifted = np.broadcast_to((rounds.alice_bases == rounds.bob_bases)[:, None, :], bob_bits.shape)
    basis = np.broadcast_to(rounds.alice_bases[:, None, :], bob_bits.shape)
    err = (bob_bits != alice) & sifted
    axes = (1, 2)

    def rate(mask):
        n = mask.sum(axis=axes)
        return np.divide(err.sum(axis=axes, where=mask), n, out=np.full(n.shape, np.nan), where=n > 0)

    qz, qx = rate(sifted & (basis == 0)), rate(sifted & (basis == 1))
    return pd.DataFrame({
        "qber": rate(sifted),
        "qber_z": qz,
        "qber_x": qx,
        "basis_asymmetry": qz - qx,
        "n_sifted": sifted.sum(axis=axes),
    })


def round_features(rounds: Rounds, bob_bits: np.ndarray, qubits: list[int] | None = None) -> pd.DataFrame:
    """One row per round position (= one physical qubit), pooled over bindings and shots.

    Flags bad qubits from honest data, independent of reported calibration. err_z_sent0 vs
    err_z_sent1 separates bit-flip directions (e.g. T1 decay shows as err_z_sent1 > err_z_sent0).
    """
    alice = rounds.alice_bits[:, None, :]
    shape = bob_bits.shape
    sifted = np.broadcast_to((rounds.alice_bases == rounds.bob_bases)[:, None, :], shape)
    basis = np.broadcast_to(rounds.alice_bases[:, None, :], shape)
    sent = np.broadcast_to(alice, shape)
    err = (bob_bits != alice) & sifted
    axes = (0, 1)

    def rate(mask):
        n = mask.sum(axis=axes)
        return np.divide((err & mask).sum(axis=axes), n, out=np.full(n.shape, np.nan), where=n > 0)

    z = sifted & (basis == 0)
    return pd.DataFrame({
        "round": np.arange(shape[2]),
        "qubit": qubits if qubits is not None else np.full(shape[2], -1),
        "qber": rate(sifted),
        "qber_z": rate(z),
        "qber_x": rate(sifted & (basis == 1)),
        "err_z_sent0": rate(z & (sent == 0)),
        "err_z_sent1": rate(z & (sent == 1)),
        "n_sifted": sifted.sum(axis=axes),
    })
