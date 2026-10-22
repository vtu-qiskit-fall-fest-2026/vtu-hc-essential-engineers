import { useState, Fragment } from 'react'
import { C, ChartFrame, HBar, TipBody, linear, niceTicks, type Tip } from './core'
import { ci, pct, pretty, pval, type Rate } from '../data'

const pctTick = (v: number, step: number) => `${(v * 100).toFixed(step < 0.01 ? 1 : 0)}%`

/* ------------------------------------------------------------------ grouped horizontal bars + CI */

export function DetectionBars({ rows }: {
  rows: { label: string; note?: string; a: Rate; b: Rate }[]
}) {
  const [tip, setTip] = useState<Tip>(null)
  const rowH = 46, top = 6, bottom = 26
  const height = top + rows.length * rowH + bottom
  return (
    <ChartFrame height={height} tip={tip} label="Share of key blocks flagged per condition, Nirikshak vs 11% rule">
      {(w) => {
        const labelW = Math.min(170, w * 0.36)
        const x = linear(0, 1, labelW, w - 44)
        return (
          <g onMouseLeave={() => setTip(null)}>
            {[0, 0.25, 0.5, 0.75, 1].map((t) => (
              <g key={t}>
                <line x1={x(t)} x2={x(t)} y1={top} y2={height - bottom} stroke={C.grid} />
                <text x={x(t)} y={height - 8} textAnchor="middle">{pct(t)}</text>
              </g>
            ))}
            {rows.map((r, i) => {
              const y0 = top + i * rowH + 7
              const bh = 13
              const bars = [
                { r: r.a, y: y0, fill: C.s1, name: 'Nirikshak' },
                { r: r.b, y: y0 + bh + 3, fill: C.neutral, name: '11% rule' },
              ]
              return (
                <g key={r.label}
                  onMouseMove={(e) => {
                    const box = (e.currentTarget.ownerSVGElement as SVGSVGElement).getBoundingClientRect()
                    setTip({ x: e.clientX - box.left, y: e.clientY - box.top, content: (
                      <TipBody title={pretty(r.label) + (r.note ? ` (${r.note})` : '')} rows={[
                        ['Nirikshak', `${pct(r.a.rate)} (${ci(r.a)})`],
                        ['11% rule', `${pct(r.b.rate)} (${ci(r.b)})`],
                        ['Blocks', String(r.a.n)],
                      ]} />) })
                  }}>
                  <rect x={0} y={top + i * rowH} width={w} height={rowH} fill="transparent" />
                  <text x={labelW - 12} y={y0 + bh + 2} textAnchor="end" className="tick-label">{pretty(r.label)}</text>
                  {r.note && <text x={labelW - 12} y={y0 + bh + 16} textAnchor="end" style={{ fontSize: 10.5 }}>{r.note}</text>}
                  {bars.map((b) => (
                    <g key={b.name}>
                      <HBar x0={x(0)} x1={x(b.r.rate ?? 0)} y={b.y} h={bh} fill={b.fill} />
                      <line x1={x(b.r.lo)} x2={x(b.r.hi)} y1={b.y + bh / 2} y2={b.y + bh / 2} stroke="var(--text-2)" strokeWidth={1} opacity={0.55} />
                      <text x={x(Math.max(b.r.rate ?? 0, b.r.hi)) + 6} y={b.y + bh - 2} style={{ fill: 'var(--text-2)', fontSize: 11.5, fontWeight: 500 }}>
                        {pct(b.r.rate)}
                      </text>
                    </g>
                  ))}
                </g>
              )
            })}
          </g>
        )
      }}
    </ChartFrame>
  )
}

/* ------------------------------------------------------------------ single-series bars with highlight */

