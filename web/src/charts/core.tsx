import { useLayoutEffect, useRef, useState, type ReactNode } from 'react'

/** Width of a container, tracked with ResizeObserver. */
export function useWidth<T extends HTMLElement>(): [React.RefObject<T | null>, number] {
  const ref = useRef<T>(null)
  const [w, setW] = useState(0)
  useLayoutEffect(() => {
    if (!ref.current) return
    const ro = new ResizeObserver(([e]) => setW(Math.round(e.contentRect.width)))
    ro.observe(ref.current)
    setW(Math.round(ref.current.getBoundingClientRect().width))
    return () => ro.disconnect()
  }, [])
  return [ref, w]
}

export const linear = (d0: number, d1: number, r0: number, r1: number) => (v: number) =>
  d1 === d0 ? r0 : r0 + ((v - d0) / (d1 - d0)) * (r1 - r0)

export function niceTicks(max: number, count = 4): number[] {
  const raw = max / count
  const mag = 10 ** Math.floor(Math.log10(raw))
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw) ?? raw
  const out: number[] = []
  for (let v = 0; ; v += step) {
    out.push(+v.toFixed(10))
    if (v >= max - 1e-12) break
  }
  return out
}

export type Tip = { x: number; y: number; content: ReactNode } | null

/** Chart frame: a relative container with a measured width and a tooltip layer. */
export function ChartFrame({ height, children, tip, label }: {
  height: number; tip: Tip; label: string
  children: (width: number) => ReactNode
}) {
  const [ref, width] = useWidth<HTMLDivElement>()
  let left = 0
  if (tip) left = Math.min(Math.max(tip.x + 14, 0), Math.max(width - 230, 0))
  return (
    <div className="chart" ref={ref} style={{ height }}>
      {width > 0 && (
        <svg width={width} height={height} role="img" aria-label={label}>
          {children(width)}
        </svg>
      )}
      {tip && (
        <div className="tooltip" style={{ left, top: Math.max(tip.y - 10, 0) }}>
          {tip.content}
        </div>
      )}
    </div>
  )
}

export function TipBody({ title, rows }: { title: string; rows: [string, ReactNode][] }) {
  return (
    <>
      <div className="tt-title">{title}</div>
      {rows.map(([k, v]) => (
        <div className="tt-row" key={k}>
          <span>{k}</span>
          <b>{v}</b>
        </div>
      ))}
    </>
  )
}

/** Horizontal bar with only the data end rounded (4px), anchored at x0. */
export function HBar({ x0, x1, y, h, fill }: { x0: number; x1: number; y: number; h: number; fill: string }) {
  const w = Math.max(x1 - x0, 0)
  const r = Math.min(4, w, h / 2)
  if (w <= 0.5) return <rect x={x0} y={y} width={1.5} height={h} fill={fill} />
  const d = `M${x0},${y} H${x0 + w - r} Q${x0 + w},${y} ${x0 + w},${y + r} V${y + h - r} Q${x0 + w},${y + h} ${x0 + w - r},${y + h} H${x0} Z`
  return <path d={d} fill={fill} />
}

export function Legend({ items }: { items: { label: string; color: string; kind?: 'box' | 'line' | 'ring' | 'dot' | 'dash' }[] }) {
  return (
    <div className="legend">
      {items.map((it) => (
        <span className="key" key={it.label}>
          {it.kind === 'dash' ? (
            <svg width="16" height="4"><line x1="0" x2="16" y1="2" y2="2" stroke={it.color} strokeWidth="2" strokeDasharray="4 3" /></svg>
          ) : (
            <span
              className={`swatch ${it.kind === 'line' ? 'line' : it.kind === 'ring' ? 'ring' : it.kind === 'dot' ? 'dot' : ''}`}
              style={it.kind === 'ring' ? { borderColor: it.color } : { background: it.color }}
            />
          )}
          {it.label}
        </span>
      ))}
    </div>
  )
}

export const C = {
  s1: 'var(--series-1)',
  s2: 'var(--series-2)',
  neutral: 'var(--neutral)',
  grid: 'var(--grid)',
  axis: 'var(--axis)',
  surface: 'var(--surface)',
  critical: 'var(--critical)',
  text2: 'var(--text-2)',
  text3: 'var(--text-3)',
}
