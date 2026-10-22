"""Nirikshak dashboard. Run: python -m nirikshak.dashboard

Tabs: real IBM hardware results, the sim-to-real stress test, a live simulator, the hardware
lessons, and a network monitor prototype. Reads the committed datasets in data/hardware, data/sim and results/.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from nirikshak.detectors import QBERThreshold, ReferenceConformal, SessionTest
from nirikshak.monitor import NetworkMonitor
from nirikshak.monitor.synthetic import default_scenarios, demo_network, hardware_replay_labels
from nirikshak.protocol import bb84_key_rate
from nirikshak.noise import simple_noise
from nirikshak.session import SessionSpec, simulate_session
from nirikshak.sim import make_simulator

ROOT = Path(__file__).resolve().parents[1]
ALPHA = 0.05

st.set_page_config(page_title="Nirikshak", layout="wide")

# Palette: categorical slots 1-2 (validated light and dark), gray for de-emphasis.
DARK = getattr(st.context.theme, "type", "light") == "dark"
BLUE = "#3987e5" if DARK else "#2a78d6"     # Nirikshak / attacked blocks
ORANGE = "#d95926" if DARK else "#eb6834"   # Nirikshak threshold
GRAY = "#898781"                            # honest blocks, 11% rule, other detectors
GRID = "#2c2c2a" if DARK else "#e1e0d9"
SURFACE = "#1a1a19" if DARK else "#fcfcfb"


def style(fig: go.Figure, height: int = 380, **layout) -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), barcornerradius=4,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0), hovermode="closest",
                      **layout)
    fig.update_xaxes(gridcolor=GRID, gridwidth=1, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, gridwidth=1, zeroline=False)
    return fig


def condition(attack: str, frac: float, strength: float) -> str:
    if attack == "none":
        return "Honest"
    if attack == "intercept_resend":
        return f"Intercept {round(frac * 16)}/16"
    return f"Probe {'pi/8' if strength < 0.5 else 'pi/4'}, {round(frac * 16)}/16"


# ---------------------------------------------------------------- data

@st.cache_data
def load_hardware() -> dict[str, pd.DataFrame]:
    lessons = pd.read_csv(ROOT / "results" / "hardware_lessons.csv").set_index("job_id")
    out = {}
    for p in sorted((ROOT / "data" / "hardware").glob("*.parquet")):
        df = pd.read_parquet(p)
        timing = lessons.loc[p.stem, "timing"] if p.stem in lessons.index else "unknown"
        out[f"Batch {df['batch'].iloc[0]}, {df['backend_name'].iloc[0]}: {timing} ({p.stem})"] = df
    return out


def score(table: pd.DataFrame) -> pd.DataFrame:
    """Key blocks with Nirikshak threshold/alarm, 11% alarm, session order and condition label."""
    key = ReferenceConformal(ALPHA).predict_table(table)
    key["rule_11"] = QBERThreshold().predict(key["qber"])
    key["session_idx"] = key["session_id"].str.split(":").str[-1].astype(int)
    key["condition"] = [condition(a, f, s) for a, f, s in zip(key.attack, key.attacked_fraction, key.strength)]
    return key.sort_values(["session_idx", "block"])


# ---------------------------------------------------------------- charts

def timeline(key: pd.DataFrame, title: str) -> go.Figure:
    """Every key block in session order: QBER, per-session Nirikshak threshold, and the 11% line."""
    gap = 3
    x, pos, centers, labels = [], 0, [], []
    for _, g in key.groupby("session_idx", sort=True):
        xs = np.arange(pos, pos + len(g))
        x.append(pd.Series(xs, index=g.index))
        centers.append(xs.mean())
        labels.append(g["condition"].iloc[0])
        pos += len(g) + gap
    key = key.assign(x=pd.concat(x))
    fig = go.Figure()
    for attacked, name, color in ((False, "Honest sessions", GRAY), (True, "Attacked sessions", BLUE)):
        for alarm in (True, False):
            g = key[(key.is_attack == attacked) & (key.alarm == alarm)]
            if g.empty:
                continue
            fig.add_trace(go.Scatter(
                x=g.x, y=g.qber, mode="markers", legendgroup=name,
                name=f"{name}, {'flagged' if alarm else 'not flagged'}",
                marker=dict(size=9, color=color if alarm else SURFACE, symbol="circle",
                            line=dict(color=color, width=2)),
                customdata=np.stack([g.condition, g.block, g.threshold, g.alarm.map({True: "yes", False: "no"})], axis=1),
                hovertemplate="%{customdata[0]}, block %{customdata[1]}<br>QBER %{y:.2%}"
                              "<br>Nirikshak threshold %{customdata[2]:.2%}<br>Flagged: %{customdata[3]}<extra></extra>"))
    # Per-session threshold as a step line (None breaks between sessions)
    tx, ty = [], []
    for _, g in key.groupby("session_idx", sort=True):
        tx += [g.x.min() - 0.5, g.x.max() + 0.5, None]
        ty += [g.threshold.iloc[0]] * 2 + [None]
    fig.add_trace(go.Scatter(x=tx, y=ty, mode="lines", name="Nirikshak threshold (this session)",
                             line=dict(color=ORANGE, width=2), hoverinfo="skip"))
    fig.add_hline(y=0.11, line=dict(color=GRAY, width=1.5), annotation_text="11% rule",
                  annotation_position="top left")
    fig.update_xaxes(tickvals=centers, ticktext=labels, tickangle=0)
    fig.update_yaxes(title="Block QBER", tickformat=".0%", rangemode="tozero")
    return style(fig, height=420, title=dict(text=title, font=dict(size=14)))


def detection_bars(key: pd.DataFrame) -> go.Figure:
    order = list(dict.fromkeys(key.sort_values("session_idx")["condition"]))
    rates = key.groupby("condition")[["alarm", "rule_11"]].mean().reindex(order)
    fig = go.Figure()
    for col, name, color in (("alarm", "Nirikshak", BLUE), ("rule_11", "11% rule", GRAY)):
        fig.add_trace(go.Bar(y=rates.index, x=rates[col], name=name, orientation="h", marker_color=color,
                             text=[f"{v:.0%}" for v in rates[col]], textposition="outside",
                             hovertemplate="%{y}<br>" + name + ": %{x:.0%}<extra></extra>"))
    fig.update_xaxes(range=[0, 1.12], tickformat=".0%", title="Share of blocks flagged")
    fig.update_yaxes(autorange="reversed")
    return style(fig, height=60 + 44 * len(order), barmode="group", bargap=0.35, bargroupgap=0.08)


def worst_case_bars(stress: pd.DataFrame) -> go.Figure:
    honest = stress[stress.condition == "honest (false alarms)"]
    detectors = [c for c in stress.columns if c not in ("test_set", "condition")]
    worst = honest[detectors].max().sort_values()
    fig = go.Figure(go.Bar(
        y=worst.index, x=worst.values, orientation="h",
        marker_color=[BLUE if d == "Nirikshak" else GRAY for d in worst.index],
        text=[f"{v:.0%}" for v in worst.values], textposition="outside",
        customdata=[honest.loc[honest[d].idxmax(), "test_set"] for d in worst.index],
        hovertemplate="%{y}<br>worst false-alarm rate %{x:.0%}<br>on %{customdata}<extra></extra>"))
    fig.add_vline(x=ALPHA, line=dict(color=ORANGE, width=2), annotation_text="5% target",
                  annotation_position="top right")
    fig.update_xaxes(range=[0, 1.05], tickformat=".0%", title="Worst false-alarm rate across all test sets")
    return style(fig, height=320, bargap=0.45, showlegend=False)


@st.cache_data
def run_network(seed: int, alpha: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Verdict per link and hourly window, with what really happened in that window."""
    hw_dir = ROOT / "data" / "hardware"
    records, links = demo_network(hw_dir, seed=seed)
    v = NetworkMonitor(alpha=alpha).run(records).verdict_table()
    v["window"] = v.groupby("link_id").cumcount()
    starts = {sc.link_id: sc.attack_start_h for sc in default_scenarios()}
    labels = hardware_replay_labels(hw_dir)
    truth = []
    for link, w in zip(v.link_id, v.window):
        if link in starts:
            truth.append("attacked" if starts[link] is not None and w >= starts[link] else "honest")
        else:
            r = labels.iloc[w]
            truth.append("honest" if r.attack == "none" else condition(r.attack, r.attacked_fraction, r.strength))
    v["truth"] = truth
    v["start"] = pd.to_datetime(v["t_start"]).dt.floor("h")
    return v, links


