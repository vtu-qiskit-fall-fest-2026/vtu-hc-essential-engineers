import { useState } from 'react'
import { BlockStrip } from '../charts/charts'
import { C, Legend } from '../charts/core'
import { Verdict } from '../components/ui'
import { pct, useData, type Simulator } from '../data'

export default function How() {
  const d = useData<Simulator>('simulator')
  const [ri, setRi] = useState(1)
  const [ki, setKi] = useState(2)

  return (
    <>
      <section className="hero">
        <div className="hero-top">
          <h1 className="statement">Noisier than today's normal?</h1>
          <p className="prose">
            BB84 reveals an eavesdropper through errors, but hardware makes errors too, and its noise drifts. A fixed line
            either misses a careful eavesdropper or raises alarms whenever the device drifts. Nirikshak measures today's
            normal on the same qubits, in the same run, and asks whether the key rounds are noisier than that.
          </p>
        </div>
        <div className="process">
          <div><span className="step"><span>1</span>Key rounds</span>
            <p>Alice sends random bits in random bases and Bob measures in random bases. Eve may intercept some rounds.
              Rounds where the bases match are kept; their error rate is the QBER.</p></div>
          <div><span className="step"><span>2</span>Reference rounds</span>
            <p>In the same job, on the same qubits, an honest calibration circuit runs with no channel and no slot for Eve.
              She cannot touch it, but it sees the same device noise and drift.</p></div>
          <div><span className="step"><span>3</span>Threshold from today</span>
            <p>Split-conformal calibration on the reference blocks sets each session's threshold, so honest blocks cross it
              about 5% of the time at any noise level.</p></div>
          <div><span className="step"><span>4</span>Session verdict</span>
            <p>A permutation test asks whether the key blocks are noisier than the reference blocks. Honest sessions are
              flagged at most 5% of the time; pooling 20 blocks catches attacks no single block shows.</p></div>
        </div>
      </section>

      <section className="finding">
        <div className="gutter">
          <h2 className="title">Try it</h2>
          <p className="note">Simulated sessions from Qiskit Aer, computed in advance. Choose the device noise and how many
            of the 16 rounds per shot Eve intercepts. The 11% rule reacts to the total; Nirikshak reacts to the gap
            between key and reference rounds.</p>
        </div>
        <div className="body">{!d ? null : (() => {
          const cell = d.grid.find((g) => g.readout === d.readouts[ri] && g.rounds === d.rounds[ki])!
          const honest = d.grid.find((g) => g.readout === d.readouts[ri] && g.rounds === 0)!
          const yMax = Math.max(0.12, ...d.grid.filter((g) => g.readout === d.readouts[ri]).flatMap((g) => g.key_blocks)) * 1.05
          return (
            <div className="split">
              <div className="plate" style={{ display: 'grid', gap: 14 }}>
                <div className="controls">
                  <div className="control"><span>Device readout error</span>
                    <div className="seg">{d.readouts.map((r, i) => <button key={r} className={i === ri ? 'on' : ''} onClick={() => setRi(i)}>{pct(r, 1)}</button>)}</div>
                  </div>
                  <div className="control"><span>Rounds Eve intercepts (of 16)</span>
                    <div className="seg">{d.rounds.map((k, i) => <button key={k} className={i === ki ? 'on' : ''} onClick={() => setKi(i)}>{k === 0 ? 'none' : k}</button>)}</div>
                  </div>
                </div>
                <Legend items={[
                  { label: 'Key block, flagged', color: C.s1, kind: 'dot' },
                  { label: 'Honest key block', color: C.neutral, kind: 'ring' },
                  { label: 'Reference block', color: 'var(--text-3)', kind: 'dot' },
                  { label: 'Session threshold', color: C.s2, kind: 'line' },
                ]} />
                <BlockStrip height={320} yMax={yMax} sessions={[
                  { label: 'honest session', is_attack: false, threshold: honest.threshold, key_blocks: honest.key_blocks, ref_blocks: honest.ref_blocks, verdict: honest.verdict, p_value: honest.p_value },
                  ...(cell.rounds ? [{ label: `Eve on ${cell.rounds} of 16`, is_attack: true, threshold: cell.threshold, key_blocks: cell.key_blocks, ref_blocks: cell.ref_blocks, verdict: cell.verdict, p_value: cell.p_value }] : []),
                ]} />
              </div>
              <div className="plate" style={{ display: 'grid', gap: 14, alignContent: 'start' }}>
                <h3 className="subtitle">{cell.rounds ? `Eve on ${cell.rounds} of 16 rounds` : 'No eavesdropper'}</h3>
                <table>
                  <tbody>
                    <tr><td>Key QBER</td><td className="num"><b>{pct(cell.key_qber, 2)}</b></td></tr>
                    <tr><td>Reference QBER</td><td className="num">{pct(cell.ref_qber, 2)}</td></tr>
                    <tr><td>BB84 key rate</td><td className="num">{cell.key_rate === 0 ? '0 (abort)' : cell.key_rate.toFixed(2)}</td></tr>
                    <tr><td>11% rule, blocks flagged</td><td className="num">{cell.blocks_rule} of 20</td></tr>
                    <tr><td>Nirikshak, blocks flagged</td><td className="num">{cell.blocks_flagged} of 20</td></tr>
                    <tr><td>Session verdict</td><td className="num"><Verdict alarm={cell.verdict} p={cell.p_value} /></td></tr>
                  </tbody>
                </table>
                <p className="note">
                  {cell.rounds === 0
                    ? 'Honest: key and reference rounds see the same noise, so the verdict stays clean even at high noise.'
                    : cell.key_rate > 0
                      ? 'The key rate is still positive: BB84 would carry on making keys and never report Eve.'
                      : 'Above 11%: BB84 itself would abort. Small attacks are the ones that need Nirikshak.'}
                </p>
              </div>
            </div>
          )
        })()}</div>
      </section>

      <section className="finding">
        <div className="gutter">
          <h2 className="title">Where 11% comes from</h2>
        </div>
        <div className="body">
          <p className="prose">
            It is the Shor-Preskill limit for distilling any secret key: the BB84 key rate 1 − 2h(QBER) reaches zero at
            11%. Below it, privacy amplification can still protect an ideal key, but the operator never learns that the
            link is being tapped, cannot locate the tap, and cannot tell an attack from drift. Nirikshak is that missing
            intrusion-detection layer.
          </p>
        </div>
      </section>
    </>
  )
}
