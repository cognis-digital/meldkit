"""Entity resolution: collapse mentions that refer to the same real entity.

Regex-typed entities resolve by normalized value; gazetteer entities resolve to
their canonical name (aliases merge). Returns resolved entity records, each with
the set of source reports it was seen in.
"""

from __future__ import annotations


def resolve(mentions: list) -> list:
    groups: dict = {}
    for m in mentions:
        key = (m["type"], m.get("canonical", m["value"]).lower())
        g = groups.setdefault(key, {"type": m["type"],
                                    "canonical": m.get("canonical", m["value"]),
                                    "values": set(), "sources": set(), "count": 0})
        g["values"].add(m["value"])
        g["sources"].add(m["source_ref"])
        g["count"] += 1
    resolved = []
    for (_etype, _canon), g in sorted(groups.items()):
        resolved.append({"type": g["type"], "canonical": g["canonical"],
                         "aliases": sorted(g["values"]), "sources": sorted(g["sources"]),
                         "mentions": g["count"]})
    return resolved