def network_grid(v: pd.DataFrame) -> go.Figure:
    links = sorted(v.link_id.unique(), reverse=True)
    starts = sorted(v.start.unique())
    z = np.full((len(links), len(starts)), np.nan)
    text = np.full(z.shape, "", dtype=object)
    for r in v.itertuples():
        i, j = links.index(r.link_id), starts.index(r.start)
        z[i, j] = float(r.alarm)
        text[i, j] = (f"{r.link_id}, {pd.Timestamp(r.start):%d %b %H:%M}<br>verdict: {'ALARM' if r.alarm else 'clean'} "
                      f"(p = {r.p_value:.4f})<br>key QBER {r.key_qber:.2%}, reference {r.ref_qber:.2%}"
                      f"<br>actually: {r.truth}")
    fig = go.Figure(go.Heatmap(z=z, x=[pd.Timestamp(t) for t in starts], y=links, text=text,
                               hovertemplate="%{text}<extra></extra>", xgap=2, ygap=2, showscale=False,
                               colorscale=[[0, GRID], [1, ORANGE]], zmin=0, zmax=1))
    truth = v[v.truth != "honest"]
    fig.add_trace(go.Scatter(x=truth.start, y=truth.link_id, mode="markers", name="window really attacked",
                             marker=dict(symbol="x-thin", size=8, line=dict(width=2, color=SURFACE if DARK else "#1f1f1e")),
                             hoverinfo="skip"))
    return style(fig, height=280, showlegend=True, plot_bgcolor="rgba(0,0,0,0)")


