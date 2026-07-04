"""STIX 2.1 export of the knowledge graph (deterministic UUIDv5 IDs)."""

from __future__ import annotations

import json
import uuid

_NS = uuid.UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")
DEFAULT_TS = "2026-01-01T00:00:00.000Z"

_STIX_TYPE = {
    "ipv4": ("ipv4-addr", "value"),
    "email": ("email-addr", "value"),
    "url": ("url", "value"),
    "sha256": ("file", "hashes.SHA-256"),
    "crypto-address": ("x-cognis-crypto-address", "value"),
}


def _sid(objtype: str, value: str) -> str:
    return f"{objtype}--{uuid.uuid5(_NS, objtype + ':' + value)}"


def bundle_from_graph(graph, created: str = DEFAULT_TS) -> dict:
    objects = []
    identity_id = _sid("identity", "Obsidia")
    objects.append({"type": "identity", "spec_version": "2.1", "id": identity_id,
                    "created": created, "modified": created,
                    "name": "Obsidia", "identity_class": "system"})

    def common(o):
        o.setdefault("spec_version", "2.1")
        o.setdefault("created", created)
        o.setdefault("modified", created)
        o.setdefault("created_by_ref", identity_id)
        return o

    for e in graph.entities.values():
        stix_obj, prop = _STIX_TYPE.get(e.type, ("x-cognis-entity", "value"))
        objects.append(common({
            "type": "indicator",
            "id": _sid("indicator", e.type + ":" + e.value.lower()),
            "name": f"{e.type}: {e.value}",
            "pattern_type": "stix",
            "pattern": f"[{stix_obj}:{prop} = '{e.value}']",
            "valid_from": created,
            "labels": ["observed-data"],
            "external_references": [{"source_name": "report", "external_id": s}
                                    for s in sorted(e.sources)],
        }))

    for edge in graph.edges:
        objects.append(common({
            "type": "relationship",
            "id": _sid("relationship", edge.source + edge.relation + edge.target),
            "relationship_type": "related-to",
            "source_ref": _sid("indicator", _rev(graph, edge.source)),
            "target_ref": _sid("indicator", _rev(graph, edge.target)),
        }))
    return {"type": "bundle", "id": _sid("bundle", "obsidia:" + created), "objects": objects}


def _rev(graph, entity_id):
    e = graph.entities[entity_id]
    return e.type + ":" + e.value.lower()


def to_json(bundle, indent=2):
    return json.dumps(bundle, indent=indent)
