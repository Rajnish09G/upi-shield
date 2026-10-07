import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

type Detection = { id: number; url: string; brand?: string; score: number; verdict: string; behavioral?: { external_form_posts?: string[]; sensitive_inputs?: string[] } };

export default function Home() {
  const [detections, setDetections] = useState<Detection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [verdictFilter, setVerdictFilter] = useState("all");
  const [analysisUrl, setAnalysisUrl] = useState("");
  const [analysisKeywords, setAnalysisKeywords] = useState("");
  const [analysisFile, setAnalysisFile] = useState<File | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisMessage, setAnalysisMessage] = useState("");
  const [analysisError, setAnalysisError] = useState("");
  const loadDetections = () => {
    setLoading(true);
    setError("");
    fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/detections`)
      .then((response) => { if (!response.ok) throw new Error(`API returned ${response.status}`); return response.json(); })
      .then(setDetections).catch((requestError: Error) => setError(requestError.message))
      .finally(() => setLoading(false));
  };
  useEffect(() => {
    loadDetections();
  }, []);
  const filtered = useMemo(() => detections.filter((item) => (verdictFilter === "all" || item.verdict === verdictFilter) && (item.url.toLowerCase().includes(query.toLowerCase()) || item.brand?.toLowerCase().includes(query.toLowerCase()))), [detections, query, verdictFilter]);
  const highRisk = detections.filter((item) => item.verdict === "phishing").length;
  const suspicious = detections.filter((item) => item.verdict === "suspicious").length;
  const analyzeUpload = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setAnalysisError("");
    setAnalysisMessage("");
    if (!analysisFile || !analysisUrl) {
      setAnalysisError("Paste a URL and choose a screenshot first.");
      return;
    }
    setAnalysisLoading(true);
    const form = new FormData();
    form.append("url", analysisUrl);
    form.append("brand_keywords", analysisKeywords);
    form.append("screenshot", analysisFile);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/analyze-upload`, { method: "POST", body: form });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail ?? `API returned ${response.status}`);
      setAnalysisMessage(`Analysis complete: ${payload.verdict} (${Number(payload.score).toFixed(2)})`);
      setAnalysisUrl("");
      setAnalysisKeywords("");
      setAnalysisFile(null);
      const fileInput = document.getElementById("screenshot-upload") as HTMLInputElement | null;
      if (fileInput) fileInput.value = "";
      loadDetections();
    } catch (requestError) {
      setAnalysisError(requestError instanceof Error ? requestError.message : "Analysis failed");
    } finally {
      setAnalysisLoading(false);
    }
  };

  return (
    <>
      <header className="page-header">
        <div><div className="eyebrow">OVERVIEW / TRIAGE QUEUE</div><h1>Detection overview</h1><p>Monitor, investigate and respond to suspected payment-brand abuse.</p></div>
        <div className="header-actions"><button className="button" onClick={loadDetections}>↻ Refresh</button><Link href="/graph" className="button primary">Open campaign graph →</Link></div>
      </header>
      <section className="stats-grid">
        <div className="stat-card"><div className="stat-label">TOTAL OBSERVATIONS</div><div className="stat-value">{detections.length}</div><div className="stat-note">Live from API</div></div>
        <div className="stat-card"><div className="stat-label">HIGH RISK</div><div className="stat-value">{highRisk}</div><div className="stat-note warning">Requires immediate review</div></div>
        <div className="stat-card"><div className="stat-label">NEEDS REVIEW</div><div className="stat-value">{suspicious}</div><div className="stat-note warning">Suspicious verdicts</div></div>
        <div className="stat-card"><div className="stat-label">SYSTEM STATUS</div><div className="stat-value" style={{ color: "var(--green)" }}>Online</div><div className="stat-note">Crawler and API connected</div></div>
      </section>
      <section className="panel analyzer-panel">
        <div>
          <div className="eyebrow">ANALYST INPUT</div>
          <h2>Check a website screenshot</h2>
          <p>Paste the page URL and upload a screenshot. The screenshot is matched against brand references and saved as evidence.</p>
        </div>
        <form className="analyzer-form" onSubmit={analyzeUpload}>
          <label>Website URL<input className="input" type="url" placeholder="https://example.com" value={analysisUrl} onChange={(event) => setAnalysisUrl(event.target.value)} /></label>
          <label>Brand keywords <span>(optional, comma separated)</span><input className="input" placeholder="upi, payment, otp, paytm" value={analysisKeywords} onChange={(event) => setAnalysisKeywords(event.target.value)} /></label>
          <label>Screenshot<input id="screenshot-upload" className="input file-input" type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => setAnalysisFile(event.target.files?.[0] ?? null)} /></label>
          <button className="button primary" type="submit" disabled={analysisLoading}>{analysisLoading ? "Analyzing..." : "Analyze screenshot →"}</button>
        </form>
        {analysisMessage && <div className="success-box">{analysisMessage}</div>}
        {analysisError && <div className="error-box">{analysisError}</div>}
      </section>
      <section className="toolbar"><div><h2>Recent detections</h2><span className="stat-label"> {filtered.length} records</span></div><div className="filters"><input className="input" placeholder="Search URL or brand..." value={query} onChange={(event) => setQuery(event.target.value)} /><select className="select" value={verdictFilter} onChange={(event) => setVerdictFilter(event.target.value)}><option value="all">All verdicts</option><option value="phishing">Phishing</option><option value="suspicious">Suspicious</option><option value="benign">Benign</option></select></div></section>
      <section className="panel table-wrap">
        {loading && <div className="empty">Loading detection telemetry...</div>}
        {error && <div className="error-box">Could not load detections: {error}</div>}
        {!loading && !error && filtered.length === 0 && <div className="empty">No detections match this view. Submit a capture through <code>/docs</code>.</div>}
        {!loading && !error && filtered.length > 0 && <table className="data-table"><thead><tr><th>URL / TARGET</th><th>BRAND</th><th>RISK SCORE</th><th>VERDICT</th><th>STATUS</th></tr></thead><tbody>{filtered.map((detection, index) => <tr key={`${detection.url}-${detection.id}`}><td className="url-cell"><Link href={`/detail/${detection.id}`}>{detection.url}</Link><small>Observation {String(index + 1).padStart(3, "0")} · just now</small></td><td>{detection.brand ?? "Unidentified"}</td><td className="score">{detection.score.toFixed(2)}</td><td><span className={`badge ${detection.verdict}`}>{detection.verdict}</span></td><td><Link href={`/detail/${detection.id}`} className="stat-label">Open →</Link></td></tr>)}</tbody></table>}
      </section>
    </>
  );
}
