"""A BB84 session = key rounds (through the channel, possibly attacked) + honest reference rounds.

Reference rounds come from a separate calibration circuit on the same qubits with no channel
and no attack slot, run in the same job as the key rounds. They see the same device noise and
drift, but Eve cannot touch them (in a real link: Bob checking his detectors with known local
states). Nirikshak calibrates its alarm threshold on them, per session.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from nirikshak.attacks import Attack, EntanglingProbe, InterceptResend
from nirikshak.features.blocks import block_features
from nirikshak.protocol.bb84 import BB84Template, Rounds, build_template

ATTACKS = ("none", "intercept_resend", "entangling_probe")


@dataclass(frozen=True)
class SessionSpec:
    attack: str = "none"
    fraction: float = 0.0        # nominal fraction of rounds attacked
    strength: float = np.pi / 4  # entangling probe only
    n_rounds: int = 16           # rounds per shot (one per qubit)
    key_blocks: int = 20
    ref_blocks: int = 20
    block_size: int = 8          # bindings per block
    shots: int = 8               # shots per binding
    seed: int = 0

    def __post_init__(self):
        if self.attack not in ATTACKS:
            raise ValueError(f"attack must be one of {ATTACKS}")

    def make_attack(self) -> Attack | None:
        if self.attack == "intercept_resend":
            return InterceptResend(fraction=self.fraction, seed=self.seed)
        if self.attack == "entangling_probe":
            return EntanglingProbe(strength=self.strength, fraction=self.fraction, seed=self.seed)
        return None

    @property
    def executions(self) -> int:
        return (self.key_blocks + self.ref_blocks) * self.block_size * self.shots


@dataclass
class Session:
    spec: SessionSpec
    key: BB84Template
    ref: BB84Template
    key_rounds: Rounds
    ref_rounds: Rounds

    @property
    def attacked_fraction(self) -> float:
        """Realized fraction of rounds Eve touches (nominal fraction rounded to whole rounds)."""
        return float(self.key.attack.attacked_mask(self.spec.n_rounds).mean())


def build_session(spec: SessionSpec) -> Session:
    rng = np.random.default_rng(spec.seed)
    n_key = spec.key_blocks * spec.block_size
    n_ref = spec.ref_blocks * spec.block_size
    return Session(
        spec=spec,
        key=build_template(spec.n_rounds, spec.make_attack()),
        ref=build_template(spec.n_rounds),  # calibration circuit: no channel, no attack slot
        key_rounds=Rounds.random(n_key, spec.n_rounds, rng),
        ref_rounds=Rounds.random(n_ref, spec.n_rounds, rng),
    )


def session_table(session: Session, key_bob: np.ndarray, ref_bob: np.ndarray, **context) -> pd.DataFrame:
    """One row per block (key and reference), with the session's labels and any context columns
    (session_id, backend, regime, job_id, ...)."""
    spec = session.spec
    frac = session.attacked_fraction
    parts = []
    for kind, rounds, bob in (("key", session.key_rounds, key_bob), ("ref", session.ref_rounds, ref_bob)):
        df = block_features(rounds, bob, spec.block_size)
        df.insert(0, "block", np.arange(len(df)))
        df.insert(0, "kind", kind)
        df["is_attack"] = kind == "key" and frac > 0
        parts.append(df)
    table = pd.concat(parts, ignore_index=True)
    labels = {k: v for k, v in asdict(spec).items() if k not in ("key_blocks", "ref_blocks")}
    labels["attacked_fraction"] = frac
    for k, v in {**labels, **context}.items():
        table[k] = v
    return table


def simulate_session(spec: SessionSpec, backend=None, **context) -> pd.DataFrame:
    """Run one session on an Aer backend (key and reference circuits in one Sampler call)."""
    from nirikshak.sim import run_many

    s = build_session(spec)
    key_out, ref_out = run_many([(s.key, s.key_rounds), (s.ref, s.ref_rounds)], shots=spec.shots, backend=backend)
    return session_table(s, key_out["bob"], ref_out["bob"], **context)
