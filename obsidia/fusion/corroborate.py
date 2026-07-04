"""Corroboration scoring and contradiction detection across sources.

For each resolved entity we ask: how well-corroborated is the picture, and does
any reporting contradict the rest? Both are computed transparently from the
observations and their Admiralty grades.

Corroboration = breadth of independent support:
  * number of distinct INT disciplines observing the entity
  * number of distinct sources
  * average per-observation Admiralty confidence
  * a small bonus for spatio-temporal agreement (observations that co-locate)

Contradiction = tension in the reporting:
  * spatial: two observations place the same entity implausibly far apart for
    the elapsed time (implied speed exceeds a plausibility ceiling)
  * attribute: two observations assert mutually exclusive attribute values
    (e.g. entity_type disagreement, or a flagged boolean like 'armed_status'
    reported both ways) — surfaced, never adjudicated

Everything here supports analyst UNDERSTANDING; nothing is auto-actioned.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .admiralty import observation_confidence
from .schema import haversine_km

# Plausibility ceiling for implied movement (km/h). Deliberately generous so we
# only flag clearly-impossible jumps, not fast-but-real movers.
MAX_PLAUSIBLE_KMH = 1200.0  # ~ jet airliner; anything faster between fixes is suspect


def _parse_ts(ts: str):
    if not ts:
        return None
    s = ts.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(ts[:19], fmt)
                break
            except ValueError:
                continue
        else:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def corroboration_score(entity, obs_by_id: dict) -> dict:
    obs = [obs_by_id[i] for i in entity.observation_ids if i in obs_by_id]
    disciplines = {o.discipline for o in obs}
    sources = {o.source for o in obs}
    confs = [observation_confidence(o) for o in obs]
    avg_conf = sum(confs) / len(confs) if confs else 0.0

    # Independent-support factor: more disciplines & sources -> closer to 1.
    disc_factor = 1.0 - 0.6 ** len(disciplines)
    src_factor = 1.0 - 0.7 ** len(sources)

    # Spatio-temporal agreement bonus: fraction of geo pairs within 25 km.
    # Cap the pair count so a very long track cannot make this quadratic-heavy.
    geo = [o for o in obs if o.has_geo]
    if len(geo) > 60:
        geo = geo[:60]
    agree = 0
    pairs = 0
    for i in range(len(geo)):
        for j in range(i + 1, len(geo)):
            pairs += 1
            if haversine_km(geo[i].lat, geo[i].lon, geo[j].lat, geo[j].lon) <= 25.0:
                agree += 1
    colocate = (agree / pairs) if pairs else 0.0

    score = round(0.45 * disc_factor + 0.25 * src_factor
                  + 0.20 * avg_conf + 0.10 * colocate, 4)
    # Band is driven first by breadth of independent support: a lone source is
    # 'single-source' regardless of its own grade, because it is uncorroborated.
    if len(sources) <= 1 and len(disciplines) <= 1:
        band = "single-source"
    elif score >= 0.72:
        band = "strong"
    elif score >= 0.45:
        band = "moderate"
    else:
        band = "weak"
    return {
        "entity_id": entity.id,
        "canonical": entity.canonical,
        "score": score,
        "band": band,
        "disciplines": sorted(disciplines),
        "discipline_count": len(disciplines),
        "source_count": len(sources),
        "avg_confidence": round(avg_conf, 4),
        "colocation": round(colocate, 4),
    }


def _implied_kmh(a, b) -> float | None:
    if not (a.has_geo and b.has_geo):
        return None
    ta, tb = _parse_ts(a.timestamp), _parse_ts(b.timestamp)
    if ta is None or tb is None:
        return None
    hours = abs((tb - ta).total_seconds()) / 3600.0
    dist = haversine_km(a.lat, a.lon, b.lat, b.lon)
    if hours < 1e-6:
        return float("inf") if dist > 1.0 else 0.0
    return dist / hours


# Attribute keys where two different asserted values indicate a real contradiction.
_MUTEX_KEYS = ("entity_type", "status", "flag_state", "affiliation")


def detect_contradictions(entity, obs_by_id: dict) -> list:
    obs = [obs_by_id[i] for i in entity.observation_ids if i in obs_by_id]
    out = []

    # Spatial/kinematic contradictions. Comparing time-adjacent observations is
    # sufficient to catch implausible jumps and keeps this linear in track length.
    geo_obs = sorted((o for o in obs if o.has_geo), key=lambda o: (o.timestamp, o.id))
    adjacency = [(geo_obs[i], geo_obs[i + 1]) for i in range(len(geo_obs) - 1)]
    for oi, oj in adjacency:
        kmh = _implied_kmh(oi, oj)
        if kmh is not None and kmh > MAX_PLAUSIBLE_KMH:
            out.append({
                "kind": "spatial-implausible-move",
                "entity_id": entity.id,
                "observations": sorted([oi.id, oj.id]),
                "implied_kmh": round(kmh, 1) if kmh != float("inf") else "inf",
                "note": "positions require implausible speed between reports",
            })

    # Attribute contradictions: entity_type + selected attribute keys.
    def _values(key):
        vals = {}
        for o in obs:
            v = o.entity_type if key == "entity_type" else o.attributes.get(key)
            if v not in (None, ""):
                vals.setdefault(str(v).lower(), []).append(o.id)
        return vals

    for key in _MUTEX_KEYS:
        vals = _values(key)
        if len(vals) > 1:
            out.append({
                "kind": "attribute-conflict",
                "entity_id": entity.id,
                "attribute": key,
                "values": {k: sorted(v) for k, v in vals.items()},
                "note": f"conflicting {key} values across reporting",
            })
    return out


def assess(resolved: list, observations) -> dict:
    """Full corroboration + contradiction pass over resolved entities."""
    obs_by_id = {o.id: o for o in observations}
    scores = [corroboration_score(e, obs_by_id) for e in resolved]
    contradictions = []
    for e in resolved:
        contradictions.extend(detect_contradictions(e, obs_by_id))
    scores.sort(key=lambda s: (-s["score"], s["canonical"]))
    return {
        "corroboration": scores,
        "contradictions": contradictions,
        "summary": {
            "entities": len(resolved),
            "strongly_corroborated": sum(1 for s in scores if s["band"] == "strong"),
            "single_source": sum(1 for s in scores if s["band"] == "single-source"),
            "contradiction_count": len(contradictions),
        },
    }
