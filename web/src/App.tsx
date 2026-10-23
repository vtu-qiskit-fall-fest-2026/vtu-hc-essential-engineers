import { useEffect, useState } from 'react'
import Hardware from './pages/Hardware'
import How from './pages/How'
import Monitor from './pages/Monitor'
import Stress from './pages/Stress'

const PAGES = [
  { path: '', label: 'On real hardware', el: Hardware },
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
  // Light by default; dark only after the visitor picks it. 'theme' held auto-detected values, so a new key.
  const stored = (() => { try { return localStorage.getItem('theme-choice') } catch { return null } })()
  const [theme, setTheme] = useState<string>(stored === 'dark' ? 'dark' : 'light')
  useEffect(() => { document.documentElement.dataset.theme = theme }, [theme])
  const toggle = () => setTheme((t) => {
    const next = t === 'dark' ? 'light' : 'dark'
    try { localStorage.setItem('theme-choice', next) } catch { /* private mode */ }
    return next
  })
  return [theme, toggle]
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
          <a className="wordmark" href="#/" aria-label="Nirikshak, home">
            <span className="latin">Nirikshak</span>
            <span className="deva" lang="hi">निरीक्षक</span>
          </a>
          <nav className="nav">
            {PAGES.map((p) => (
              <a key={p.path} href={`#/${p.path}`} className={p === page ? 'active' : ''} aria-current={p === page ? 'page' : undefined}>{p.label}</a>
            ))}
          </nav>
          <button className="theme-btn" onClick={toggle}>{theme === 'dark' ? 'Light' : 'Dark'}</button>
        </div>
      </header>
      <main>
        <div className="wrap"><Page /></div>
      </main>
      <footer>
        <div className="wrap">
          <span>Nirikshak means inspector. Built by Essential Engineers for Qiskit Fall Fest 2026, Track 1.</span>
          <a href={REPO}>Code, data and how to reproduce every number</a>
        </div>
      </footer>
    </>
  )
}
