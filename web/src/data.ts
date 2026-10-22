export type Rate = { k: number; n: number; rate: number | null; lo: number; hi: number }

export type HwSession = {
  session: number; condition: string; is_attack: boolean
  key_qber: number; ref_qber: number; key_rate: number; p_value: number; verdict: boolean
  threshold: number; blocks_flagged: number; blocks_rule: number; blocks: number
  key_blocks: number[]; ref_blocks: number[]
}
export type HwBatch = {
  job_id: string; batch: number; backend: string; submitted: string | null; timing: 'none' | 'delay' | 'echo'
  honest_qber: number | null; honest_qber_x: number | null; untouched: [number, number]; touched: [number, number]
  quantum_seconds: number | null; slot_us: number | null; sessions: HwSession[]
}
export type PooledCondition = {
  condition: string; is_attack: boolean; key_qber: [number, number]; key_rate: [number, number]
  nirikshak: Rate; rule: Rate; sessions: Rate
}
export type Hardware = {
  alpha: number; rule_11: number; batches: HwBatch[]
  pooled: Record<string, { batches: string[]; conditions: PooledCondition[]; attacked_sessions: Rate; honest_sessions: Rate; max_attacked_p: number }>
  sim_session_false_alarms: Record<string, Rate>
}

export type Stress = {
  alpha: number; detectors: string[]; test_sets: string[]
  rows: { test_set: string; condition: string; rates: Record<string, number> }[]
  worst_false_alarms: { detector: string; rate: number; where: string }[]
}

export type Verdict = {
  link_id: string; window: number; h: number; start: string; end: string; key_qber: number; ref_qber: number
  p_value: number; alarm: boolean; blocks_flagged: number; blocks_flagged_frozen: number; blocks_flagged_11: number; truth: string
}
export type Monitor = {
  alpha: number; start: string; seed: number
  links: { link_id: string; description: string; source: string }[]
  verdicts: Verdict[]
  blocks: Record<string, { h: number[]; qber: number[]; threshold: (number | null)[]; alarm: number[]; alarm_frozen: number[]; frozen_threshold: number | null }>
  telemetry_example: Record<string, string | number>[]
}

export type SimCell = {
  readout: number; rounds: number; key_qber: number; ref_qber: number; key_rate: number; p_value: number; verdict: boolean
  threshold: number; blocks_flagged: number; blocks_rule: number; key_blocks: number[]; ref_blocks: number[]
}
export type Simulator = { alpha: number; readouts: number[]; rounds: number[]; grid: SimCell[] }

// Results are exported by scripts/export_web.py and bundled into the build (no runtime fetch).
const DATA: Record<string, unknown> = Object.fromEntries(
  Object.entries(import.meta.glob('./results/*.json', { eager: true, import: 'default' }))
    .map(([path, mod]) => [path.replace(/^.*\/(.*)\.json$/, '$1'), mod]),
)

export function useData<T>(name: string): T | null {
  return (DATA[name] as T) ?? null
}

export const pct = (x: number | null | undefined, d = 0) => (x == null ? 'n/a' : `${(x * 100).toFixed(d)}%`)
export const pctRange = (a: number, b: number, d = 1) =>
  (a * 100).toFixed(d) === (b * 100).toFixed(d) ? pct(a, d) : `${(a * 100).toFixed(d)}-${pct(b, d)}`
export const ci = (r: Rate) => `${pct(r.lo)}-${pct(r.hi)}`
export const pval = (p: number) => (p < 0.0001 ? '< 0.0001' : p.toFixed(4))
export const pretty = (c: string) => c.replace(/^honest$/, 'Honest').replace(/^intercept/, 'Intercept').replace(/^probe/, 'Probe')

export function timingLabel(t: HwBatch['timing']) {
  return t === 'echo' ? 'timing matched, spin echo' : t === 'delay' ? 'timing matched, plain idle' : 'timing not matched'
}

export function fmtTime(iso: string | null, withDay = true) {
  if (!iso) return ''
  const m = iso.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/)
  if (!m) return iso
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  return withDay ? `${+m[3]} ${months[+m[2] - 1]}, ${m[4]}:${m[5]}` : `${m[4]}:${m[5]}`
}