def link_detail(lv: pd.DataFrame) -> tuple[go.Figure, go.Figure]:
    q = go.Figure()
    q.add_trace(go.Scatter(x=lv.start, y=lv.key_qber, name="key blocks", mode="lines+markers",
                           line=dict(color=BLUE, width=2), marker=dict(size=8)))
    q.add_trace(go.Scatter(x=lv.start, y=lv.ref_qber, name="reference blocks", mode="lines+markers",
                           line=dict(color=GRAY, width=2), marker=dict(size=8)))
    q.update_yaxes(tickformat=".1%", rangemode="tozero", title="mean QBER per window")
    b = go.Figure()
    for col, name, color in (("blocks_flagged", "Nirikshak (rolling reference)", BLUE),
                             ("blocks_flagged_frozen", "threshold frozen at commissioning", ORANGE),
                             ("blocks_flagged_11", "11% rule", GRAY)):
        b.add_trace(go.Bar(x=lv.start, y=lv[col], name=name, marker_color=color))
    b.update_yaxes(title="key blocks flagged (of 20)", range=[0, 20.5])
    return style(q, height=300).update_layout(hovermode="x unified"), style(b, height=300, barmode="group", bargap=0.25)


# ---------------------------------------------------------------- page

st.title("Nirikshak")
st.caption("Catching eavesdroppers on real quantum hardware. BB84 on IBM Quantum `ibm_kingston`; "
           f"every detector held to a {ALPHA:.0%} false-alarm budget.")

tab_hw, tab_stress, tab_sim, tab_lessons, tab_net = st.tabs(
    ["Real hardware", "Stress test", "Simulator", "What hardware taught us", "Network monitor"])

