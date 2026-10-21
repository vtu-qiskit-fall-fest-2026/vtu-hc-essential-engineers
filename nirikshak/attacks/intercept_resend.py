"""Intercept-resend: Eve measures in a random basis, then re-sends the state she saw.

Re-sending needs no feed-forward: after a Z measurement the qubit is |m>, and undoing
Eve's basis rotation turns it into the state she measured. Needs mid-circuit measurement.
Expected QBER on sifted rounds: 0.25 * fraction (noiseless).
"""

from __future__ import annotations

from nirikshak.attacks.base import Attack


class InterceptResend(Attack):
    name = "intercept_resend"
    uses_eve_register = True

    def apply(self, qc, i, qubit, e_basis, eve, ancilla):
        if not self.attacked_mask(len(eve))[i]:
            return
        qc.ry(e_basis, qubit)        # rotate into Eve's basis (e_basis = -pi/2 * basis)
        qc.measure(qubit, eve[i])    # mid-circuit measurement
        qc.ry(-e_basis, qubit)       # re-prepare the measured state in Eve's basis
