"""Provenance-first graph model. Every entity and edge records the source
report(s) it came from, so any downstream product is fully traceable — a hard
requirement for intelligence work. Pure stdlib; deterministic IDs.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field


def make_id(kind: str, value: str) -> str:
    h = hashlib.sha1(f"{kind}:{value}".encode("utf-8")).hexdigest()[:16]
    return f"{kind}--{h}"


@dataclass
class Entity:
    id: str
    type: str
    value: str
    sources: set = field(default_factory=set)
    attributes: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"id": self.id, "type": self.type, "value": self.value,
                "sources": sorted(self.sources), "attributes": self.attributes}


@dataclass
class Edge:
    source: str
    target: str
    relation: str
    sources: set = field(default_factory=set)
    weight: float = 1.0

    def to_dict(self) -> dict:
        return {"source": self.source, "target": self.target, "relation": self.relation,
                "sources": sorted(self.sources), "weight": self.weight}


class KnowledgeGraph:
    def __init__(self) -> None:
        self.entities: dict = {}
        self.edges: list = []
        self._edge_index: dict = {}

    def add_entity(self, e: Entity) -> Entity:
        if e.id in self.entities:
            self.entities[e.id].sources |= e.sources
            return self.entities[e.id]
        self.entities[e.id] = e
        return e

    def add_edge(self, edge: Edge) -> Edge:
        key = (edge.source, edge.target, edge.relation)
        existing = self._edge_index.get(key)
        if existing is not None:
            existing.sources |= edge.sources
            existing.weight += edge.weight
            return existing
        self._edge_index[key] = edge
        self.edges.append(edge)
        return edge

    def neighbors(self, node_id: str) -> list:
        out = []
        for e in self.edges:
            if e.source == node_id:
                out.append((e.target, e))
            elif e.target == node_id:
                out.append((e.source, e))
        return out

    def to_dict(self) -> dict:
        return {"entities": [e.to_dict() for e in self.entities.values()],
                "edges": [e.to_dict() for e in self.edges]}
