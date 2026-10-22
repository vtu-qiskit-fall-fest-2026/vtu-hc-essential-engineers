import { useWidth } from './core'
import { pct } from '../data'

export type RulerMark = { rounds: number; qber: number; caught: string; rule: string }

/** The hero: a QBER scale from 0 to 16%, with today's normal, Nirikshak's threshold, the 11% abort
 *  line, and each real intercept-resend attack placed at its measured QBER. */
export function QberRuler({ marks, honest, reference, rule = 0.11 }: {
  marks: RulerMark[]; honest: [number, number]; reference: [number, number]; rule?: number
}) {
  const [ref, w] = useWidth<HTMLDivElement>()
  const vertical = w > 0 && w < 720
  const max = 0.16
  return (
    <div className="ruler" ref={ref}>
      {w > 0 && (vertical
        ? <Vertical w={w} {...{ marks, honest, reference, rule, max }} />
        : <Horizontal w={w} {...{ marks, honest, reference, rule, max }} />)}
    </div>
  )
}

type P = { w: number; marks: RulerMark[]; honest: [number, number]; reference: [number, number]; rule: number; max: number }

const tickList = (max: number) => Array.from({ length: Math.round(max * 200) + 1 }, (_, i) => i / 200)

function Horizontal({ w, marks, honest, reference, rule, max }: P) {
  const H = 380, base = 290, left = 2, right = w - 2
  const x = (q: number) => left + (q / max) * (right - left)
  const tiers = [64, 150]
  const label = 'QBER scale from 0 to 16 percent with measured attacks on ibm_kingston'
  return (
    <svg width={w} height={H} role="img" aria-label={label}>
      {/* abort zone */}
      <rect x={x(rule)} y={18} width={right - x(rule)} height={base - 18} fill="var(--plate-2)" />
      <line x1={x(rule)} x2={x(rule)} y1={10} y2={base + 26} stroke="var(--ink)" strokeWidth={2} />
      <text className="zone-label" x={x(rule) + 10} y={32} fill="var(--ink)">11%: BB84 stops making keys</text>
      <text className="m-sub" x={x(rule) + 10} y={50}>the only alarm BB84 has</text>

      {/* scale */}
      <line x1={left} x2={right} y1={base} y2={base} stroke="var(--ink)" strokeWidth={1.5} />
      {tickList(max).map((t) => {
        const major = Math.round(t * 1000) % 10 === 0
        return (
          <g key={t}>
            <line x1={x(t)} x2={x(t)} y1={base} y2={base + (major ? 12 : 6)} stroke="var(--ink-3)" strokeWidth={major ? 1.2 : 0.8} />
            {major && Math.round(t * 100) % 2 === 0 && (
              <text className={`scale-num ${t === 0 ? 'major' : ''}`} x={x(t)} y={base + 28}
                textAnchor={t === 0 ? 'start' : t >= max - 1e-9 ? 'end' : 'middle'}>{pct(t)}</text>
            )}
          </g>
        )
      })}
      <text className="scale-num major" x={right} y={base + 46} textAnchor="end">QBER of the key rounds</text>

      {/* today's normal: the reference rounds Eve cannot touch */}
      <rect x={x(reference[0])} y={base - 14} width={Math.max(x(reference[1]) - x(reference[0]), 3)} height={14} fill="var(--ref)" />
      <line x1={x((reference[0] + reference[1]) / 2)} x2={x((reference[0] + reference[1]) / 2)} y1={base - 14} y2={base - 70} stroke="var(--ref)" strokeWidth={1.5} />
      <text className="m-title" x={x((reference[0] + reference[1]) / 2) - 8} y={base - 78} textAnchor="middle">Today's normal</text>
      <text className="m-sub" x={x(0)} y={base + 64}>
        Reference rounds measured {pct(reference[0], 1)} to {pct(reference[1], 1)}, honest key rounds {pct(honest[0], 1)} to {pct(honest[1], 1)}.
        Nirikshak flags a session whose key rounds sit above its own reference rounds.
      </text>

      {/* attacks */}
      {marks.map((m, i) => {
        const tx = x(m.qber), ty = tiers[i % 2]
        const flip = tx > right - 190
        const anchor = flip ? 'end' : 'start'
        const lx = flip ? tx - 10 : tx + 10
        return (
          <g key={m.rounds} className="drop" style={{ animationDelay: `${250 + i * 160}ms` }}>
            <line x1={tx} x2={tx} y1={ty - 14} y2={base - 1} stroke="var(--key)" strokeWidth={1.5} />
            <circle cx={tx} cy={base} r={6} fill="var(--key)" stroke="var(--plate)" strokeWidth={2} />
            <text className="m-title" x={lx} y={ty} textAnchor={anchor}>Eve on {m.rounds} of 16 rounds</text>
            <text className="m-value" x={lx} y={ty + 25} textAnchor={anchor}>{pct(m.qber, 1)}</text>
            <text className="m-sub hit" x={lx} y={ty + 44} textAnchor={anchor}>Nirikshak: {m.caught}</text>
            <text className="m-sub" x={lx} y={ty + 61} textAnchor={anchor}>11% rule: {m.rule}</text>
          </g>
        )
      })}
    </svg>
  )
}

