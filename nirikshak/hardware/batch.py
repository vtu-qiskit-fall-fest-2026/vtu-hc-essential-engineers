"""Hardware batches: many sessions in one Sampler job, two PUBs per session (key, reference)."""

from __future__ import annotations

from dataclasses import asdict

import numpy as np
import pandas as pd

from nirikshak.hardware.calibration import pick_layout
from nirikshak.hardware.runner import compile_template, signal_qubits
from nirikshak.hardware.timing import slot_duration
from nirikshak.protocol.bb84 import build_template
from nirikshak.session import Session, SessionSpec, build_session, session_table
from nirikshak.sim import bits_to_array


def compile_sessions(sessions: list[Session], backend, exclude=(), seed: int | None = None,
                     match_timing: bool = True):
    """Returns (pubs, layouts, slot_dt). Key and reference circuits of a session share the same
    signal qubits. With match_timing, every circuit is padded to the same slot duration slot_dt."""
    layouts_full = [pick_layout(backend, s.key, exclude=exclude) for s in sessions]
    slot_dt = 0
    if match_timing:
        slot_dt = max(slot_duration(compile_template(s.key, backend, layout=lay, seed=seed), backend)
                      for s, lay in zip(sessions, layouts_full))
    pubs, layouts = [], []
    for s, layout in zip(sessions, layouts_full):
        n = s.spec.n_rounds
        key_t, ref_t = s.key, s.ref
        if match_timing:
            own = slot_duration(compile_template(s.key, backend, layout=layout, seed=seed), backend)
            key_t = build_template(n, s.key.attack, slot_delay=slot_dt - own)
            ref_t = build_template(n, None, slot_delay=slot_dt)
        key_isa = compile_template(key_t, backend, layout=layout, seed=seed)
        ref_isa = compile_template(ref_t, backend, layout=layout[:n], seed=seed)
        if signal_qubits(key_isa, n) != signal_qubits(ref_isa, n):
            raise RuntimeError("key and reference circuits landed on different qubits")
        if match_timing and not slot_duration(key_isa, backend) == slot_duration(ref_isa, backend) == slot_dt:
            raise RuntimeError("timing match failed")
        pubs += [(key_isa, key_t.parameter_values(s.key_rounds)),
                 (ref_isa, ref_t.parameter_values(s.ref_rounds))]
        layouts.append(signal_qubits(key_isa, n))
    return pubs, layouts, slot_dt


def specs_to_json(sessions: list[Session]) -> list[dict]:
    return [asdict(s.spec) for s in sessions]


def sessions_from_json(specs: list[dict]) -> list[Session]:
    """Rebuild sessions; random choices are regenerated deterministically from each spec's seed."""
    return [build_session(SessionSpec(**d)) for d in specs]


def rounds_arrays(sessions: list[Session]) -> dict[str, np.ndarray]:
    out = {}
    for i, s in enumerate(sessions):
        for kind, r in (("key", s.key_rounds), ("ref", s.ref_rounds)):
            for field in ("alice_bits", "alice_bases", "bob_bases", "eve_bases"):
                out[f"{i}_{kind}_{field}"] = getattr(r, field)
    return out


def decode(sessions: list[Session], result, layouts: list[list[int]], **context) -> tuple[pd.DataFrame, dict]:
    """Sampler result (2 PUBs per session) -> block table, plus raw bit arrays."""
    tables, bits = [], {}
    for i, s in enumerate(sessions):
        key_bob = bits_to_array(result[2 * i].data.bob)
        ref_bob = bits_to_array(result[2 * i + 1].data.bob)
        bits[f"{i}_key_bob"], bits[f"{i}_ref_bob"] = key_bob, ref_bob
        sid = f"{context.get('job_id', 'local')}:{i}"
        tables.append(session_table(s, key_bob, ref_bob, session_id=sid,
                                    qubits=",".join(map(str, layouts[i])), **context))
    return pd.concat(tables, ignore_index=True), bits
