import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import type { SimulationNodeDatum } from "d3";

type GraphNode = SimulationNodeDatum & { id: string; label?: string; type: string };

export default function GraphPage() {
  const ref = useRef<SVGSVGElement>(null);
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);
  const groupRef = useRef<SVGGElement | null>(null);
  const [graph, setGraph] = useState<{ nodes: GraphNode[]; links: { source: string; target: string }[] }>({ nodes: [], links: [] });
  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/graph`)
      .then((response) => response.json()).then(setGraph).catch(() => setGraph({ nodes: [], links: [] }));
  }, []);
  useEffect(() => {
    if (!ref.current) return;
    const svg = d3.select(ref.current);
    svg.selectAll("*").remove();
    const zoom = d3.zoom<SVGSVGElement, unknown>().scaleExtent([0.5, 3]);
    svg.call(zoom);
    zoomRef.current = zoom;
    const nodes: GraphNode[] = graph.nodes.length ? graph.nodes : [{ id: "campaign", type: "Campaign" }];
    const links = graph.links;
    const simulationNodes = nodes.map((node) => ({ ...node }));
    const simulationLinks = links.map((link) => ({ ...link }));
    const simulation = d3.forceSimulation(simulationNodes)
      .force("link", d3.forceLink(simulationLinks).id((node: any) => node.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-160))
      .force("center", d3.forceCenter(280, 165));
    const group = svg.append("g");
    groupRef.current = group.node();
    const linkLines = group.selectAll("line").data(simulationLinks).join("line").attr("stroke", "#9bc9a7").attr("stroke-width", 2);
    const nodeItems = group.selectAll("g").data(simulationNodes).join("g");
    nodeItems.append("circle").attr("r", (node) => node.type === "Domain" ? 15 : 11).attr("fill", (node) => node.type === "Domain" ? "#168d49" : "#a6d9b2").attr("stroke", "#4b9f63");
    nodeItems.append("text").attr("y", 27).attr("text-anchor", "middle").attr("fill", "#426951").attr("font-size", 10).text((node) => node.label ?? node.id);
    simulation.on("tick", () => {
      linkLines.attr("x1", (link: any) => link.source.x).attr("y1", (link: any) => link.source.y).attr("x2", (link: any) => link.target.x).attr("y2", (link: any) => link.target.y);
      nodeItems.attr("transform", (node: any) => `translate(${node.x},${node.y})`);
    });
    return () => { simulation.stop(); };
  }, [graph]);
  const fitGraph = () => {
    if (!ref.current || !groupRef.current || !zoomRef.current) return;
    const bounds = groupRef.current.getBBox();
    if (!bounds.width || !bounds.height) return;
    const padding = 35;
    const scale = Math.min(
      560 / (bounds.width + padding * 2),
      330 / (bounds.height + padding * 2),
      1.8,
    );
    const x = 280 - scale * (bounds.x + bounds.width / 2);
    const y = 165 - scale * (bounds.y + bounds.height / 2);
    d3.select(ref.current).transition().duration(450).call(
      zoomRef.current.transform,
      d3.zoomIdentity.translate(x, y).scale(scale),
    );
  };
  return <><header className="page-header"><div><div className="eyebrow">NETWORK INTELLIGENCE / CAMPAIGNS</div><h1>Campaign graph</h1><p>Explore infrastructure shared across detected sites and payment identities.</p></div><Link href="/" className="button">← Back to triage</Link></header><section className="panel graph-panel"><div className="toolbar"><h2>Relationship map <span className="stat-label">· detection projection</span></h2><button className="button" onClick={fitGraph}>Fit to screen</button></div><svg ref={ref} viewBox="0 0 560 330" role="img" aria-label="Campaign relationship graph" /><div className="graph-legend"><span><i className="legend-dot" style={{ background: "var(--cyan)" }} />Domain</span><span><i className="legend-dot" style={{ background: "#a6d9b2" }} />Brand match</span><span>Neo4j data is used when available</span></div></section><section className="panel graph-explainer"><div className="eyebrow">HOW IT WORKS</div><h2>Read the campaign graph</h2><div className="graph-steps"><div><strong>1. Domain</strong><p>Each observed URL becomes a domain node, such as <code>www.paytm.com</code>.</p></div><div><strong>2. Brand match</strong><p>The visual detector assigns the closest known brand from the screenshot reference set.</p></div><div><strong>3. Relationship</strong><p>A line labelled <code>MATCHES_BRAND</code> connects the domain to the matched brand.</p></div><div><strong>4. Campaign view</strong><p>Shared hosts, certificates, IPs, wallets or kit hashes become additional Neo4j nodes when ingested.</p></div></div></section></>;
}
