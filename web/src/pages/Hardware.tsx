import { Fragment, useState } from 'react'
import { BlockStrip, DetectionBars, DriftDots } from '../charts/charts'
import { C, Legend } from '../charts/core'
import { QberRuler } from '../charts/ruler'
import { fmtTime, pct, pctRange, pretty, pval, timingLabel, useData, type Hardware as HW, type HwSession } from '../data'

const mean = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / xs.length
const minmax = (xs: number[]): [number, number] => [Math.min(...xs), Math.max(...xs)]

function Glyph({ hit }: { hit: boolean }) {
  return hit
    ? <svg width="11" height="11" viewBox="0 0 10 10" aria-label="flagged"><path d="M5 1 L9.5 9 H0.5 Z" fill="var(--alarm)" /></svg>
    : <svg width="11" height="11" viewBox="0 0 10 10" aria-label="clean"><circle cx="5" cy="5" r="3.6" fill="none" stroke="var(--ink-3)" strokeWidth="1.5" /></svg>
}

export default function Hardware() {
  const d = useData<HW>('hardware')
  const [batchIdx, setBatchIdx] = useState<number | null>(null)
  if (!d) return null

  const backend = Object.keys(d.pooled).includes('ibm_kingston') ? 'ibm_kingston' : Object.keys(d.pooled)[0]
  const pooled = d.pooled[backend]
  const echo = d.batches.filter((b) => b.timing === 'echo' && b.backend === backend)
  const sessions = echo.flatMap((b) => b.sessions)
  const honest = sessions.filter((s) => !s.is_attack)
  const sel = batchIdx ?? d.batches.indexOf(echo[echo.length - 1])
  const batch = d.batches[sel]
  const iso = (s: string) => s.replace(/(\+\d{2})(\d{2})$/, '$1:$2')
  const hoursSpan = (Date.parse(iso(echo[echo.length - 1].submitted!)) - Date.parse(iso(echo[0].submitted!))) / 3.6e6
  const qseconds = echo.reduce((a, b) => a + (b.quantum_seconds ?? 0), 0)

  const marks = [1, 2, 4, 8].map((k) => {
    const c = pooled.conditions.find((x) => x.condition === `intercept ${k}/16`)!
    const ss = sessions.filter((s) => s.condition === `intercept ${k}/16`)
    return {
      rounds: k, qber: mean(ss.map((s) => s.key_qber)),
      caught: `${c.sessions.k} of ${c.sessions.n} sessions`,
      rule: c.rule.k === 0 ? 'never' : `${pct(c.rule.rate)} of blocks`,
    }
  })
  const bySession = (cond: string, b: (typeof echo)[number]): HwSession[] => b.sessions.filter((s) => s.condition === cond)

  return (
    <>
      <section className="hero">
        <div className="hero-top">
        <h1 className="statement">Eve stays far below 11%. Nirikshak still catches her.</h1>
        <p className="prose">
          We ran BB84 on IBM's {backend} with and without an eavesdropper, in {echo.length} batches across{' '}
          {Math.round(hoursSpan)} hours. Each blue marker is a real intercept attack, placed at the error rate it caused.
          BB84 only stops at 11%. Nirikshak compares every session with honest reference rounds measured on the same
          qubits at the same time, so it reacts to anything above today's normal.
        </p>
        </div>
        <QberRuler marks={marks} rule={d.rule_11}
          honest={minmax(honest.map((s) => s.key_qber))}
          reference={minmax(sessions.map((s) => s.ref_qber))} />
      </section>

      <section className="finding">
        <div className="gutter">
          <h2 className="title">Every attacked session flagged</h2>
          <dl className="facts">
            <div><dt>Backend</dt><dd>{backend} (Heron r2)</dd></div>
            <div><dt>Batches</dt><dd>{echo.map((b) => b.batch).join(', ')}, from {fmtTime(echo[0].submitted)} to {fmtTime(echo[echo.length - 1].submitted)}</dd></div>
            <div><dt>Sessions</dt><dd>{sessions.length}, each 20 key and 20 reference blocks</dd></div>
            <div><dt>Quantum time</dt><dd>{qseconds} s</dd></div>
          </dl>
        </div>
        <div className="body">
          <p className="tally">
            <span className="n key">{pooled.attacked_sessions.k} of {pooled.attacked_sessions.n}</span> attacked sessions
            flagged, each with p ≤ {pval(pooled.max_attacked_p)}.{' '}
            <span className="n">{pooled.honest_sessions.k} of {pooled.honest_sessions.n}</span> honest sessions flagged,
            against a budget of 5%; on {d.sim_session_false_alarms.train_honest?.n} simulated honest sessions the rate
            was {pct(d.sim_session_false_alarms.train_honest?.rate)}.
          </p>
          <div className="plate">
            <div className="table-wrap"><div className="matrix" style={{ ['--cols' as string]: echo.length }}>
              <div className="mh">Session</div>
              {echo.map((b) => <div className="mh" key={b.job_id}>Batch {b.batch}, {fmtTime(b.submitted, false)}</div>)}
              <div className="mh end">BB84 key rate</div>
              {pooled.conditions.map((c) => (
                <Fragment key={c.condition}>
                  <div className="cond">{pretty(c.condition)}</div>
                  {echo.map((b) => {
                    const ss = bySession(c.condition, b)
                    const hit = ss.some((s) => s.verdict)
                    return (
                      <div key={b.job_id} className={`cell ${hit ? 'hit' : ''}`}
                        title={ss.map((s) => `p = ${pval(s.p_value)}`).join(', ')}>
                        <span className="glyphs">{ss.map((s) => <Glyph key={s.session} hit={s.verdict} />)}</span>
                        {ss.length === 1 && <span>p {pval(ss[0].p_value)}</span>}
                      </div>
                    )
                  })}
                  <div className="end">{c.key_rate[1] === 0 ? '0, aborts' : `${c.key_rate[0].toFixed(2)}-${c.key_rate[1].toFixed(2)}`}</div>
                </Fragment>
              ))}
            </div></div>
            <p className="note" style={{ marginTop: 14 }}>
              Red triangle: session verdict attack (one-sided permutation test of key blocks against the session's own
              reference blocks, 5% budget). Circle: clean. Key rate is the asymptotic BB84 rate 1 − 2h(QBER); above
              zero, BB84 keeps making keys and never reports Eve.
            </p>
          </div>
        </div>
      </section>

      <section className="finding">
        <div className="gutter">
          <h2 className="title">Which blocks gave Eve away</h2>
          <p className="note">
            A block is 8 random settings of 16 rounds, about 512 sifted bits. Each key block is compared with a threshold
            set from that session's 20 reference blocks. Bars pool the three batches; whiskers are exact 95% intervals.
          </p>
        </div>
        <div className="body">
          <div className="plate">
            <div className="plate-head">
              <span className="subtitle">Key blocks flagged</span>
              <Legend items={[{ label: 'Nirikshak', color: C.s1 }, { label: '11% rule', color: C.neutral }]} />
            </div>
            <DetectionBars rows={pooled.conditions.map((c) => ({
              label: c.condition, note: c.condition === 'honest' ? 'false alarms' : undefined, a: c.nirikshak, b: c.rule,
            }))} />
          </div>
        </div>
      </section>

      <section className="finding">
        <div className="gutter">
          <h2 className="title">Inside one batch</h2>
          <dl className="facts">
            <div><dt>IBM job</dt><dd>{batch.job_id}</dd></div>
            <div><dt>Backend</dt><dd>{batch.backend}</dd></div>
            <div><dt>Submitted</dt><dd>{fmtTime(batch.submitted)}</dd></div>
            <div><dt>Timing</dt><dd>{timingLabel(batch.timing)}</dd></div>
            <div><dt>Honest QBER</dt><dd>{pct(batch.honest_qber, 2)}</dd></div>
          </dl>
          {batch.timing !== 'echo' && (
            <p className="note">
              Not used for any claim: {batch.timing === 'none'
                ? 'rounds Eve never touched waited during her measurements and picked up extra noise.'
                : 'plain idling raised the honest noise floor to 4%. A spin echo fixed it from batch 3.'}
            </p>
          )}
        </div>
        <div className="body">
          <div className="seg" role="tablist">
            {d.batches.map((b, i) => (
              <button key={b.job_id} role="tab" aria-selected={i === sel} className={i === sel ? 'on' : ''} onClick={() => setBatchIdx(i)}>
                Batch {b.batch}{b.backend !== backend ? `, ${b.backend.replace('ibm_', '')}` : ''}
              </button>
            ))}
          </div>
          <div className="plate">
            <Legend items={[
              { label: 'Attacked session: flagged block', color: C.s1, kind: 'dot' },
              { label: 'unflagged block', color: C.s1, kind: 'ring' },
              { label: 'Honest session block', color: C.neutral, kind: 'ring' },
              { label: 'Reference block', color: 'var(--ink-3)', kind: 'dot' },
              { label: "Session's threshold", color: C.s2, kind: 'line' },
            ]} />
            <div style={{ marginTop: 10 }}>
              <BlockStrip rule={d.rule_11} sessions={batch.sessions.map((s) => ({
                label: s.condition, is_attack: s.is_attack, threshold: s.threshold, key_blocks: s.key_blocks,
                ref_blocks: s.ref_blocks, verdict: s.verdict, p_value: s.p_value,
              }))} />
            </div>
          </div>
        </div>
      </section>

      <section className="finding">
        <div className="gutter">
          <h2 className="title">The hardware's normal, and what it taught us</h2>
          <p className="note">
            Reference rounds sat within 0.2 points of honest key rounds in every session, across {Math.round(hoursSpan)} hours.
            Getting there took two failed batches.
          </p>
        </div>
        <div className="body split even">
          <div className="plate">
            <div className="plate-head">
              <span className="subtitle">Honest sessions over time</span>
              <Legend items={[{ label: 'Key rounds', color: C.s1, kind: 'dot' }, { label: 'Reference rounds', color: C.s2, kind: 'dot' }]} />
            </div>
            <DriftDots groups={echo.map((b) => {
              const h = b.sessions.filter((s) => !s.is_attack)
              return { label: `Batch ${b.batch}`, sub: fmtTime(b.submitted), key: h.map((s) => s.key_qber), ref: h.map((s) => s.ref_qber) }
            })} />
          </div>
          <div className="plate">
            <span className="subtitle">Timing between preparation and measurement</span>
            <div className="table-wrap" style={{ marginTop: 10 }}>
              <table>
                <thead><tr><th>Batch</th><th>Idle qubits</th><th className="num">Honest</th><th className="num">Rounds Eve skipped</th></tr></thead>
                <tbody>
                  {d.batches.map((b) => (
                    <tr key={b.job_id}>
                      <td>{b.batch}{b.backend !== backend ? `, ${b.backend}` : ''}</td>
                      <td>{b.timing === 'echo' ? 'spin echo' : b.timing === 'delay' ? 'plain wait' : 'unmatched'}</td>
                      <td className="num">{pct(b.honest_qber, 1)}</td>
                      <td className="num">{b.untouched[0] != null ? pctRange(b.untouched[0], b.untouched[1]) : ''}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="note" style={{ marginTop: 12 }}>
              In batch 1 Eve's mid-circuit measurements made every qubit wait, so rounds she never touched got noisier
              and detection looked better than it was. Batch 2 gave every circuit the same wait, but idling dephased the
              qubits. From batch 3 a spin echo fills the wait, and rounds Eve skips look like honest rounds.
            </p>
          </div>
        </div>
      </section>
    </>
  )
}