with tab_hw:
    batches = load_hardware()
    names = list(batches)
    choice = st.selectbox("Hardware batch", names, index=len(names) - 1)
    key = score(batches[choice])
    honest, attacked = key[~key.is_attack], key[key.is_attack]
    ir = attacked[attacked.attack == "intercept_resend"]
    caught = ir.groupby("attacked_fraction").alarm.mean()
    smallest = next((f for f, r in caught.sort_index().items() if r >= 0.9), None)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Honest QBER", f"{honest.qber.mean():.1%}")
    c2.metric("Nirikshak false alarms", f"{honest.alarm.mean():.0%}", help="Share of honest key blocks flagged")
    c3.metric("Nirikshak catches (90%+ of blocks)",
              f"{round(smallest * 16)} of 16 rounds" if smallest else "none")
    c4.metric("11% rule catches any block from",
              next((f"{round(f * 16)} of 16 rounds" for f, r in ir.groupby("attacked_fraction").rule_11.mean().sort_index().items() if r > 0), "never"))
    if "not matched" in choice:
        st.warning("Batch 1 ran before the timing fix: rounds Eve did not touch picked up extra noise, "
                   "so its detection rates are inflated and not claimed. See 'What hardware taught us'.")
    st.plotly_chart(timeline(key, "Every key block in the batch, in session order"), key="tl_hw")
    st.markdown("**Detection by condition** (honest row = false alarms)")
    st.plotly_chart(detection_bars(key), key="bars_hw")
    st.markdown("**Session verdicts**: one permutation test per session, key blocks vs that session's "
                "reference blocks. Key rate: asymptotic BB84 secret bits per sifted bit (0 = protocol aborts).")
    verdicts = SessionTest(ALPHA).predict_table(batches[choice])
    verdicts["Session"] = [condition(a, f, s) for a, f, s in zip(verdicts.attack, verdicts.attacked_fraction, verdicts.strength)]
    verdicts["Key QBER"] = verdicts.key_mean.map("{:.1%}".format)
    verdicts["Reference QBER"] = verdicts.ref_mean.map("{:.1%}".format)
    verdicts["Key rate"] = bb84_key_rate(verdicts.key_mean.to_numpy()).round(2)
    verdicts["p-value"] = verdicts.p_value.map("{:.4f}".format)
    verdicts["Verdict"] = verdicts.alarm.map({True: "attack", False: "clean"})
    st.dataframe(verdicts[["Session", "Key QBER", "Reference QBER", "Key rate", "p-value", "Verdict"]],
                 width="stretch", hide_index=True)
    with st.expander("Table view"):
        st.dataframe(key.groupby(["session_idx", "condition"]).agg(
            blocks=("qber", "size"), mean_qber=("qber", "mean"), threshold=("threshold", "first"),
            nirikshak=("alarm", "mean"), rule_11=("rule_11", "mean")).reset_index(), width="stretch")

with tab_stress:
    stress = pd.read_csv(ROOT / "results" / "stress_test.csv")
    st.markdown("Detectors trained or calibrated on clean simulation, then tested on shifted noise and "
                "real hardware. Nirikshak calibrates per session on its own reference rounds instead.")
    st.plotly_chart(worst_case_bars(stress), key="worst")
    sets = list(dict.fromkeys(stress.test_set))
    pick = st.selectbox("Test set", sets, index=len(sets) - 1)
    g = stress[stress.test_set == pick].drop(columns="test_set").set_index("condition")
    st.dataframe(g.style.format("{:.0%}"), width="stretch")
    st.caption("Honest row: false-alarm rate (target 5% or less). Other rows: detection rate.")

with tab_sim:
    st.markdown("Run a simulated session pair (honest and attacked) with your own noise level.")
    s1, s2, s3 = st.columns(3)
    attack = s1.selectbox("Attack", ["intercept_resend", "entangling_probe"])
    rounds = s2.slider("Rounds Eve touches (of 16)", 1, 16, 2)
    readout = s3.slider("Readout error", 0.005, 0.06, 0.015, 0.005)

    @st.cache_data(show_spinner="Simulating...")
    def simulate(attack: str, rounds: int, readout: float) -> pd.DataFrame:
        small = dict(key_blocks=20, ref_blocks=20, block_size=4, shots=8)
        nm = simple_noise(readout=readout, readout_1to0=2 * readout)
        parts = [simulate_session(SessionSpec(attack="none", seed=1, **small),
                                  backend=make_simulator(nm), session_id="sim:0"),
                 simulate_session(SessionSpec(attack=attack, fraction=rounds / 16, seed=2, **small),
                                  backend=make_simulator(nm), session_id="sim:1")]
        return pd.concat(parts, ignore_index=True)

    skey = score(simulate(attack, rounds, readout))
    st.plotly_chart(timeline(skey, "Simulated key blocks: honest session, then attacked session"), key="tl_sim")
    a, b = st.columns(2)
    a.metric("Nirikshak: attacked blocks flagged", f"{skey[skey.is_attack].alarm.mean():.0%}")
    b.metric("11% rule: attacked blocks flagged", f"{skey[skey.is_attack].rule_11.mean():.0%}")

