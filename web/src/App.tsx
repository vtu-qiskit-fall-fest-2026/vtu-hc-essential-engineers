import { useEffect, useState } from 'react'
import Hardware from './pages/Hardware'
import How from './pages/How'
import Monitor from './pages/Monitor'
import Stress from './pages/Stress'

const PAGES = [
  { path: '', label: 'Hardware results', el: Hardware },
  { path: 'monitor', label: 'Network monitor', el: Monitor },
  { path: 'stress', label: 'Stress test', el: Stress },
  { path: 'how', label: 'How it works', el: How },
]

const REPO = 'https://github.com/vtu-qiskit-fall-fest-2026/vtu-hc-essential-engineers'

function useRoute() {
  const get = () => window.location.hash.replace(/^#\/?/, '')
  const [route, setRoute] = useState(get)
  useEffect(() => {
    const on = () => { setRoute(get()); window.scrollTo(0, 0) }
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  return route
}

function useTheme(): [string, () => void] {
  const stored = (() => { try { return localStorage.getItem('theme') } catch { return null } })()
  const [theme, setTheme] = useState<string>(stored ?? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'))
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    try { localStorage.setItem('theme', theme) } catch { /* private mode */ }
  }, [theme])
  return [theme, () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))]
}

export default function App() {
  const route = useRoute()
  const [theme, toggle] = useTheme()
  const page = PAGES.find((p) => p.path === route) ?? PAGES[0]
  const Page = page.el
  return (
    <>
      <header className="topbar">
        <div className="wrap">
          <a className="brand" href="#/">
            <span className="brand-mark">
              <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden><circle cx="8" cy="8" r="5.2" fill="none" stroke="#fff" strokeWidth="1.8" /><circle cx="8" cy="8" r="1.8" fill="#fff" /></svg>
            </span>
            <span>Nirikshak</span>
          </a>
          <nav className="nav">
            {PAGES.map((p) => (
              <a key={p.path} href={`#/${p.path}`} className={p === page ? 'active' : ''}>{p.label}</a>
            ))}
          </nav>
          <button className="icon-btn" onClick={toggle} aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}>
            {theme === 'dark'
              ? <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden><circle cx="8" cy="8" r="3.2" fill="currentColor" /><g stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">{[0, 45, 90, 135, 180, 225, 270, 315].map((a) => <line key={a} x1="8" y1="1.2" x2="8" y2="2.8" transform={`rotate(${a} 8 8)`} />)}</g></svg>
              : <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden><path d="M13.5 9.8A5.8 5.8 0 0 1 6.2 2.5a5.8 5.8 0 1 0 7.3 7.3Z" fill="currentColor" /></svg>}
          </button>
        </div>
      </header>
      <main>
        <div className="wrap"><Page /></div>
      </main>
      <footer>
        <div className="wrap">
          <span>Nirikshak · Essential Engineers (VTU-QFF-HC-0173) · Qiskit Fall Fest 2026, Track 1</span>
          <span><a href={REPO}>Source, data and reproduction steps</a></span>
        </div>
      </footer>
    </>
  )
}
