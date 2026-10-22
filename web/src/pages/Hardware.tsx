import { useState } from 'react'
import { BlockStrip, DetectionBars, DriftDots } from '../charts/charts'
import { Legend, C } from '../charts/core'
import { ci, fmtTime, pct, pctRange, pretty, pval, timingLabel, useData, type Hardware as HW } from '../data'

export default function Hardware() {
  const d = useData<HW>('hardware')
  const [batchIdx, setBatchIdx] = useState<number | null>(null)
  if (!d) return <div className="loading">Loading results...</div>

  const backends = Object.keys(d.pooled)
  const backend = backends.includes('ibm_kingston') ? 'ibm_kingston' : backends[0]
  const pooled = d.pooled[backend]
  const echo = d.batches.filter((b) => b.timing === 'echo')
  const attacks = pooled.conditions.filter((c) => c.is_attack)
  const smallest = pooled.conditions.find((c) => c.condition === 'intercept 1/16')
  const ruleCaught = attacks.filter((c) => (c.rule.rate ?? 0) >= 0.5).length
  const sel = batchIdx ?? d.batches.indexOf(echo[echo.length - 1])
  const batch = d.batches[sel]
  const hoursSpan = echo.length > 1
    ? (Date.parse(echo[echo.length - 1].submitted!.replace(/(\+\d{2})(\d{2})$/, '$1:$2')) -
       Date.parse(echo[0].submitted!.replace(/(\+\d{2})(\d{2})$/, '$1:$2'))) / 3.6e6
    : 0

  return (
    <>
      <div className="page-head">
        <span className="eyebrow">Real IBM Quantum hardware · {backend}</span>
        <h1>Catching eavesdroppers on real quantum hardware</h1>
        <p className="lede">
          We ran BB84 key exchanges on IBM's {backend}, with and without an eavesdropper, across {echo.length} batches
          over {Math.round(hoursSpan)} hours. Nirikshak compares every session against honest reference rounds measured on
          the same qubits at the same time, so device drift cancels and small attacks stand out.
        </p>
      </div>

      <div className="grid-4">
        <div className="card stat accent">
          <span className="label">Attacked sessions caught</span>
          <span className="value">{pooled.attacked_sessions.k}<small>of {pooled.attacked_sessions.n}</small></span>
          <span className="note">95% interval {ci(pooled.attacked_sessions)}; every p ≤ {pval(pooled.max_attacked_p)}</span>
        </div>
        <div className="card stat">
          <span className="label">Honest sessions flagged</span>
          <span className="value">{pooled.honest_sessions.k}<small>of {pooled.honest_sessions.n}</small></span>
          <span className="note">
            budget 5%; in simulation {pct(d.sim_session_false_alarms.train_honest?.rate)} of {d.sim_session_false_alarms.train_honest?.n} honest sessions
          </span>
        </div>
        <div className="card stat">
          <span className="label">Smallest attack caught</span>
          <span className="value">1<small>of 16 rounds</small></span>
          <span className="note">
            key QBER {smallest ? pctRange(smallest.key_qber[0], smallest.key_qber[1]) : ''}; BB84 would keep making keys
          </span>
        </div>
        <div className="card stat">
          <span className="label">Attacks the 11% rule catches</span>
          <span className="value">{ruleCaught}<small>of {attacks.length}</small></span>
          <span className="note">only Eve on 8 of 16 rounds crosses 11%</span>
        </div>
      </div>

      <section className="section">
        <div className="section-head">
          <h2>Detection per attack</h2>
          <p>
            Share of key blocks flagged, pooled over the spin-echo batches. The session verdict (right) is the decision;
            block alarms show where in a session to look. Whiskers: exact 95% intervals.
          </p>
        </div>
        <div className="grid-2 wide-left">
          <div className="card">
            <div className="card-title">
              <h3>Key blocks flagged</h3>
              <Legend items={[{ label: 'Nirikshak', color: C.s1 }, { label: '11% rule', color: C.neutral }]} />
            </div>
            <DetectionBars rows={pooled.conditions.map((c) => ({
              label: c.condition, note: c.condition === 'honest' ? 'false alarms' : undefined, a: c.nirikshak, b: c.rule,
            }))} />
          </div>
          <div className="card">
            <div className="card-title"><h3>Session verdicts</h3><span className="sub">sessions flagged</span></div>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Condition</th><th className="num">Key QBER</th><th className="num">Key rate</th><th className="num">Flagged</th></tr></thead>
                <tbody>
                  {pooled.conditions.map((c) => (
                    <tr key={c.condition}>
                      <td>{pretty(c.condition)}</td>
                      <td className="num">{pctRange(c.key_qber[0], c.key_qber[1])}</td>
                      <td className="num">{c.key_rate[0] === 0 && c.key_rate[1] === 0 ? '0 (abort)' : `${c.key_rate[0].toFixed(2)}-${c.key_rate[1].toFixed(2)}`}</td>
                      <td className="num">
                        <span className={`badge ${c.is_attack ? (c.sessions.k === c.sessions.n ? 'attack' : 'muted') : 'clean'}`}>
                          {c.sessions.k} of {c.sessions.n}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="note" style={{ marginTop: 12 }}>
              Key rate: asymptotic BB84 secret bits per sifted bit, 1 − 2h(QBER). Above zero, the protocol carries on
              and never reports the eavesdropper.
            </p>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <h2>Inside one batch</h2>
          <p>
            One IBM job, ten sessions. Each column is a session: hollow gray dots are its honest reference blocks, filled
            dots its key blocks that crossed the session's threshold (orange line). The dashed line is the 11% rule.
          </p>
        </div>
        <div className="card">
          <div className="card-title" style={{ alignItems: 'center' }}>
            <div className="seg">
              {d.batches.map((b, i) => (
                <button key={b.job_id} className={i === sel ? 'on' : ''} onClick={() => setBatchIdx(i)}>
                  Batch {b.batch}{b.backend !== backend ? ` (${b.backend.replace('ibm_', '')})` : ''}
                </button>
              ))}
            </div>
            <span className="sub">
              {batch.backend} · {fmtTime(batch.submitted)} · {timingLabel(batch.timing)} · job <span className="mono">{batch.job_id}</span>
            </span>
          </div>
          {batch.timing !== 'echo' && (
            <p className="callout" style={{ marginBottom: 12 }}>
              Not used for claims: {batch.timing === 'none'
                ? 'rounds Eve did not touch waited during her measurements and picked up extra noise.'
                : 'plain idling raised the honest noise floor to 4%. Fixed with a spin echo from batch 3 on.'}
            </p>
          )}
          <Legend items={[
            { label: 'Attacked session, block flagged', color: C.s1, kind: 'dot' },
            { label: 'not flagged', color: C.s1, kind: 'ring' },
            { label: 'Honest session block', color: C.neutral, kind: 'ring' },
            { label: 'Reference block', color: 'var(--text-3)', kind: 'dot' },
            { label: 'Session threshold', color: C.s2, kind: 'line' },
          ]} />
          <div style={{ marginTop: 10 }}>
            <BlockStrip rule={d.rule_11} sessions={batch.sessions.map((s) => ({
              label: s.condition, is_attack: s.is_attack, threshold: s.threshold, key_blocks: s.key_blocks,
              ref_blocks: s.ref_blocks, verdict: s.verdict, p_value: s.p_value,
            }))} />
          </div>
        </div>
      </section>

      <section className="section">
        <div className="grid-2">
          <div className="card">
            <div className="card-title">
              <h3>Honest sessions over time</h3>
              <Legend items={[{ label: 'Key rounds', color: C.s1, kind: 'dot' }, { label: 'Reference rounds', color: C.s2, kind: 'dot' }]} />
            </div>
            <DriftDots groups={echo.map((b) => {
              const h = b.sessions.filter((s) => !s.is_attack)
              return { label: `${b.backend.replace('ibm_', '')} batch ${b.batch}`, sub: fmtTime(b.submitted), key: h.map((s) => s.key_qber), ref: h.map((s) => s.ref_qber) }
            })} />
            <p className="note" style={{ marginTop: 8 }}>
              Reference rounds track key rounds in every session, which is what lets them set the alarm threshold.
            </p>
          </div>
          <div className="card">
            <div className="card-title"><h3>What the hardware taught us</h3></div>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Batch</th><th>Timing</th><th className="num">Honest QBER</th><th className="num">Untouched rounds</th></tr></thead>
                <tbody>
                  {d.batches.map((b) => (
                    <tr key={b.job_id}>
                      <td>{b.batch}{b.backend !== backend ? ` (${b.backend})` : ''}</td>
                      <td>{b.timing === 'echo' ? 'spin echo' : b.timing === 'delay' ? 'plain idle' : 'not matched'}</td>
                      <td className="num">{pct(b.honest_qber, 1)}</td>
                      <td className="num">{b.untouched[0] != null ? pctRange(b.untouched[0], b.untouched[1]) : ''}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="note" style={{ marginTop: 12 }}>
              Batch 1: Eve's mid-circuit measurements made every qubit wait, so rounds she never touched got noisier,
              which inflated detection. Batch 2: equal timing for every circuit, but idling dephased the qubits. From
              batch 3: a spin echo during the wait. Untouched rounds now match honest ones.
            </p>
          </div>
        </div>
      </section>
    </>
  )
}

