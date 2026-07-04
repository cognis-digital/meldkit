"""Interoperability exports for fused observations & entities.

Formats:
  * JSON       : full fidelity (observations, entities, assessment).
  * CSV        : flat observation table for spreadsheets / quick triage.
  * STIX 2.1-like : a documented STIX-shaped bundle (observed-data + identity +
    sighting relationships). Deterministic UUIDv5 ids. See docs/INTEROP.md for
    the exact profile and the ways it departs from strict STIX.
  * symbol-agnostic entity schema : a NATO-symbol-AGNOSTIC entity record. It
    carries an entity_type and a neutral 'affiliation' hint (unknown/friend/
    neutral/suspect) but deliberately emits NO milsymbol / APP-6 / 2525 symbol
    code — this tool describes entities, it does not paint a targeting overlay.

All exporters are deterministic and stdlib-only.
"""

from __future__ import annotations

import csv
import io
import json
import uuid

_NS = uuid.UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")
_STIX_TS = "2026-01-01T00:00:00.000Z"

# Neutral affiliation vocabulary — situational, NOT a targeting designation.
AFFILIATIONS = ("unknown", "friend", "neutral", "suspect", "pending")


def _sid(objtype: str, value: str) -> str:
    return f"{objtype}--{uuid.uuid5(_NS, objtype + ':' + value)}"


# --------------------------------------------------------------------------- JSON
def to_json(observations, resolved=None, assessment=None, indent=2) -> str:
    payload = {
        "observations": [o.to_dict() for o in observations],
    }
    if resolved is not None:
        payload["entities"] = [e.to_dict() for e in resolved]
    if assessment is not None:
        payload["assessment"] = assessment
    return json.dumps(payload, indent=indent, sort_keys=False)


# ---------------------------------------------------------------------------- CSV
OBS_COLUMNS = ["id", "discipline", "source", "timestamp", "entity", "entity_type",
               "lat", "lon", "reliability", "credibility", "text"]


def observations_to_csv(observations) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=OBS_COLUMNS, extrasaction="ignore",
                       lineterminator="\n")
    w.writeheader()
    for o in observations:
        row = o.to_dict()
        row["text"] = (row.get("text") or "").replace("\n", " ")
        w.writerow(row)
    return buf.getvalue()


def entities_to_csv(resolved) -> str:
    cols = ["id", "canonical", "entity_type", "discipline_count",
            "observation_count", "disciplines", "sources", "aliases"]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for e in resolved:
        d = e.to_dict()
        w.writerow({
            "id": d["id"], "canonical": d["canonical"], "entity_type": d["entity_type"],
            "discipline_count": d["discipline_count"],
            "observation_count": d["observation_count"],
            "disciplines": "|".join(d["disciplines"]),
            "sources": "|".join(d["sources"]),
            "aliases": "|".join(d["aliases"]),
        })
    return buf.getvalue()


# --------------------------------------------------------------- symbol-agnostic
def _affiliation_for(entity) -> str:
    """Derive a NEUTRAL situational affiliation hint. Defaults to 'unknown';
    only downgrades to 'suspect' if reporting explicitly used a suspect/threat
    label. This is descriptive context, never a targeting call."""
    hints = " ".join(a.lower() for a in entity.aliases) + " " + entity.canonical.lower()
    if any(w in hints for w in ("suspect", "hostile-report", "illicit", "smuggl")):
        return "suspect"
    return "unknown"


def to_symbol_agnostic(resolved) -> dict:
    """A NATO-symbol-agnostic entity schema. entity_type + neutral affiliation,
    explicitly WITHOUT any APP-6/2525 symbol identification code."""
    return {
        "schema": "obsidia/symbol-agnostic-entity/1.0",
        "note": "symbol-agnostic by design: carries no military-symbology "
                "identification codes; situational-awareness descriptors only, "
                "not a targeting overlay",
        "entities": [{
            "id": e.id,
            "label": e.canonical,
            "entity_type": e.etype,
            "affiliation": _affiliation_for(e),   # neutral hint only
            "aliases": sorted(a for a in e.aliases if a != e.canonical),
            "disciplines": sorted(e.disciplines),
            "identifiers": dict(sorted(e.identifiers.items())),
        } for e in resolved],
    }


# ------------------------------------------------------------------ STIX 2.1-like
def to_stix(observations, resolved, created: str = _STIX_TS) -> dict:
    """A STIX 2.1-shaped bundle: identity + observed-data (per observation) +
    x-cognis-entity SCOs + sighting relationships. Documented profile in
    docs/INTEROP.md."""
    objects = []
    ident = _sid("identity", "Obsidia Fusion")
    objects.append({"type": "identity", "spec_version": "2.1", "id": ident,
                    "created": created, "modified": created,
                    "name": "Obsidia Fusion", "identity_class": "system"})

    for o in observations:
        objects.append({
            "type": "observed-data", "spec_version": "2.1",
            "id": _sid("observed-data", o.id),
            "created": created, "modified": created, "created_by_ref": ident,
            "first_observed": o.timestamp or created,
            "last_observed": o.timestamp or created,
            "number_observed": 1,
            "labels": [f"discipline:{o.discipline}", f"source:{o.source}"],
            "x_cognis_text": o.text,
            "x_cognis_geo": ([o.lat, o.lon] if o.has_geo else None),
            "x_cognis_reliability": o.reliability, "x_cognis_credibility": o.credibility,
        })

    for e in resolved:
        eid = _sid("x-cognis-entity", e.id)
        objects.append({
            "type": "x-cognis-entity", "spec_version": "2.1", "id": eid,
            "created": created, "modified": created, "created_by_ref": ident,
            "name": e.canonical, "entity_type": e.etype,
            "aliases": sorted(a for a in e.aliases if a != e.canonical),
            "x_cognis_disciplines": sorted(e.disciplines),
        })
        for oid in e.observation_ids:
            objects.append({
                "type": "relationship", "spec_version": "2.1",
                "id": _sid("relationship", eid + "sighting" + oid),
                "created": created, "modified": created, "created_by_ref": ident,
                "relationship_type": "derived-from",
                "source_ref": eid, "target_ref": _sid("observed-data", oid),
            })
    return {"type": "bundle", "id": _sid("bundle", "obsidia-fusion:" + created),
            "objects": objects}


def to_stix_json(observations, resolved, indent=2) -> str:
    return json.dumps(to_stix(observations, resolved), indent=indent)
