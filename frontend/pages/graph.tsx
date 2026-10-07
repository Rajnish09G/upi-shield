import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import type { SimulationNodeDatum } from "d3";

type GraphNode = SimulationNodeDatum & { id: string; type: string };

export default function GraphPage() {
  const ref = useRef<SVGSVGElement>(null);
  const [graph, setGraph] = useState<{ nodes: GraphNode[]; links: { source: string; target: string }[] }>({ nodes: [], links: [] });
  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/graph`)
      .then((response) => response.json()).then(setGraph).catch(() => setGraph({ nodes: [], links: [] }));
  }, []);
  useEffect(() => {
    if (!ref.current) return;
    const svg = d3.select(ref.current);
    svg.selectAll("*").remove();
    const nodes: GraphNode[] = graph.nodes.length ? graph.nodes : [{ id: "campaign", type: "Campaign" }];
    const links = graph.links;
    const simulation = d3.forceSimulation(nodes.map((node) => ({ ...node })))
      .force("link", d3.forceLink(links.map((link) => ({ ...link }))).id((node: any) => node.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-160))
      .force("center", d3.forceCenter(280, 165));
    const group = svg.append("g");
    const linkLines = group.selectAll("line").data(links).join("line").attr("stroke", "#31526b").attr("stroke-width", 2);
    const nodeItems = group.selectAll("g").data(nodes).join("g");
    nodeItems.append("circle").attr("r", (node) => node.type === "Domain" ? 15 : 11).attr("fill", (node) => node.type === "Domain" ? "#35d0d1" : "#1d4560").attr("stroke", "#6f9ab0");
    nodeItems.append("text").attr("y", 27).attr("text-anchor", "middle").attr("fill", "#a8bed1").attr("font-size", 10).text((node) => node.id);
    simulation.on("tick", () => {
      linkLines.attr("x1", (link: any) => link.source.x).attr("y1", (link: any) => link.source.y).attr("x2", (link: any) => link.target.x).attr("y2", (link: any) => link.target.y);
      nodeItems.attr("transform", (node: any) => `translate(${node.x},${node.y})`);
    });
    return () => { simulation.stop(); };
  }, [graph]);
  return <><header className="page-header"><div><div className="eyebrow">NETWORK INTELLIGENCE / CAMPAIGNS</div><h1>Campaign graph</h1><p>Explore infrastructure shared across detected sites and payment identities.</p></div><Link href="/" className="button">← Back to triage</Link></header><section className="panel graph-panel"><div className="toolbar"><h2>Relationship map <span className="stat-label">· sample projection</span></h2><button className="button">Fit to screen</button></div><svg ref={ref} viewBox="0 0 560 330" role="img" aria-label="Campaign relationship graph" /><div className="graph-legend"><span><i className="legend-dot" style={{ background: "var(--cyan)" }} />Campaign cluster</span><span><i className="legend-dot" style={{ background: "#1d4560" }} />Observed entity</span><span>Neo4j connection pending</span></div></section></>;
}
