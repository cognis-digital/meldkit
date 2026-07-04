"""Cross-source entity resolution & de-confliction over Observations.

Groups observations that refer to the same real-world entity even when they
arrive from different INT disciplines under slightly different labels, then
de-conflicts (flags) cases where the same label is used by what look like
distinct entities.

Resolution signals (transparent, deterministic):
  * normalized entity name match (case/space/punct-insensitive, alias-aware)
  * shared explicit identifier attributes (emitter_id, track_id, imo, mmsi, ...)
  * name similarity via token-set Jaccard for near-duplicate spellings

This is analytic aggregation for understanding — it builds a fused entity list,
not a target list.
"""

from __future__ import annotations

import re
from collections import defaultdict

_ID_KEYS = ("emitter_id", "track_id", "imo", "mmsi", "callsign", "hull", "tail")
_WS = re.compile(r"[\s\-_/.]+")
_PUNCT = re.compile(r"[^\w\s]")


def norm_name(name: str) -> str:
    s = _PUNCT.sub(" ", (name or "").lower())
    s = _WS.sub(" ", s).strip()
    return s


def _tokens(name: str) -> set:
    return set(norm_name(name).split())


def name_similarity(a: str, b: str) -> float:
    """Token-set Jaccard similarity in [0,1]."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


class ResolvedEntity:
    def __init__(self, eid: str, canonical: str, etype: str):
        self.id = eid
        self.canonical = canonical
        self.etype = etype
        self.aliases: set = set()
        self.observation_ids: list = []
        self.disciplines: set = set()
        self.sources: set = set()
        self.identifiers: dict = {}

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "canonical": self.canonical,
            "entity_type": self.etype,
            "aliases": sorted(a for a in self.aliases if a and a != self.canonical),
            "observation_ids": list(self.observation_ids),
            "disciplines": sorted(self.disciplines),
            "sources": sorted(self.sources),
            "identifiers": dict(sorted(self.identifiers.items())),
            "observation_count": len(self.observation_ids),
            "discipline_count": len(self.disciplines),
        }


def _entity_id(canonical: str, etype: str) -> str:
    import hashlib
    h = hashlib.blake2b(f"{etype}:{norm_name(canonical)}".encode(), digest_size=6).hexdigest()
    return f"ent--{h}"


def resolve_entities(observations, name_threshold: float = 0.6) -> list:
    """Return a list of ResolvedEntity, merging observations of the same entity.

    Only observations that name an entity participate; unnamed observations
    (e.g. a bare sensor event) are skipped here and handled by track/geo logic.
    """
    named = [o for o in observations if o.entity]

    # Bucket by explicit identifier first (strongest signal).
    id_groups = {}
    for o in named:
        for k in _ID_KEYS:
            v = o.attributes.get(k)
            if v:
                id_groups.setdefault((k, str(v)), []).append(o)

    # Union-find over observations, seeded by shared identifiers, then by name.
    parent = {o.id: o.id for o in named}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    for group in id_groups.values():
        for o in group[1:]:
            union(group[0].id, o.id)

    # Name-based merge within the same entity_type. Operate over DISTINCT
    # normalized names (not every observation pair) so this stays ~O(names^2)
    # rather than O(observations^2) and scales to large scenarios.
    by_type_name = defaultdict(list)          # (etype, norm_name) -> [obs...]
    for o in named:
        by_type_name[(o.entity_type or "", norm_name(o.entity))].append(o)

    # First, collapse identical normalized names outright.
    for group in by_type_name.values():
        rep = group[0].id
        for o in group[1:]:
            union(rep, o.id)

    # Then, pairwise-compare only the distinct names within a type.
    names_by_type = defaultdict(list)
    for (etype, nname), group in by_type_name.items():
        names_by_type[etype].append((nname, group[0]))
    for etype, entries in names_by_type.items():
        for i in range(len(entries)):
            na, oa = entries[i]
            for j in range(i + 1, len(entries)):
                nb, ob = entries[j]
                if not na or not nb:
                    continue
                if (na in nb or nb in na
                        or name_similarity(na, nb) >= name_threshold):
                    union(oa.id, ob.id)

    clusters = defaultdict(list)
    for o in named:
        clusters[find(o.id)].append(o)

    resolved = []
    obs_by_id = {o.id: o for o in named}
    for root, obs_list in clusters.items():
        # canonical = the most-frequent longest name (stable, deterministic)
        names = [o.entity for o in obs_list]
        canonical = sorted(names, key=lambda n: (-names.count(n), -len(n), n))[0]
        etype = obs_by_id[root].entity_type or (obs_list[0].entity_type)
        ent = ResolvedEntity(_entity_id(canonical, etype), canonical, etype)
        for o in sorted(obs_list, key=lambda x: (x.timestamp, x.id)):
            ent.aliases.add(o.entity)
            ent.observation_ids.append(o.id)
            ent.disciplines.add(o.discipline)
            ent.sources.add(o.source)
            for k in _ID_KEYS:
                v = o.attributes.get(k)
                if v:
                    ent.identifiers[k] = str(v)
        resolved.append(ent)

    resolved.sort(key=lambda e: (-len(e.observation_ids), e.canonical))
    return resolved


def deconflict(resolved: list) -> list:
    """Flag potential identity conflicts: the same normalized name mapped to more
    than one entity_type, or one identifier value claimed by multiple entities.

    Returns a list of conflict records for analyst review — de-confliction here
    means *surfacing ambiguity*, never auto-deciding it.
    """
    conflicts = []
    by_name = defaultdict(list)
    for e in resolved:
        by_name[norm_name(e.canonical)].append(e)
    for name, ents in by_name.items():
        types = {e.etype for e in ents}
        if len(ents) > 1 and len(types) > 1:
            conflicts.append({
                "kind": "name-type-ambiguity",
                "name": name,
                "entities": [{"id": e.id, "entity_type": e.etype} for e in ents],
                "note": "same name used across different entity types",
            })

    by_ident = defaultdict(list)
    for e in resolved:
        for k, v in e.identifiers.items():
            by_ident[(k, v)].append(e.id)
    for (k, v), ids in by_ident.items():
        if len(set(ids)) > 1:
            conflicts.append({
                "kind": "identifier-collision",
                "identifier": f"{k}={v}",
                "entities": sorted(set(ids)),
                "note": "one identifier claimed by multiple resolved entities",
            })
    return conflicts
