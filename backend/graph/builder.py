from urllib.parse import urlparse

from ..db import get_db_session, get_detections, neo4j_driver

SCHEMA = (
    "CREATE CONSTRAINT domain_unique IF NOT EXISTS FOR (d:Domain) REQUIRE d.name IS UNIQUE",
    "CREATE CONSTRAINT ip_unique IF NOT EXISTS FOR (i:IP) REQUIRE i.addr IS UNIQUE",
    "CREATE CONSTRAINT upi_unique IF NOT EXISTS FOR (u:UPI) REQUIRE u.vpa IS UNIQUE",
)

async def init_schema() -> None:
    async with neo4j_driver.session() as session:
        for statement in SCHEMA:
            await session.run(statement)


async def add_observation(
    domain: str,
    ip: str | None = None,
    asn: str | None = None,
    cert_sha: str | None = None,
    upi_id: str | None = None,
    kit_hash: str | None = None,
) -> None:
    async with neo4j_driver.session() as session:
        await session.run(
            """
            MERGE (d:Domain {name: $domain})
            FOREACH (_ IN CASE WHEN $ip IS NULL THEN [] ELSE [1] END |
              MERGE (i:IP {addr: $ip}) MERGE (d)-[:RESOLVES_TO]->(i))
            FOREACH (_ IN CASE WHEN $asn IS NULL THEN [] ELSE [1] END |
              MERGE (a:ASN {id: $asn}) MERGE (d)-[:BELONGS_TO]->(a))
            FOREACH (_ IN CASE WHEN $cert_sha IS NULL THEN [] ELSE [1] END |
              MERGE (c:Cert {sha: $cert_sha}) MERGE (d)-[:USES_CERT]->(c))
            FOREACH (_ IN CASE WHEN $upi_id IS NULL THEN [] ELSE [1] END |
              MERGE (u:UPI {vpa: $upi_id}) MERGE (d)-[:COLLECTS_TO]->(u))
            FOREACH (_ IN CASE WHEN $kit_hash IS NULL THEN [] ELSE [1] END |
              MERGE (k:Kit {hash: $kit_hash}) MERGE (d)-[:USES_KIT]->(k))
            """,
            domain=domain, ip=ip, asn=asn, cert_sha=cert_sha,
            upi_id=upi_id, kit_hash=kit_hash,
        )


async def graph_snapshot() -> dict:
    """Return a frontend-friendly graph projection from Neo4j."""
    nodes: dict[str, dict] = {}
    links: list[dict[str, str]] = []
    async with neo4j_driver.session() as session:
        result = await session.run(
            "MATCH (a)-[r]->(b) RETURN labels(a)[0] AS a_label, "
            "coalesce(a.name, a.addr, a.vpa, a.id, a.sha, a.hash) AS a_id, "
            "type(r) AS relation, labels(b)[0] AS b_label, "
            "coalesce(b.name, b.addr, b.vpa, b.id, b.sha, b.hash) AS b_id"
        )
        records = await result.data()
    for row in records:
        for label, node_id in (
            (row["a_label"], row["a_id"]), (row["b_label"], row["b_id"])
        ):
            if node_id:
                nodes[str(node_id)] = {"id": str(node_id), "type": label}
        if row["a_id"] and row["b_id"]:
            links.append({
                "source": str(row["a_id"]), "target": str(row["b_id"]),
                "relation": row["relation"],
            })
    if nodes:
        return {"nodes": list(nodes.values()), "links": links}

    # Keep the analyst graph useful before infrastructure observations are
    # ingested into Neo4j: project persisted detections by domain and brand.
    async for db_session in get_db_session():
        detections = await get_detections(db_session)
    for detection in detections:
        domain = urlparse(detection.url).netloc or detection.url
        brand = detection.brand or "unidentified"
        nodes.setdefault(domain, {"id": domain, "type": "Domain"})
        brand_id = f"brand:{brand}"
        nodes.setdefault(brand_id, {"id": brand_id, "label": brand, "type": "Brand"})
        links.append({
            "source": domain,
            "target": brand_id,
            "relation": "MATCHES_BRAND",
        })
    return {"nodes": list(nodes.values()), "links": links}
