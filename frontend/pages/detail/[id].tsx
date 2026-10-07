import Link from "next/link";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

type Detection = { id: number; url: string; brand?: string; score: number; verdict: string; behavioral: Record<string, unknown>; screenshot: string; dom: string };

export default function DetailPage() {
  const router = useRouter();
  const [detection, setDetection] = useState<Detection | null>(null);
  useEffect(() => { if (router.query.id) fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/detections/${router.query.id}`).then((response) => response.json()).then(setDetection); }, [router.query.id]);
  const screenshotName = detection?.screenshot.split(/[\\/]/).pop();
  return <><header className="page-header"><div><div className="eyebrow">INVESTIGATION / OBSERVATION</div><h1>Detection {router.query.id ?? "detail"}</h1><p>Evidence review and signal breakdown.</p></div><Link href="/" className="button">← Back to queue</Link></header><div className="detail-grid"><section className="panel detail-card"><h2>Captured evidence</h2>{screenshotName ? <img src={`http://localhost:8000/artifacts/${screenshotName}`} alt="Captured page evidence" style={{ maxWidth: "100%", borderRadius: 7 }} /> : <div className="capture-placeholder">Loading evidence...</div>}</section><section className="panel detail-card"><h2>Signal summary</h2><div className="signal"><span>Verdict</span><strong className={`badge ${detection?.verdict ?? "benign"}`}>{detection?.verdict ?? "loading"}</strong></div><div className="signal"><span>Risk score</span><strong className="mono">{detection?.score.toFixed(2) ?? "—"}</strong></div><div className="signal"><span>External form posts</span><strong className="mono">{(detection?.behavioral?.external_form_posts as string[] | undefined)?.length ?? 0}</strong></div><div className="signal"><span>Sensitive inputs</span><strong className="mono">{(detection?.behavioral?.sensitive_inputs as string[] | undefined)?.length ?? 0}</strong></div>{detection && <a className="button primary" href={`http://localhost:8000/detections/${detection.id}/report`}>Download takedown report</a>}</section></div></>;
}