with tab_lessons:
    lessons = pd.read_csv(ROOT / "results" / "hardware_lessons.csv")
    st.markdown("Each batch changed one thing. A fair test needs rounds Eve never touched to look "
                "exactly like honest rounds.")
    view = lessons.assign(**{
        "Honest QBER": lessons.honest_qber.map("{:.1%}".format),
        "Honest QBER, X basis": lessons.honest_qber_x.map("{:.1%}".format),
        "Rounds Eve did not touch": [f"{a:.1%} to {b:.1%}" for a, b in zip(lessons.untouched_min, lessons.untouched_max)],
        "Rounds Eve touched": [f"{a:.1%} to {b:.1%}" for a, b in zip(lessons.touched_min, lessons.touched_max)],
    })[["batch", "backend", "timing", "Honest QBER", "Honest QBER, X basis", "Rounds Eve did not touch",
        "Rounds Eve touched", "quantum_seconds", "job_id"]]
    st.dataframe(view.rename(columns={"batch": "Batch", "backend": "Backend", "timing": "Timing", "quantum_seconds": "Quantum s",
                                      "job_id": "IBM job"}), width="stretch", hide_index=True)
    st.markdown("- **Batch 1:** Eve's mid-circuit measurements made every qubit wait; untouched rounds "
                "dephased, inflating detection.\n"
                "- **Batch 2:** every circuit idles for the same slot. Fair, but idling raised honest QBER "
                "to 4% (phase errors).\n"
                "- **Batch 3:** spin echo during the idle. Fair and low: untouched rounds match honest rounds.\n"
                "- **Batches 4-5:** repeats, the second 21 hours later: honest QBER unchanged (1.75%, 1.8%).")


with tab_net:
    st.markdown("**Prototype of Nirikshak as a monitoring layer for a QKD network.** Each link streams "
                "telemetry (per block: sifted rounds and errors, for key rounds and for local reference "
                "rounds). Every hour the monitor gives each link a verdict with a 5% false-alarm budget.")
    st.caption("Links L1-L4 are simulated (binomial error counts with the drift and attacks listed). "
               "L5 replays real ibm_kingston sessions, one per hour, including attacks we ran. "
               "Not real operator data; no operator or network is represented.")
    seed = st.number_input("Simulation seed", 0, 999, 0, help="Re-draws the simulated links L1-L4")
    v, links = run_network(int(seed), ALPHA)
    status = v.sort_values("start").groupby("link_id").tail(1).set_index("link_id")
    cols = st.columns(len(links))
    for c, link in zip(cols, links.itertuples()):
        last = status.loc[link.link_id]
        lv = v[v.link_id == link.link_id]
        c.metric(f"{link.link_id}: {'ALARM' if last.alarm else 'ok'}", f"{int(lv.alarm.sum())} of {len(lv)} windows",
                 help=link.description)
        c.caption(f"{link.description} ({link.source})")
    st.plotly_chart(network_grid(v), width="stretch")
    honest = v[v.truth == "honest"]
    attacked = v[v.truth != "honest"]
    a, b, c = st.columns(3)
    a.metric("Honest windows flagged", f"{honest.alarm.mean():.0%}", help=f"{int(honest.alarm.sum())} of {len(honest)}")
    b.metric("Attacked windows flagged", f"{attacked.alarm.mean():.0%}", help=f"{int(attacked.alarm.sum())} of {len(attacked)}")
    c.metric("Attacked windows over 11% QBER", f"{(attacked.key_qber > 0.11).mean():.0%}")

    pick = st.selectbox("Link detail", list(links.link_id), index=1,
                        format_func=lambda l: f"{l}: {links.set_index('link_id').loc[l, 'description']}")
    q, bars = link_detail(v[v.link_id == pick])
    left, right = st.columns(2)
    left.plotly_chart(q, width="stretch")
    right.plotly_chart(bars, width="stretch")
    st.markdown("A threshold frozen at commissioning drowns in alarms when the link drifts (L2); "
                "Nirikshak re-calibrates on the reference rounds every window, so drift alone stays near 1 "
                "flagged block in 20 while a tap on 1 of 16 rounds (L3) is flagged every hour.")
    st.subheader("Alarm log")
    log = v[v.alarm].sort_values("start", ascending=False)
    st.dataframe(log.assign(**{"window start": log.start.dt.strftime("%d %b %H:%M"),
                               "key QBER": log.key_qber.map("{:.2%}".format),
                               "reference QBER": log.ref_qber.map("{:.2%}".format),
                               "p-value": log.p_value.map("{:.4f}".format)})
                 [["link_id", "window start", "key QBER", "reference QBER", "p-value", "blocks_flagged", "truth"]]
                 .rename(columns={"link_id": "Link", "blocks_flagged": "Blocks flagged", "truth": "Actually"}),
                 width="stretch", hide_index=True)
