import { useState } from 'react'
import { HeatTable, WorstBars } from '../charts/charts'
import { useData, type Stress as S } from '../data'

const rowLabel = (t: string) => t
  .replace('sim: training conditions', 'Simulation, training noise')
  .replace('sim: drifted noise', 'Simulation, drifted noise')
  .replace('sim: Kingston noise snapshot', 'Simulation, Kingston snapshot')
  .replace(/^hardware: (\S+) batch (\d+) \((.*)\)$/, (_m, b, n, t) =>
    `${b.replace('ibm_', '')} batch ${n}, ${/NOT/.test(t) ? 'timing unmatched' : /plain/.test(t) ? 'plain wait' : 'spin echo'}`)

const short = (t: string) => t.replace('hardware: ', '').replace(/ \(timing.*\)$/, '').replace('sim: ', 'simulation, ')
  .replace(/ \((timing )?NOT matched\)/, '')

export default function Stress() {
  const d = useData<S>('stress')
  const [cond, setCond] = useState<string | null>(null)
  if (!d) return null

  const conditions = Array.from(new Set(d.rows.map((r) => r.condition))).filter((c) => !c.startsWith('honest'))
  const selCond = cond ?? conditions.find((c) => c.includes('1/16')) ?? conditions[0]
  const worst = [...d.worst_false_alarms].sort((a, b) => b.rate - a.rate)
  const get = (condition: string) => (set: string, det: string) =>
    d.rows.find((r) => r.test_set === set && r.condition === condition)?.rates[det]
  const honestCond = d.rows.find((r) => r.condition.startsWith('honest'))!.condition
  const nk = worst.find((w) => w.detector === 'Nirikshak')

  return (
    <>
      <section className="hero">
        <div className="hero-top">
          <h1 className="statement">Trained in simulation, lost on real noise.</h1>
          <p className="prose">
            Every detector here except Nirikshak learns from simulated BB84 data and is tuned for 5% false alarms. We then
            test them all on drifted simulation, a Kingston noise snapshot and every hardware batch. When the noise moves,
            the trained detectors flag most honest blocks. Nirikshak has nothing to retrain: it recalibrates on each
            session's own reference rounds.
          </p>
        </div>
      </section>

      <section className="finding">
        <div className="gutter">
          <h2 className="title">Worst case outside training</h2>
          <p className="note">Share of honest blocks flagged on the worst test set, excluding the training conditions.</p>
        </div>
        <div className="body">
          <div className="plate">
            <WorstBars budget={d.alpha} highlight="Nirikshak"
              rows={worst.map((w) => ({ label: w.detector, value: w.rate, where: short(w.where) }))} />
          </div>
          {nk && (
            <p className="note">
              Nirikshak's worst case, {Math.round(nk.rate * 100)}% on {short(nk.where)}, is 8 of 60 honest blocks spread
              over 3 sessions, and all 3 got a clean session verdict. A block threshold rests on only 20 reference blocks,
              so it varies from session to session; the session verdict keeps its 5% budget.
            </p>
          )}
        </div>
      </section>

      <section className="finding">
        <div className="gutter">
          <h2 className="title">False alarms, every test set</h2>
          <p className="note">Share of honest blocks flagged. Deeper red is worse.</p>
        </div>
        <div className="body">
          <div className="plate"><HeatTable rows={d.test_sets} cols={d.detectors} value={get(honestCond)} good="low" rowLabel={rowLabel} /></div>
        </div>
      </section>

      <section className="finding">
        <div className="gutter">
          <h2 className="title">Detection, every test set</h2>
          <p className="note">Share of attacked blocks flagged; deeper red means more missed. Where noise matches training
            the trained detectors catch slightly more per block. Elsewhere they either flag everything or miss small attacks.</p>
        </div>
        <div className="body">
          <div className="seg">
            {conditions.map((c) => <button key={c} className={c === selCond ? 'on' : ''} onClick={() => setCond(c)}>{c}</button>)}
          </div>
          <div className="plate"><HeatTable rows={d.test_sets} cols={d.detectors} value={get(selCond)} good="high" rowLabel={rowLabel} /></div>
        </div>
      </section>
    </>
  )
}
