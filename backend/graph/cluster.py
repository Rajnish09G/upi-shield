import networkx as nx
from community import community_louvain


def cluster_sites(edges: list[tuple[str, str]]) -> list[list[str]]:
    """Return Louvain communities for an undirected observation edge list."""
    graph = nx.Graph()
    graph.add_edges_from(edges)
    if not graph:
        return []
    partition = community_louvain.best_partition(graph)
    clusters: dict[int, list[str]] = {}
    for node, cluster_id in partition.items():
        clusters.setdefault(cluster_id, []).append(node)
    return list(clusters.values())
