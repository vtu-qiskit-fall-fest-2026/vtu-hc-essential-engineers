import { useState } from 'react'
import { HeatTable, WorstBars } from '../charts/charts'
import { useData, type Stress as S } from '../data'

const short = (t: string) => t.replace('hardware: ', '').replace(/ \(timing.*\)$/, '').replace('sim: ', 'simulation, ')
  .replace(/ \((timing )?NOT matched\)/, '')

export default function Stress() {
  const d = useData<S>('stress')
  const [cond, setCond] = useState<string | null>(null)
  if (!d) return <div className="loading">Loading stress test...</div>

  const conditions = Array.from(new Set(d.rows.map((r) => r.condition))).filter((c) => !c.startsWith('honest'))
  const selCond = cond ?? conditions.find((c) => c.includes('1/16')) ?? conditions[0]
  const worst = [...d.worst_false_alarms].sort((a, b) => b.rate - a.rate)
  const get = (condition: string) => (set: string, det: string) =>
    d.rows.find((r) => r.test_set === set && r.condition === condition)?.rates[det]
  const honestCond = d.rows.find((r) => r.condition.startsWith('honest'))!.condition
  const nk = worst.find((w) => w.detector === 'Nirikshak')

  return (
    <>
      <div className="page-head">
        <span className="eyebrow">Simulation to hardware stress test</span>
        <h1>Detectors trained in simulation break on real noise</h1>
        <p className="lede">
          Every detector here except Nirikshak is trained or calibrated on simulated BB84 data for 5% false alarms,
          then tested on drifted simulation, a Kingston noise snapshot and every hardware batch. When the noise moves,
          the simulation-trained detectors flag most honest blocks. Nirikshak recalibrates on each session's own
          reference rounds.
        </p>
      </div>

      <div className="card">
        <div className="card-title">
          <h3>Worst-case false alarms outside training conditions</h3>
          <span className="sub">share of honest blocks flagged, worst test set</span>
        </div>
        <WorstBars budget={d.alpha} highlight="Nirikshak"
          rows={worst.map((w) => ({ label: w.detector, value: w.rate, where: short(w.where) }))} />
        {nk && (
          <p className="note" style={{ marginTop: 10 }}>
            Nirikshak's worst case ({Math.round(nk.rate * 100)}%, {short(nk.where)}) is per block: 8 of 60 honest blocks
            spread over 3 sessions, all of which got a clean session verdict. Block thresholds rest on 20 reference
            blocks, so they vary between sessions; the session verdict keeps its 5% budget.
          </p>
        )}
      </div>

      <section className="section">
        <div className="section-head">
          <h2>False alarms on every test set</h2>
          <p>Share of honest blocks flagged. Darker is worse.</p>
        </div>
        <div className="card">
          <HeatTable rows={d.test_sets} cols={d.detectors} value={get(honestCond)} good="low" />
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <h2>Detection on every test set</h2>
          <p>Share of attacked blocks flagged. Darker means more missed. When noise matches training, the simulation-trained
            detectors detect slightly more per block; elsewhere they either drown in false alarms or miss small attacks.</p>
        </div>
        <div className="card" style={{ display: 'grid', gap: 14 }}>
          <div className="seg">
            {conditions.map((c) => <button key={c} className={c === selCond ? 'on' : ''} onClick={() => setCond(c)}>{c}</button>)}
          </div>
          <HeatTable rows={d.test_sets} cols={d.detectors} value={get(selCond)} good="high" />
        </div>
      </section>
    </>
  )
}