export function WorstBars({ rows, budget, highlight }: {
  rows: { label: string; value: number; where: string }[]; budget: number; highlight: string
}) {
  const [tip, setTip] = useState<Tip>(null)
  const rowH = 38, top = 18, bottom = 26
  const height = top + rows.length * rowH + bottom
  return (
    <ChartFrame height={height} tip={tip} label="Worst-case false-alarm rate per detector">
      {(w) => {
        const labelW = Math.min(220, w * 0.4)
        const x = linear(0, 1, labelW, w - 48)
        return (
          <g onMouseLeave={() => setTip(null)}>
            {[0, 0.25, 0.5, 0.75, 1].map((t) => (
              <g key={t}>
                <line x1={x(t)} x2={x(t)} y1={top} y2={height - bottom} stroke={C.grid} />
                <text x={x(t)} y={height - 8} textAnchor="middle">{pct(t)}</text>
              </g>
            ))}
            {rows.map((r, i) => {
              const y = top + i * rowH + 9
              return (
                <g key={r.label} onMouseMove={(e) => {
                  const box = (e.currentTarget.ownerSVGElement as SVGSVGElement).getBoundingClientRect()
                  setTip({ x: e.clientX - box.left, y: e.clientY - box.top, content: (
                    <TipBody title={r.label} rows={[['Worst false-alarm rate', pct(r.value)], ['Where', r.where]]} />) })
                }}>
                  <rect x={0} y={top + i * rowH} width={w} height={rowH} fill="transparent" />
                  <text x={labelW - 12} y={y + 14} textAnchor="end" className="tick-label"
                    style={r.label === highlight ? { fontWeight: 600, fill: 'var(--text)' } : undefined}>{r.label}</text>
                  <HBar x0={x(0)} x1={x(r.value)} y={y} h={20} fill={r.label === highlight ? C.s1 : C.neutral} />
                  <text x={x(r.value) + 6} y={y + 14} style={{ fill: 'var(--text-2)', fontSize: 11.5, fontWeight: 500 }}>{pct(r.value)}</text>
                </g>
              )
            })}
            <line x1={x(budget)} x2={x(budget)} y1={top - 6} y2={height - bottom} stroke={C.s2} strokeWidth={2} strokeDasharray="4 3" />
            <text x={x(budget) + 5} y={top - 6} style={{ fill: 'var(--text-2)', fontSize: 11 }}>{pct(budget)} budget</text>
          </g>
        )
      }}
    </ChartFrame>
  )
}

/* ------------------------------------------------------------------ block strip: sessions side by side */

export type StripSession = {
  label: string; is_attack: boolean; threshold: number; key_blocks: number[]; ref_blocks?: number[]
  verdict?: boolean; p_value?: number
}

export function BlockStrip({ sessions, rule = 0.11, height = 340, showRef = true, yMax }: {
  sessions: StripSession[]; rule?: number; height?: number; showRef?: boolean; yMax?: number
}) {
  const [tip, setTip] = useState<Tip>(null)
  const top = 34, bottom = 46, left = 44
  const maxQ = yMax ?? Math.max(rule * 1.08, ...sessions.flatMap((s) => [...s.key_blocks, ...(s.ref_blocks ?? [])]))
  const ticks = niceTicks(maxQ, 5)
  const yTop = ticks[ticks.length - 1]
  return (
    <ChartFrame height={height} tip={tip} label="Block QBER per session with the Nirikshak threshold and the 11% rule">
      {(w) => {
        const y = linear(0, yTop, height - bottom, top)
        const n = sessions.length
        const gap = Math.max(6, Math.min(16, w / n / 6))
        const colW = (w - left - gap * (n - 1)) / n
        return (
          <g onMouseLeave={() => setTip(null)}>
            {ticks.map((t) => (
              <g key={t}>
                <line x1={left} x2={w} y1={y(t)} y2={y(t)} stroke={C.grid} />
                <text x={left - 8} y={y(t) + 4} textAnchor="end">{pctTick(t, ticks[1] - ticks[0])}</text>
              </g>
            ))}
            <line x1={left} x2={w} y1={y(rule)} y2={y(rule)} stroke={C.neutral} strokeWidth={1.5} strokeDasharray="5 4" />
            <text x={w} y={y(rule) - 6} textAnchor="end" style={{ fill: 'var(--text-2)', fontSize: 11 }}>11% rule</text>
            {sessions.map((s, i) => {
              const x0 = left + i * (colW + gap)
              const color = s.is_attack ? C.s1 : C.neutral
              const kx = (j: number, m: number) => x0 + ((j + 0.5) / m) * colW * (showRef ? 0.62 : 1) + (showRef ? colW * 0.38 : 0)
              const rx = (j: number, m: number) => x0 + ((j + 0.5) / m) * colW * 0.32
              const r = Math.max(2.2, Math.min(4, colW / 24))
              return (
                <g key={i}>
                  <rect x={x0} y={top} width={colW} height={height - top - bottom} fill="var(--surface-2)" opacity={0.5} rx={6} />
                  {showRef && s.ref_blocks?.map((q, j) => (
                    <circle key={'r' + j} cx={rx(j, s.ref_blocks!.length)} cy={y(Math.min(q, yTop))} r={r * 0.75} fill="var(--text-3)" opacity={0.5} />
                  ))}
                  <line x1={x0 + 2} x2={x0 + colW - 2} y1={y(s.threshold)} y2={y(s.threshold)} stroke={C.s2} strokeWidth={2} />
                  {s.key_blocks.map((q, j) => {
                    const flagged = q > s.threshold
                    return (
                      <circle key={j} cx={kx(j, s.key_blocks.length)} cy={y(Math.min(q, yTop))} r={r}
                        fill={flagged ? color : C.surface} stroke={color} strokeWidth={1.5} />
                    )
                  })}
                  <rect x={x0} y={top} width={colW} height={height - top - bottom} fill="transparent"
                    onMouseMove={(e) => {
                      const box = (e.currentTarget.ownerSVGElement as SVGSVGElement).getBoundingClientRect()
                      const flagged = s.key_blocks.filter((q) => q > s.threshold).length
                      const rows: [string, string][] = [
                        ['Key QBER (mean)', pct(s.key_blocks.reduce((a, b) => a + b, 0) / s.key_blocks.length, 2)],
                        ['Threshold', pct(s.threshold, 2)],
                        ['Blocks flagged', `${flagged} of ${s.key_blocks.length}`],
                      ]
                      if (s.ref_blocks?.length) rows.splice(1, 0, ['Reference QBER', pct(s.ref_blocks.reduce((a, b) => a + b, 0) / s.ref_blocks.length, 2)])
                      if (s.p_value != null) rows.push(['Session verdict', `${s.verdict ? 'ATTACK' : 'clean'} (p ${pval(s.p_value)})`])
                      setTip({ x: e.clientX - box.left, y: e.clientY - box.top, content: <TipBody title={pretty(s.label)} rows={rows} /> })
                    }} />
                  <text x={x0 + colW / 2} y={height - bottom + 16} textAnchor="middle" className="tick-label" style={{ fontSize: n > 6 ? 10.5 : 12 }}>
                    {shortLabel(s.label, colW)}
                  </text>
                  {s.verdict != null && (
                    <g transform={`translate(${x0 + colW / 2}, ${height - bottom + 32})`}>
                      <text textAnchor="middle" style={{ fontSize: 10.5, fontWeight: 600, fill: s.verdict ? 'var(--critical)' : 'var(--text-3)' }}>
                        {s.verdict ? '▲ attack' : '○ clean'}
                      </text>
                    </g>
                  )}
                </g>
              )
            })}
          </g>
        )
      }}
    </ChartFrame>
  )
}

