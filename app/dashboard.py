"""Nirikshak dashboard (skeleton). Run: python -m nirikshak.dashboard"""

import numpy as np
import pandas as pd
import streamlit as st

from nirikshak.attacks import EntanglingProbe, InterceptResend
from nirikshak.detectors import ConformalThreshold, QBERThreshold
from nirikshak.features import block_features
from nirikshak.noise import simple_noise
from nirikshak.protocol import Rounds, build_template
from nirikshak.sim import make_simulator, run

st.set_page_config(page_title="Nirikshak", layout="wide")
st.title("Nirikshak")
st.caption("Catching real eavesdroppers on real quantum hardware. Simulator mode.")

with st.sidebar:
    attack_name = st.selectbox("Attack", ["none", "intercept_resend", "entangling_probe"])
    fraction = st.slider("Fraction of rounds attacked", 0.0, 1.0, 0.1, 0.05)
    readout = st.slider("Readout error (drift)", 0.0, 0.08, 0.02, 0.005)
    alpha = st.select_slider("Nirikshak false-alarm budget", [0.01, 0.05, 0.1], 0.05)
    n_blocks = st.slider("Blocks", 20, 200, 60, 10)

N_ROUNDS, SHOTS = 16, 32


@st.cache_data(show_spinner="Simulating...")
def simulate(attack_name, fraction, readout, n_blocks, seed):
    att = {"none": None,
           "intercept_resend": InterceptResend(fraction=fraction),
           "entangling_probe": EntanglingProbe(fraction=fraction)}[attack_name]
    rng = np.random.default_rng(seed)
    t = build_template(N_ROUNDS, att)
    r = Rounds.random(n_blocks, N_ROUNDS, rng)
    out = run(t, r, shots=SHOTS, backend=make_simulator(simple_noise(readout=readout), seed=seed))
    return block_features(r, out["bob"])


# Calibration: honest reference blocks at the same noise level (stand-in for interleaved reference rounds).
calib = simulate("none", 0.0, readout, 40, seed=7)
live = simulate(attack_name, fraction, readout, n_blocks, seed=11)

nk = ConformalThreshold(alpha).fit(calib["qber"].to_numpy())
base = QBERThreshold()
live["baseline_alarm"] = base.predict(live["qber"])
live["nirikshak_alarm"] = nk.predict(live["qber"].to_numpy())

c1, c2, c3 = st.columns(3)
c1.metric("Mean QBER", f"{live['qber'].mean():.3f}")
c2.metric("Baseline (11%) alarms", f"{live['baseline_alarm'].mean():.0%}")
c3.metric("Nirikshak alarms", f"{live['nirikshak_alarm'].mean():.0%}")

chart = pd.DataFrame({"QBER": live["qber"], "11% threshold": base.threshold,
                      "Nirikshak threshold": nk.threshold_})
st.line_chart(chart)
st.dataframe(live, width="stretch")
