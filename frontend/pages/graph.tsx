import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import type { SimulationNodeDatum } from "d3";

type GraphNode = SimulationNodeDatum & { id: string; label?: string; type: string };

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
    const simulationNodes = nodes.map((node) => ({ ...node }));
    const simulationLinks = links.map((link) => ({ ...link }));
    const simulation = d3.forceSimulation(simulationNodes)
      .force("link", d3.forceLink(simulationLinks).id((node: any) => node.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-160))
      .force("center", d3.forceCenter(280, 165));
    const group = svg.append("g");
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
  return <><header className="page-header"><div><div className="eyebrow">NETWORK INTELLIGENCE / CAMPAIGNS</div><h1>Campaign graph</h1><p>Explore infrastructure shared across detected sites and payment identities.</p></div><Link href="/" className="button">← Back to triage</Link></header><section className="panel graph-panel"><div className="toolbar"><h2>Relationship map <span className="stat-label">· detection projection</span></h2><button className="button">Fit to screen</button></div><svg ref={ref} viewBox="0 0 560 330" role="img" aria-label="Campaign relationship graph" /><div className="graph-legend"><span><i className="legend-dot" style={{ background: "var(--cyan)" }} />Domain</span><span><i className="legend-dot" style={{ background: "#a6d9b2" }} />Brand match</span><span>Neo4j data is used when available</span></div></section></>;
}
