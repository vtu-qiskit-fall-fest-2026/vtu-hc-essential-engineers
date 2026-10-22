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
      <div className="page-head">
        <span className="eyebrow">How it works</span>
        <h1>Ask "noisier than today's normal?", not "above 11%?"</h1>
        <p className="lede">
          BB84 reveals an eavesdropper through errors, but hardware makes errors too, and its noise drifts. A fixed
          threshold either misses a careful eavesdropper or cries wolf when the device drifts. Nirikshak measures
          today's normal on the same qubits, in the same run, and compares against that.
        </p>
      </div>

      <div className="steps">
        <div className="card"><span className="num">01</span><h3>Key rounds</h3>
          <p>Alice sends random bits in random bases; Bob measures in random bases. Eve may intercept some rounds. Rounds
            where the bases match are kept; their error rate is the QBER.</p></div>
        <div className="card"><span className="num">02</span><h3>Reference rounds</h3>
          <p>In the same job, on the same qubits, an honest calibration circuit runs with no channel and no attack slot.
            Eve cannot touch it, but it sees the same device noise and drift.</p></div>
        <div className="card"><span className="num">03</span><h3>Threshold from today</h3>
          <p>Split-conformal calibration on the reference blocks sets each session's alarm threshold, so honest blocks
            cross it about 5% of the time, whatever the noise level.</p></div>
        <div className="card"><span className="num">04</span><h3>Session verdict</h3>
          <p>A permutation test asks whether the key blocks are noisier than the reference blocks. Under no attack it
            fires in at most 5% of sessions; pooling 20 blocks catches attacks no single block shows.</p></div>
      </div>

      <section className="section">
        <div className="section-head">
          <h2>Try it</h2>
          <p>Precomputed simulated sessions (Qiskit Aer). Pick the device noise and how many of the 16 rounds per shot Eve
            intercepts. The 11% rule only reacts to the total; Nirikshak reacts to the gap between key and reference.</p>
        </div>
        {!d ? <div className="loading">Loading simulator...</div> : (() => {
          const cell = d.grid.find((g) => g.readout === d.readouts[ri] && g.rounds === d.rounds[ki])!
          const honest = d.grid.find((g) => g.readout === d.readouts[ri] && g.rounds === 0)!
          const yMax = Math.max(0.12, ...d.grid.filter((g) => g.readout === d.readouts[ri]).flatMap((g) => g.key_blocks)) * 1.05
          return (
            <div className="grid-2 wide-left">
              <div className="card" style={{ display: 'grid', gap: 14 }}>
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
              <div className="card" style={{ display: 'grid', gap: 14, alignContent: 'start' }}>
                <h3>{cell.rounds ? `Eve on ${cell.rounds} of 16 rounds` : 'No eavesdropper'}</h3>
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
        })()}
      </section>

      <section className="section">
        <div className="section-head">
          <h2>Where the 11% comes from</h2>
          <p>
            It is the Shor-Preskill limit for distilling any secret key: the BB84 key rate 1 − 2h(QBER) reaches zero at
            11%. Below it, privacy amplification can still protect an ideal key, but the operator never learns the link
            is being tapped, cannot locate it, and cannot tell an attack from drift. Nirikshak is that missing
            intrusion-detection layer.
          </p>
        </div>
      </section>
    </>
  )
}
