import { useEffect, useMemo, useState } from 'react'
import { LinkTrace, MonitorGrid, type GridCell } from '../charts/charts'
import { C, Legend } from '../charts/core'
import { Verdict as VerdictBadge } from '../components/ui'
import { pct, pval, useData, type Monitor as M } from '../data'

const hh = (h: number) => `${String(Math.floor(h) % 24).padStart(2, '0')}:00`
const day = (h: number) => (h >= 24 ? ' (+1 day)' : '')

export default function Monitor() {
  const d = useData<M>('monitor')
  const hours = useMemo(() => (d ? Math.max(...d.verdicts.map((v) => v.window)) + 1 : 0), [d])
  const [upto, setUpto] = useState<number | null>(null)
  const [playing, setPlaying] = useState(false)
  const [pick, setPick] = useState('L3')

  const now = upto ?? hours
  useEffect(() => {
    if (!playing) return
    const id = setInterval(() => {
      setUpto((u) => {
        const next = (u ?? 0) + 1
        if (next >= hours) { setPlaying(false); return hours }
        return next
      })
    }, 550)
    return () => clearInterval(id)
  }, [playing, hours])

  if (!d) return <div className="loading">Loading monitor...</div>

  const links = d.links.map((l) => l.link_id)
  const cells: GridCell[] = d.verdicts.map((v) => ({
    link: v.link_id, h: v.window, alarm: v.alarm, truth: v.truth, p: v.p_value, key: v.key_qber, ref: v.ref_qber,
    label: `${hh(v.window)}-${hh(v.window + 1)}${day(v.window)}`,
  }))
  const seen = d.verdicts.filter((v) => v.window < now)
  const honest = d.verdicts.filter((v) => v.truth === 'honest')
  const attacked = d.verdicts.filter((v) => v.truth !== 'honest')
  const l2 = d.verdicts.filter((v) => v.link_id === 'L2')
  const avg = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / Math.max(xs.length, 1)
  const b = d.blocks[pick]
  const linkInfo = d.links.find((l) => l.link_id === pick)!
  const feed = seen.filter((v) => v.alarm).sort((a, b2) => b2.window - a.window || a.link_id.localeCompare(b2.link_id))

  return (
    <>
      <div className="page-head">
        <span className="eyebrow">Prototype · monitoring layer for a QKD network</span>
        <h1>One verdict per link, every hour</h1>
        <p className="lede">
          Each link streams a few numbers per block: how many sifted rounds, how many errors, for key rounds and for
          local reference rounds that never cross the channel. Nirikshak turns that into an hourly verdict with a 5%
          false-alarm budget, whatever the link's noise is doing.
        </p>
        <p className="note">
          Links L1-L4 are simulated. L5 replays real ibm_kingston sessions, one per hour, including attacks we ran
          ourselves. No real operator, network or traffic is represented.
        </p>
      </div>

      <div className="card" style={{ display: 'grid', gap: 16 }}>
        <div className="controls">
          <button className="btn primary" onClick={() => {
            if (playing) return setPlaying(false)
            if (now >= hours) setUpto(0)
            setPlaying(true)
          }}>
            <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden>
              {playing ? <><rect x="2" y="1" width="3" height="10" fill="currentColor" /><rect x="7" y="1" width="3" height="10" fill="currentColor" /></>
                : <path d="M2 1 L11 6 L2 11 Z" fill="currentColor" />}
            </svg>
            {playing ? 'Pause' : now >= hours ? 'Replay the day' : 'Play'}
          </button>
          <label className="control" style={{ flex: 1, minWidth: 200 }}>
            <span>Time · {now >= hours ? `all ${hours} hours` : `${hh(now)}${day(now)}`}</span>
            <input type="range" min={0} max={hours} value={now} onChange={(e) => { setPlaying(false); setUpto(+e.target.value) }} />
          </label>
        </div>

        <div className="grid-4" style={{ gridTemplateColumns: `repeat(auto-fit, minmax(170px, 1fr))` }}>
          {d.links.map((l) => {
            const lv = seen.filter((v) => v.link_id === l.link_id)
            const last = lv[lv.length - 1]
            return (
              <button key={l.link_id} className={`card link-card ${last?.alarm ? 'alarm' : ''}`}
                style={{ textAlign: 'left', cursor: 'pointer', font: 'inherit', color: 'inherit', outline: pick === l.link_id ? '2px solid var(--series-1)' : undefined }}
                onClick={() => setPick(l.link_id)}>
                <div className="row">
                  <span className="id">{l.link_id}</span>
                  {last ? <VerdictBadge alarm={last.alarm} /> : <span className="badge muted">waiting</span>}
                </div>
                <span className="desc">{l.description}</span>
                <div className="row">
                  <span className="src">{l.source}</span>
                  <span className="note">{lv.filter((v) => v.alarm).length} of {lv.length} alarms</span>
                </div>
              </button>
            )
          })}
        </div>

        <div>
          <div className="card-title">
            <h3>Verdicts by link and hour</h3>
            <Legend items={[
              { label: 'Alarm', color: 'var(--critical)' },
              { label: 'Clean', color: 'var(--surface-2)' },
              { label: 'Window really attacked', color: 'var(--text)', kind: 'line' },
            ]} />
          </div>
          <MonitorGrid links={links} hours={hours} cells={cells} upto={now} onPick={setPick} />
        </div>
      </div>

      <section className="section">
        <div className="grid-2 wide-left">
          <div className="card">
            <div className="card-title">
              <h3>{pick}: {linkInfo.description}</h3>
              <div className="seg">
                {links.map((l) => <button key={l} className={l === pick ? 'on' : ''} onClick={() => setPick(l)}>{l}</button>)}
              </div>
            </div>
            <Legend items={[
              { label: 'Key block, flagged', color: C.s1, kind: 'dot' },
              { label: 'Key block', color: 'var(--text-3)', kind: 'dot' },
              { label: "Nirikshak's threshold (last 20 reference blocks)", color: C.s2, kind: 'line' },
              { label: 'Threshold frozen at commissioning', color: C.neutral, kind: 'dash' },
              { label: 'Attacked hours', color: 'var(--critical-soft)' },
            ]} />
            <div style={{ marginTop: 8 }}>
              <LinkTrace h={b.h} qber={b.qber} threshold={b.threshold} alarm={b.alarm} frozen={b.frozen_threshold}
                hours={Math.max(...d.verdicts.filter((v) => v.link_id === pick).map((v) => v.window)) + 1} upto={now} attacked={d.verdicts.filter((v) => v.link_id === pick && v.truth !== 'honest').map((v) => v.window)} />
            </div>
          </div>
          <div className="card">
            <div className="card-title"><h3>Alarm log</h3><span className="sub">{feed.length} alarms so far</span></div>
            <div className="feed">
              {feed.length === 0 && <p className="note">No alarms yet.</p>}
              {feed.map((v) => (
                <div className="feed-item" key={v.link_id + v.window}>
                  <span className="t">{hh(v.window)}</span>
                  <span className="l">{v.link_id}</span>
                  <span className="d" title={`p-value ${pval(v.p_value)}`}>{pct(v.key_qber, 1)} key · {pct(v.ref_qber, 1)} ref</span>
                  <span className={`badge ${v.truth === 'honest' ? 'muted' : 'attack'}`}>{v.truth === 'honest' ? 'false alarm' : 'real'}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="grid-4">
          <div className="card stat">
            <span className="label">Honest hours flagged</span>
            <span className="value">{pct(avg(honest.map((v) => +v.alarm)))}</span>
            <span className="note">{honest.filter((v) => v.alarm).length} of {honest.length}; budget 5% (5.3% over 30 random days)</span>
          </div>
          <div className="card stat accent">
            <span className="label">Attacked hours flagged</span>
            <span className="value">{pct(avg(attacked.map((v) => +v.alarm)))}</span>
            <span className="note">{attacked.filter((v) => v.alarm).length} of {attacked.length}, including a tap on 1 of 16 rounds</span>
          </div>
          <div className="card stat">
            <span className="label">Attacked hours over 11% QBER</span>
            <span className="value">{pct(avg(attacked.map((v) => +(v.key_qber > 0.11))))}</span>
            <span className="note">what a fixed 11% alarm would have seen</span>
          </div>
          <div className="card stat">
            <span className="label">Drifting link L2, blocks flagged per hour</span>
            <span className="value">{avg(l2.map((v) => v.blocks_flagged)).toFixed(1)}<small>vs {avg(l2.map((v) => v.blocks_flagged_frozen)).toFixed(1)}</small></span>
            <span className="note">Nirikshak vs a threshold frozen at commissioning (of 20)</span>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="grid-2">
          <div className="card">
            <div className="card-title"><h3>Telemetry format</h3><span className="sub">JSON Lines, one record per block</span></div>
            <pre className="code">{d.telemetry_example.map((r) => JSON.stringify(r)).join('\n')}</pre>
            <p className="note" style={{ marginTop: 12 }}>
              <code>kind</code> is <code>key</code> (the key exchange's parameter-estimation sample) or <code>ref</code> (local
              reference states at the receiver). No key material, nothing vendor-specific.
            </p>
          </div>
          <div className="card">
            <div className="card-title"><h3>Run it on your own telemetry</h3></div>
            <pre className="code">{`pip install -r requirements.txt
python -m nirikshak.monitor --demo demo.jsonl   # this demo
python -m nirikshak.monitor your_links.jsonl    # status + alarm log`}</pre>
            <p className="note" style={{ marginTop: 12 }}>
              A real deployment would also need photonic details (decoy states, detector statistics, finite-key effects)
              and operator integration. This is a prototype.
            </p>
          </div>
        </div>
      </section>
    </>
  )
}