function Vertical({ w, marks, reference, rule, max }: P) {
  const H = 640, top = 16, base = H - 20, axisX = 44
  const y = (q: number) => base - (q / max) * (base - top)
  return (
    <svg width={w} height={H} role="img" aria-label="QBER scale from 0 to 16 percent with measured attacks on ibm_kingston">
      <rect x={axisX} y={top} width={w - axisX} height={y(rule) - top} fill="var(--plate-2)" />
      <line x1={axisX - 10} x2={w} y1={y(rule)} y2={y(rule)} stroke="var(--ink)" strokeWidth={2} />
      <text className="zone-label" x={w} y={y(rule) - 8} textAnchor="end" fill="var(--ink)">11%: BB84 stops making keys</text>
      <line x1={axisX} x2={axisX} y1={top} y2={base} stroke="var(--ink)" strokeWidth={1.5} />
      {tickList(max).map((t) => {
        const major = Math.round(t * 1000) % 10 === 0
        return (
          <g key={t}>
            <line x1={axisX - (major ? 10 : 5)} x2={axisX} y1={y(t)} y2={y(t)} stroke="var(--ink-3)" />
            {major && Math.round(t * 100) % 2 === 0 && <text className="scale-num" x={axisX - 14} y={y(t) + 4} textAnchor="end">{pct(t)}</text>}
          </g>
        )
      })}
      <rect x={axisX} y={y(reference[1])} width={14} height={Math.max(y(reference[0]) - y(reference[1]), 3)} fill="var(--ref)" />
      <text className="m-sub" x={axisX + 22} y={y(reference[0]) + 4}>
        Today's normal: reference rounds {pct(reference[0], 1)} to {pct(reference[1], 1)}
      </text>
      {marks.map((m, i) => {
        const ty = y(m.qber)
        return (
          <g key={m.rounds} className="drop" style={{ animationDelay: `${250 + i * 160}ms` }}>
            <line x1={axisX} x2={axisX + 24} y1={ty} y2={ty} stroke="var(--key)" strokeWidth={1.5} />
            <circle cx={axisX} cy={ty} r={5} fill="var(--key)" stroke="var(--plate)" strokeWidth={2} />
            <text className="m-title" x={axisX + 30} y={ty + 5}>
              <tspan className="m-value" style={{ fontSize: 17 }}>{pct(m.qber, 1)}</tspan>
              <tspan dx={8}>Eve on {m.rounds} of 16</tspan>
            </text>
            <text className="m-sub" x={axisX + 30} y={ty + 22}>
              <tspan className="m-sub hit">Nirikshak {m.caught}</tspan>
              <tspan dx={10}>11% rule {m.rule}</tspan>
            </text>
          </g>
        )
      })}
    </svg>
  )
}
