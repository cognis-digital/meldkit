"""Build a provenance-tracked knowledge graph from resolved entities.

Entities become nodes (carrying their source reports); entities co-mentioned in
the same report get a co-occurrence edge whose weight is the number of shared
reports. This is the fused, queryable picture an analyst reasons over.
"""

from __future__ import annotations

from collections import defaultdict

from .extract import extract
from .model import Edge, Entity, KnowledgeGraph, make_id
from .resolve import resolve


def build_graph(reports: list, gazetteer: dict | None = None) -> KnowledgeGraph:
    mentions = extract(reports, gazetteer or {})
    resolved = resolve(mentions)

    g = KnowledgeGraph()
    key_to_id = {}
    report_entities = defaultdict(set)
    for ent in resolved:
        eid = make_id(ent["type"], ent["canonical"].lower())
        key_to_id[(ent["type"], ent["canonical"].lower())] = eid
        g.add_entity(Entity(eid, ent["type"], ent["canonical"],
                            set(ent["sources"]),
                            {"aliases": ent["aliases"], "mentions": ent["mentions"]}))
        for rid in ent["sources"]:
            report_entities[rid].add(eid)

    # co-occurrence edges within each report
    for rid, eids in report_entities.items():
        ids = sorted(eids)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                g.add_edge(Edge(ids[i], ids[j], "co-mentioned", {rid}, 1.0))
    return g


def correlate(graph: KnowledgeGraph, entity_value: str, entity_type: str | None = None) -> list:
    """Return entities co-mentioned with the given entity, ranked by edge weight."""
    target = None
    for e in graph.entities.values():
        if e.value.lower() == entity_value.lower() and (entity_type is None or e.type == entity_type):
            target = e
            break
    if not target:
        return []
    out = []
    for nid, edge in graph.neighbors(target.id):
        ne = graph.entities[nid]
        out.append({"type": ne.type, "value": ne.value, "weight": edge.weight,
                    "shared_reports": sorted(edge.sources)})
    out.sort(key=lambda x: (-x["weight"], x["type"], x["value"]))
    return out
