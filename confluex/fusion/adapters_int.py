"""Normalizers that turn discipline-specific SYNTHETIC records into the common
Observation schema.

Each adapter accepts a list of plain dicts (as would come from a synthetic feed,
a sample file, or a de-identified export) and returns Observations. The adapters
are intentionally permissive about input shape and defensive about content:

  * SIGINT here is strictly METADATA (emitter id, link, bearing, time) — there is
    NO communications content, and none is ever parsed or stored.
  * No adapter produces targeting/engagement fields.

All adapters are deterministic and offline.
"""

from __future__ import annotations

from .admiralty import default_grade_for
from .schema import Observation


def _grade(rec, discipline):
    rel = rec.get("reliability", "")
    cred = rec.get("credibility", "")
    if not rel and not cred:
        code = default_grade_for(discipline)
        rel, cred = code[0], code[1]
    return rel, cred


def osint(records: list) -> list:
    """Open-source text: {title/text, url, timestamp, entity?, lat?, lon?}."""
    out = []
    for r in records:
        text = (r.get("text") or r.get("title") or "").strip()
        rel, cred = _grade(r, "OSINT")
        out.append(Observation(
            discipline="OSINT", source=r.get("source", "osint"),
            timestamp=r.get("timestamp", ""), text=text,
            entity=r.get("entity", ""), entity_type=r.get("entity_type", ""),
            lat=r.get("lat"), lon=r.get("lon"),
            attributes={k: v for k, v in r.items() if k in ("url", "domain", "lang")},
            reliability=rel, credibility=cred))
    return out


def sigint_meta(records: list) -> list:
    """SIGINT METADATA ONLY — emitter externals, never content.

    Expected keys: {emitter_id, link, timestamp, bearing?, freq_band?, lat?, lon?}.
    A synthetic 'content' key, if present, is explicitly IGNORED and dropped.
    """
    out = []
    for r in records:
        emitter = r.get("emitter_id", r.get("emitter", "unknown-emitter"))
        band = r.get("freq_band", "")
        bearing = r.get("bearing")
        parts = [f"Signal metadata: emitter {emitter}"]
        if band:
            parts.append(f"band {band}")
        if bearing is not None:
            parts.append(f"bearing {bearing}deg")
        if r.get("link"):
            parts.append(f"link {r['link']}")
        rel, cred = _grade(r, "SIGINT")
        attrs = {"emitter_id": emitter}
        for k in ("link", "freq_band", "bearing", "duration_s", "pulses"):
            if r.get(k) is not None:
                attrs[k] = r[k]
        # Defensive: never carry communications content.
        attrs.pop("content", None)
        out.append(Observation(
            discipline="SIGINT", source=r.get("source", "sigint"),
            timestamp=r.get("timestamp", ""), text="; ".join(parts),
            entity=emitter, entity_type="emitter",
            lat=r.get("lat"), lon=r.get("lon"),
            attributes=attrs, reliability=rel, credibility=cred))
    return out


def geoint(records: list) -> list:
    """GEOINT/location tracks: {entity, entity_type, lat, lon, timestamp,
    heading?, speed_kn?}. One record == one sighting/track point."""
    out = []
    for r in records:
        ent = r.get("entity", r.get("track_id", "unknown"))
        etype = r.get("entity_type", "track")
        bits = [f"{etype} {ent} at {r.get('lat')},{r.get('lon')}"]
        if r.get("speed_kn") is not None:
            bits.append(f"speed {r['speed_kn']}kn")
        if r.get("heading") is not None:
            bits.append(f"heading {r['heading']}deg")
        rel, cred = _grade(r, "GEOINT")
        attrs = {k: r[k] for k in ("heading", "speed_kn", "track_id", "altitude_m")
                 if r.get(k) is not None}
        out.append(Observation(
            discipline="GEOINT", source=r.get("source", "geoint"),
            timestamp=r.get("timestamp", ""), text="; ".join(bits),
            entity=ent, entity_type=etype,
            lat=r.get("lat"), lon=r.get("lon"),
            attributes=attrs, reliability=rel, credibility=cred))
    return out


def humint(records: list) -> list:
    """HUMINT-style reports: {report, source_id?, entity?, lat?, lon?, timestamp,
    reliability?, credibility?}. Human reporting is graded cautiously by default."""
    out = []
    for r in records:
        text = (r.get("report") or r.get("text") or "").strip()
        rel, cred = _grade(r, "HUMINT")
        out.append(Observation(
            discipline="HUMINT", source=r.get("source", r.get("source_id", "humint")),
            timestamp=r.get("timestamp", ""), text=text,
            entity=r.get("entity", ""), entity_type=r.get("entity_type", ""),
            lat=r.get("lat"), lon=r.get("lon"),
            attributes={"source_id": r.get("source_id", "")} if r.get("source_id") else {},
            reliability=rel, credibility=cred))
    return out


def masint(records: list) -> list:
    """MASINT-style sensor events: {sensor, phenomenology, measurement, unit?,
    timestamp, lat?, lon?}. Acoustic/seismic/EO-IR/RF measurement & signature."""
    out = []
    for r in records:
        phen = r.get("phenomenology", "signature")
        meas = r.get("measurement")
        unit = r.get("unit", "")
        text = f"MASINT {phen} event"
        if meas is not None:
            text += f": {meas}{unit}"
        rel, cred = _grade(r, "MASINT")
        attrs = {"phenomenology": phen}
        for k in ("measurement", "unit", "sensor", "confidence"):
            if r.get(k) is not None:
                attrs[k] = r[k]
        out.append(Observation(
            discipline="MASINT", source=r.get("sensor", r.get("source", "masint")),
            timestamp=r.get("timestamp", ""), text=text,
            entity=r.get("entity", phen), entity_type=r.get("entity_type", "sensor-event"),
            lat=r.get("lat"), lon=r.get("lon"),
            attributes=attrs, reliability=rel, credibility=cred))
    return out


def structured(records: list) -> list:
    """Already-structured reporting/logs/registries: mostly passthrough with a
    synthesized text line for retrieval. {entity, entity_type, fields..., timestamp}."""
    out = []
    for r in records:
        ent = r.get("entity", "")
        etype = r.get("entity_type", "record")
        text = r.get("text") or f"{etype} {ent} " + ", ".join(
            f"{k}={v}" for k, v in sorted(r.items())
            if k not in ("entity", "entity_type", "timestamp", "source",
                         "lat", "lon", "reliability", "credibility", "text"))
        rel, cred = _grade(r, "STRUCTURED")
        attrs = {k: v for k, v in r.items()
                 if k not in ("entity", "entity_type", "timestamp", "source",
                              "lat", "lon", "reliability", "credibility", "text")}
        out.append(Observation(
            discipline="STRUCTURED", source=r.get("source", "structured"),
            timestamp=r.get("timestamp", ""), text=text.strip(),
            entity=ent, entity_type=etype,
            lat=r.get("lat"), lon=r.get("lon"),
            attributes=attrs, reliability=rel, credibility=cred))
    return out


ADAPTERS = {
    "osint": osint,
    "sigint": sigint_meta,
    "sigint_meta": sigint_meta,
    "geoint": geoint,
    "humint": humint,
    "masint": masint,
    "structured": structured,
}


def normalize(discipline: str, records: list) -> list:
    """Dispatch to the adapter for a discipline name."""
    key = (discipline or "").lower()
    if key not in ADAPTERS:
        raise KeyError(f"no adapter for discipline {discipline!r}; "
                       f"have {sorted(set(ADAPTERS))}")
    return ADAPTERS[key](records)