function shortLabel(label: string, w: number) {
  const p = pretty(label)
  if (w > 110) return p
  return p.replace('Intercept ', 'IR ').replace('Probe ', 'EP ').replace(', ', ' ')
}

/* ------------------------------------------------------------------ drift: key vs reference per batch */

export function DriftDots({ groups }: {
  groups: { label: string; sub: string; key: number[]; ref: number[] }[]
}) {
  const [tip, setTip] = useState<Tip>(null)
  const height = 260, top = 14, bottom = 44, left = 46
  const maxQ = Math.max(0.025, ...groups.flatMap((g) => [...g.key, ...g.ref])) * 1.15
  const ticks = niceTicks(maxQ, 4)
  return (
    <ChartFrame height={height} tip={tip} label="Honest QBER per batch, key rounds vs reference rounds">
      {(w) => {
        const y = linear(0, ticks[ticks.length - 1], height - bottom, top)
        const colW = (w - left) / groups.length
        return (
          <g onMouseLeave={() => setTip(null)}>
            {ticks.map((t) => (
              <g key={t}>
                <line x1={left} x2={w} y1={y(t)} y2={y(t)} stroke={C.grid} />
                <text x={left - 8} y={y(t) + 4} textAnchor="end">{pctTick(t, ticks[1] - ticks[0])}</text>
              </g>
            ))}
            {groups.map((g, i) => {
              const cx = left + colW * (i + 0.5)
              return (
                <g key={g.label} onMouseMove={(e) => {
                  const box = (e.currentTarget.ownerSVGElement as SVGSVGElement).getBoundingClientRect()
                  setTip({ x: e.clientX - box.left, y: e.clientY - box.top, content: (
                    <TipBody title={`${g.label}, ${g.sub}`} rows={[
                      ['Key rounds', g.key.map((q) => pct(q, 2)).join(', ')],
                      ['Reference rounds', g.ref.map((q) => pct(q, 2)).join(', ')],
                    ]} />) })
                }}>
                  <rect x={left + colW * i} y={top} width={colW} height={height - top - bottom} fill="transparent" />
                  {g.key.map((q, j) => <circle key={'k' + j} cx={cx - 12} cy={y(q)} r={5} fill={C.s1} stroke={C.surface} strokeWidth={2} />)}
                  {g.ref.map((q, j) => <circle key={'r' + j} cx={cx + 12} cy={y(q)} r={5} fill={C.s2} stroke={C.surface} strokeWidth={2} />)}
                  <text x={cx} y={height - bottom + 18} textAnchor="middle" className="tick-label">{g.label}</text>
                  <text x={cx} y={height - bottom + 33} textAnchor="middle">{g.sub}</text>
                </g>
              )
            })}
          </g>
        )
      }}
    </ChartFrame>
  )
}

