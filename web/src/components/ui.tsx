export function Verdict({ alarm, p }: { alarm: boolean; p?: number }) {
  return alarm ? (
    <span className="badge attack">
      <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden><path d="M5 1 L9.5 9 H0.5 Z" fill="currentColor" /></svg>
      Attack{p != null ? ` · p ${p < 0.0001 ? '< 0.0001' : p.toFixed(4)}` : ''}
    </span>
  ) : (
    <span className="badge clean">
      <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden><circle cx="5" cy="5" r="3.5" fill="none" stroke="currentColor" strokeWidth="1.6" /></svg>
      Clean{p != null ? ` · p ${p.toFixed(2)}` : ''}
    </span>
  )
}
