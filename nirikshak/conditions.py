"""Standard attack conditions, shared by the simulated dataset and hardware batches."""

from __future__ import annotations

import numpy as np

from nirikshak.session import SessionSpec

# With 16 rounds per shot, fractions are whole rounds: 1/16 = 6.25% of rounds attacked.
IR_FRACTIONS = (1 / 16, 2 / 16, 4 / 16, 8 / 16)
EP_SETTINGS = ((np.pi / 4, 0.5), (np.pi / 4, 1.0), (np.pi / 8, 1.0))  # (strength, fraction)


def standard_conditions(seed0: int = 0, honest_repeats: int = 3, **spec_kwargs) -> list[SessionSpec]:
    """Honest sessions, partial intercept-resend at several fractions, entangling probes.
    Each session gets its own seed (attacked rounds and random choices differ)."""
    specs = [SessionSpec(attack="none", **spec_kwargs) for _ in range(honest_repeats)]
    specs += [SessionSpec(attack="intercept_resend", fraction=f, **spec_kwargs) for f in IR_FRACTIONS]
    specs += [SessionSpec(attack="entangling_probe", strength=s, fraction=f, **spec_kwargs) for s, f in EP_SETTINGS]
    return [SessionSpec(**{**spec.__dict__, "seed": seed0 + i}) for i, spec in enumerate(specs)]