/* ------------------------------------------------------------------ monitor: links x hours grid */

export type GridCell = { link: string; h: number; alarm: boolean; truth: string; p: number; key: number; ref: number; label: string }

export function MonitorGrid({ links, hours, cells, upto, onPick }: {
  links: string[]; hours: number; cells: GridCell[]; upto: number; onPick?: (link: string) => void
}) {
  const [tip, setTip] = useState<Tip>(null)
  const rowH = 30, top = 8, bottom = 24, left = 40
  const height = top + links.length * rowH + bottom
  return (
    <ChartFrame height={height} tip={tip} label="Verdict per link and hour">
      {(w) => {
        const cw = (w - left) / hours
        return (
          <g onMouseLeave={() => setTip(null)}>
            {links.map((l, i) => (
              <text key={l} x={left - 10} y={top + i * rowH + rowH / 2 + 4} textAnchor="end" className="tick-label mono"
                style={{ fontFamily: 'var(--mono)', cursor: onPick ? 'pointer' : undefined }} onClick={() => onPick?.(l)}>{l}</text>
            ))}
            {Array.from({ length: hours + 1 }, (_, h) => h).filter((h) => h % 6 === 0).map((h) => (
              <text key={h} x={left + h * cw} y={height - 6} textAnchor="middle">{`${String(h % 24).padStart(2, '0')}:00`}</text>
            ))}
            {cells.map((c) => {
              const i = links.indexOf(c.link)
              const visible = c.h < upto
              const x = left + c.h * cw + 1, yy = top + i * rowH + 2
              const attacked = c.truth !== 'honest'
              return (
                <g key={c.link + c.h} opacity={visible ? 1 : 0.18} style={{ cursor: onPick ? 'pointer' : undefined }}
                  onClick={() => onPick?.(c.link)}
                  onMouseMove={(e) => {
                    if (!visible) return setTip(null)
                    const box = (e.currentTarget.ownerSVGElement as SVGSVGElement).getBoundingClientRect()
                    setTip({ x: e.clientX - box.left, y: e.clientY - box.top, content: (
                      <TipBody title={`${c.link}, ${c.label}`} rows={[
                        ['Verdict', c.alarm ? 'ALARM' : 'clean'],
                        ['p-value', pval(c.p)],
                        ['Key / reference QBER', `${pct(c.key, 2)} / ${pct(c.ref, 2)}`],
                        ['Actually', attacked ? `attacked (${c.truth})` : 'honest'],
                      ]} />) })
                  }}>
                  <rect x={x} y={yy} width={Math.max(cw - 2, 1)} height={rowH - 4} rx={3}
                    fill={visible && c.alarm ? 'var(--critical)' : 'var(--surface-2)'} />
                  {attacked && (
                    <rect x={x} y={yy + rowH - 8} width={Math.max(cw - 2, 1)} height={3} rx={1.5} fill="var(--text)" opacity={visible ? 0.75 : 0.4} />
                  )}
                </g>
              )
            })}
            {upto < hours && (
              <line x1={left + upto * cw} x2={left + upto * cw} y1={top - 4} y2={height - bottom + 2} stroke="var(--text)" strokeWidth={1.5} />
            )}
          </g>
        )
      }}
    </ChartFrame>
  )
}

/* ------------------------------------------------------------------ monitor: one link over time */

