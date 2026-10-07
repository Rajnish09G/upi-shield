import type { AppProps } from "next/app";
import Link from "next/link";
import "../styles/globals.css";

export default function App({ Component, pageProps }: AppProps) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link href="/" className="brand">
          <span className="brand-mark">U</span>
          <span>UPI <strong>Shield</strong></span>
        </Link>
        <div className="workspace-label">SECURITY OPERATIONS</div>
        <nav className="nav-list">
          <Link href="/" className="nav-item"><span>◉</span> Triage queue</Link>
          <Link href="/graph" className="nav-item"><span>⌘</span> Campaign graph</Link>
        </nav>
        <div className="sidebar-bottom">
          <div className="system-status"><span className="status-dot" /> Systems operational</div>
          <div className="user-card"><div className="avatar">RA</div><div><strong>Research analyst</strong><small>Workspace admin</small></div><span>•••</span></div>
        </div>
      </aside>
      <main className="main-content"><Component {...pageProps} /></main>
    </div>
  );
}
