import { useEffect, useMemo, useState } from 'react'
import { LinkTrace } from '../charts/charts'
import { C, Legend } from '../charts/core'
import { Verdict as VerdictBadge } from '../components/ui'
import { pct, pval, useData, type Monitor as M, type Verdict } from '../data'

const hh = (h: number) => `${String(Math.floor(h) % 24).padStart(2, '0')}:00`
const avg = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / Math.max(xs.length, 1)

export default function Monitor() {
  const d = useData<M>('monitor')
  const hours = useMemo(() => (d ? Math.max(...d.verdicts.map((v) => v.window)) + 1 : 0), [d])
  const [upto, setUpto] = useState<number | null>(null)
  const [playing, setPlaying] = useState(false)
  const [pick, setPick] = useState('L3')
  const [hot, setHot] = useState<Verdict | null>(null)

  const now = upto ?? hours
  useEffect(() => {
    if (!playing) return
    const id = setInterval(() => {
      setUpto((u) => {
        const next = (u ?? 0) + 1
        if (next >= hours) { setPlaying(false); return hours }
        return next
      })
    }, 500)
    return () => clearInterval(id)
  }, [playing, hours])

  if (!d) return null

  const seen = d.verdicts.filter((v) => v.window < now)
  const honest = d.verdicts.filter((v) => v.truth === 'honest')
  const attacked = d.verdicts.filter((v) => v.truth !== 'honest')
  const l2 = d.verdicts.filter((v) => v.link_id === 'L2')
  const b = d.blocks[pick]
  const linkInfo = d.links.find((l) => l.link_id === pick)!
  const feed = seen.filter((v) => v.alarm).sort((a, b2) => b2.window - a.window || a.link_id.localeCompare(b2.link_id))
  const pickHours = Math.max(...d.verdicts.filter((v) => v.link_id === pick).map((v) => v.window)) + 1

  return (
    <>
      <section className="hero">
        <div className="hero-top">
          <h1 className="statement">One verdict per link, every hour.</h1>
          <p className="prose">
            Each link reports a few counts per block: sifted rounds and errors, for key rounds and for local reference
            rounds that never cross the channel. Nirikshak turns them into an hourly verdict that stays within a 5%
            false-alarm budget however the link drifts. Four links here are simulated; L5 replays our real ibm_kingston
            sessions, one per hour. No real operator or network is shown.
          </p>
        </div>
      </section>

      <section className="plate" style={{ display: 'grid', gap: 14 }}>
        <div className="controls">
          <button className="btn" onClick={() => {
            if (playing) return setPlaying(false)
            if (now >= hours) setUpto(0)
            setPlaying(true)
          }}>
            <svg width="11" height="11" viewBox="0 0 12 12" aria-hidden>
              {playing ? <><rect x="2" y="1" width="3" height="10" fill="currentColor" /><rect x="7" y="1" width="3" height="10" fill="currentColor" /></>
                : <path d="M2 1 L11 6 L2 11 Z" fill="currentColor" />}
            </svg>
            {playing ? 'Pause' : now >= hours ? 'Replay the day' : 'Play'}
          </button>
          <label className="control" style={{ flex: 1, minWidth: 200 }}>
            <span>{now >= hours ? `Showing all ${hours} hours` : `Showing up to ${hh(now)}${now >= 24 ? ' the next day' : ''}`}</span>
            <input type="range" min={0} max={hours} value={now} aria-label="Hour"
              onChange={(e) => { setPlaying(false); setUpto(+e.target.value) }} />
          </label>
        </div>

        <div className="board" style={{ ['--hours' as string]: hours }} onMouseLeave={() => setHot(null)}>
          <div className="board-row head">
            <div className="who"><span className="src">Link</span></div>
            <div className="hours">
              {Array.from({ length: hours }, (_, h) => <span key={h}>{h % 6 === 0 ? hh(h) : ''}</span>)}
            </div>
            <div className="tallycol">Alarms</div>
          </div>
          {d.links.map((l) => {
            const lv = d.verdicts.filter((v) => v.link_id === l.link_id)
            const shown = lv.filter((v) => v.window < now)
            const last = shown[shown.length - 1]
            return (
              <div key={l.link_id} className={`board-row ${pick === l.link_id ? 'picked' : ''}`}>
                <button className="who" onClick={() => setPick(l.link_id)} aria-pressed={pick === l.link_id}>
                  <span className="id">{l.link_id} {last ? <VerdictBadge alarm={last.alarm} /> : null}</span>
                  <span className="desc">{l.description}</span>
                  <span className="src">{l.source === 'simulated' ? 'Simulated' : 'Real IBM hardware, replayed'}</span>
                </button>
                <div className="strip">
                  {Array.from({ length: hours }, (_, h) => {
                    const v = lv.find((x) => x.window === h)
                    if (!v) return <span key={h} />
                    const future = h >= now
                    return (
                      <button key={h} aria-label={`${l.link_id} ${hh(h)}: ${v.alarm ? 'alarm' : 'clean'}`}
                        className={`${!future && v.alarm ? 'alarm' : ''} ${future ? 'future' : ''} ${v.truth !== 'honest' ? 'truth' : ''} ${hot === v ? 'hot' : ''}`}
                        onMouseEnter={() => !future && setHot(v)} onFocus={() => !future && setHot(v)}
                        onClick={() => { setPick(l.link_id); if (!future) setHot(v) }} />
                    )
                  })}
                </div>
                <div className="tallycol">{shown.filter((v) => v.alarm).length} of {shown.length}</div>
              </div>
            )
          })}
        </div>

        <div className="readout" aria-live="polite">
          {hot ? (
            <>
              <span><b>{hot.link_id}</b>, {hh(hot.window)} to {hh(hot.window + 1)}</span>
              <span>Verdict <b>{hot.alarm ? 'alarm' : 'clean'}</b>, p {pval(hot.p_value)}</span>
              <span>Key rounds <b>{pct(hot.key_qber, 2)}</b>, reference <b>{pct(hot.ref_qber, 2)}</b></span>
              <span>Blocks over the threshold <b>{hot.blocks_flagged} of 20</b></span>
              <span>What really happened <b>{hot.truth === 'honest' ? 'nothing, honest hour' : `attack, ${hot.truth}`}</b></span>
            </>
          ) : (
            <span>Point at an hour to read its verdict. Red cells are alarms; a dark underline marks hours that were really attacked.</span>
          )}
        </div>
      </section>

      <section className="finding">
        <div className="gutter">
          <h2 className="title">{pick}, block by block</h2>
          <p className="note">{linkInfo.description}. Every dot is one key block. The orange line is Nirikshak's threshold,
            recomputed from the last 20 reference blocks; the dashed line is a threshold fixed when the link was commissioned.</p>
          <div className="seg">
            {d.links.map((l) => <button key={l.link_id} className={l.link_id === pick ? 'on' : ''} onClick={() => setPick(l.link_id)}>{l.link_id}</button>)}
          </div>
        </div>
        <div className="body">
          <div className="plate">
            <Legend items={[
              { label: 'Flagged key block', color: C.s1, kind: 'dot' },
              { label: 'Key block', color: 'var(--ink-3)', kind: 'dot' },
              { label: "Nirikshak's threshold", color: C.s2, kind: 'line' },
              { label: 'Fixed at commissioning', color: C.neutral, kind: 'dash' },
              { label: 'Attacked hours', color: 'var(--alarm-soft)' },
            ]} />
            <div style={{ marginTop: 8 }}>
              <LinkTrace h={b.h} qber={b.qber} threshold={b.threshold} alarm={b.alarm} frozen={b.frozen_threshold}
                hours={pickHours} upto={now}
                attacked={d.verdicts.filter((v) => v.link_id === pick && v.truth !== 'honest').map((v) => v.window)} />
            </div>
          </div>
        </div>
      </section>

      <section className="finding">
        <div className="gutter">
          <h2 className="title">Alarm log</h2>
          <p className="note">What an operator would receive, newest first. False alarms are marked; at a 5% budget about one honest hour in twenty raises one.</p>
        </div>
        <div className="body split">
          <div className="plate">
            <div className="feed">
              {feed.length === 0 && <p className="note">No alarms yet. Press play to run the day.</p>}
              {feed.map((v) => (
                <div className="feed-item" key={v.link_id + v.window}>
                  <span className="t">{hh(v.window)}</span>
                  <span className="l">{v.link_id}</span>
                  <span className="d" title={`p-value ${pval(v.p_value)}`}>key {pct(v.key_qber, 1)}, reference {pct(v.ref_qber, 1)}</span>
                  <span className={`badge ${v.truth === 'honest' ? 'muted' : 'attack'}`}>{v.truth === 'honest' ? 'false alarm' : 'attack'}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="plate" style={{ display: 'grid', gap: 14, alignContent: 'start' }}>
            <p className="tally" style={{ fontSize: 18 }}>
              <span className="n key">{pct(avg(attacked.map((v) => +v.alarm)))}</span> of attacked hours flagged, including a
              tap on 1 of 16 rounds. <span className="n">{pct(avg(attacked.map((v) => +(v.key_qber > 0.11))))}</span> of them
              crossed 11%.
            </p>
            <p className="tally" style={{ fontSize: 18 }}>
              <span className="n">{pct(avg(honest.map((v) => +v.alarm)))}</span> of honest hours flagged ({honest.filter((v) => v.alarm).length} of{' '}
              {honest.length}); over 30 simulated days it was 5.3%.
            </p>
            <p className="tally" style={{ fontSize: 18 }}>
              On the drifting link L2, <span className="n">{avg(l2.map((v) => v.blocks_flagged)).toFixed(1)}</span> blocks
              an hour crossed Nirikshak's threshold, against <span className="n">{avg(l2.map((v) => v.blocks_flagged_frozen)).toFixed(1)}</span> for
              the commissioning threshold.
            </p>
          </div>
        </div>
      </section>

      <section className="finding">
        <div className="gutter">
          <h2 className="title">Plug in your own links</h2>
          <p className="note">One JSON line per block. <code>kind</code> is <code>key</code> for the key exchange's
            test sample or <code>ref</code> for local reference states. No key material, nothing vendor-specific.</p>
        </div>
        <div className="body split even">
          <pre className="code">{d.telemetry_example.map((r) => JSON.stringify(r)).join('\n')}</pre>
          <div style={{ display: 'grid', gap: 12, alignContent: 'start' }}>
            <pre className="code">{`python -m nirikshak.monitor --demo demo.jsonl
python -m nirikshak.monitor your_links.jsonl`}</pre>
            <p className="note">A real deployment also needs photonic detail (decoy states, detector statistics,
              finite-key effects) and integration with the operator's systems. This is a prototype.</p>
          </div>
        </div>
      </section>
    </>
  )
}