export function LinkTrace({ h, qber, threshold, alarm, frozen, hours, upto, attacked }: {
  h: number[]; qber: number[]; threshold: (number | null)[]; alarm: number[]; frozen: number | null; hours: number; upto: number
  attacked: number[]
}) {
  const [tip, setTip] = useState<Tip>(null)
  const height = 280, top = 14, bottom = 28, left = 46
  const maxQ = Math.max(0.03, ...qber) * 1.1
  const ticks = niceTicks(maxQ, 4)
  return (
    <ChartFrame height={height} tip={tip} label="Key block QBER over time with Nirikshak's rolling threshold">
      {(w) => {
        const x = linear(0, hours, left, w)
        const y = linear(0, ticks[ticks.length - 1], height - bottom, top)
        const pts: string[] = []
        threshold.forEach((t, i) => { if (t != null && h[i] < upto) pts.push(`${x(h[i]).toFixed(1)},${y(t).toFixed(1)}`) })
        return (
          <g onMouseLeave={() => setTip(null)}
            onMouseMove={(e) => {
              const box = (e.currentTarget.ownerSVGElement as SVGSVGElement).getBoundingClientRect()
              const hx = ((e.clientX - box.left - left) / (w - left)) * hours
              if (hx < 0 || hx > Math.min(upto, hours)) return setTip(null)
              let best = 0
              h.forEach((v, i) => { if (Math.abs(v - hx) < Math.abs(h[best] - hx)) best = i })
              setTip({ x: e.clientX - box.left, y: e.clientY - box.top, content: (
                <TipBody title={`Block at ${String(Math.floor(h[best]) % 24).padStart(2, '0')}:${String(Math.floor((h[best] % 1) * 60)).padStart(2, '0')}`} rows={[
                  ['Key QBER', pct(qber[best], 2)],
                  ['Nirikshak threshold', threshold[best] == null ? 'warming up' : pct(threshold[best]!, 2)],
                  ['Frozen threshold', frozen == null ? 'n/a' : pct(frozen, 2)],
                  ['Flagged', alarm[best] ? 'yes' : 'no'],
                ]} />) })
            }}>
            <rect x={left} y={top} width={w - left} height={height - top - bottom} fill="transparent" />
            {attacked.map((a) => (
              <rect key={a} x={x(a)} y={top} width={x(a + 1) - x(a)} height={height - top - bottom} fill="var(--critical-soft)" />
            ))}
            {ticks.map((t) => (
              <g key={t}>
                <line x1={left} x2={w} y1={y(t)} y2={y(t)} stroke={C.grid} />
                <text x={left - 8} y={y(t) + 4} textAnchor="end">{pctTick(t, ticks[1] - ticks[0])}</text>
              </g>
            ))}
            {Array.from({ length: Math.floor(hours / 6) + 1 }, (_, i) => i * 6).map((t) => (
              <text key={t} x={x(t)} y={height - 8} textAnchor="middle">{`${String(t % 24).padStart(2, '0')}:00`}</text>
            ))}
            {frozen != null && (
              <g>
                <line x1={left} x2={w} y1={y(frozen)} y2={y(frozen)} stroke={C.neutral} strokeWidth={1.5} strokeDasharray="5 4" />
                <text x={left + 6} y={y(frozen) - 6} style={{ fill: 'var(--text-2)', fontSize: 11.5 }}>fixed at commissioning</text>
              </g>
            )}
            {h.map((v, i) => v < upto && (
              <circle key={i} cx={x(v)} cy={y(qber[i])} r={alarm[i] ? 3 : 2.2}
                fill={alarm[i] ? C.s1 : 'var(--text-3)'} opacity={alarm[i] ? 1 : 0.45} />
            ))}
            <polyline points={pts.join(' ')} fill="none" stroke={C.s2} strokeWidth={2} strokeLinejoin="round" />
          </g>
        )
      }}
    </ChartFrame>
  )
}

/* ------------------------------------------------------------------ heat table */

export function HeatTable({ rows, cols, value, fmt, good, rowLabel }: {
  rows: string[]; cols: string[]; value: (r: string, c: string) => number | undefined
  fmt?: (v: number) => string; good: 'low' | 'high'; rowLabel?: (r: string) => string
}) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Tested on</th>
            {cols.map((c) => <th key={c} className="num" style={{ whiteSpace: 'normal', minWidth: 90 }}>{c}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r}>
              <td style={{ whiteSpace: 'normal', minWidth: 170 }}>{rowLabel ? rowLabel(r) : r}</td>
              {cols.map((c) => {
                const v = value(r, c)
                const bad = v == null ? 0 : good === 'low' ? v : 1 - v
                return (
                  <Fragment key={c}>
                    <td className="num" style={{
                      background: v == null ? undefined : `color-mix(in srgb, var(--critical) ${Math.round(Math.min(bad, 1) * 38)}%, transparent)`,
                      fontWeight: c === 'Nirikshak' ? 600 : undefined,
                    }}>{v == null ? '' : (fmt ?? ((x: number) => pct(x)))(v)}</td>
                  </Fragment>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
