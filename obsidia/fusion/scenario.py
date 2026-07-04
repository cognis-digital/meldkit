"""Load a multi-INT scenario and run the full fusion pipeline.

A scenario file is a JSON object:
  {
    "name": "...",
    "sources": {
        "osint":  [ {..synthetic osint record..}, ... ],
        "sigint": [ ... ],   # metadata only
        "geoint": [ ... ],
        "humint": [ ... ],
        "masint": [ ... ],
        "structured": [ ... ]
    },
    "zones": [ {name, lat, lon, radius_km, kind, ...}, ... ]   # optional
  }

Everything is synthetic. run_scenario() returns a single fused result object
(observations, resolved entities, corroboration/contradiction assessment,
tracks, patterns-of-life, anomalies, geofence alerts) — the raw material the
COP renderer turns into a picture. Deterministic and offline.
"""

from __future__ import annotations

import json

from . import adapters_int, corroborate, entities, geofence, tracks
from .schema import Observation, validate


def load_scenario(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def observations_from_scenario(scenario: dict) -> list:
    obs = []
    for discipline, records in (scenario.get("sources") or {}).items():
        obs.extend(adapters_int.normalize(discipline, records))
    # Stable order: by timestamp then id.
    obs.sort(key=lambda o: (o.timestamp, o.id))
    return obs


def run_scenario(scenario: dict) -> dict:
    observations = observations_from_scenario(scenario)
    problems = {o.id: validate(o) for o in observations if validate(o)}

    resolved = entities.resolve_entities(observations)
    conflicts = entities.deconflict(resolved)
    assessment = corroborate.assess(resolved, observations)

    obs_by_id = {o.id: o for o in observations}
    track_list = [tracks.associate_track(e, obs_by_id) for e in resolved]
    track_list = [t for t in track_list if t["point_count"] >= 2]
    pols = [tracks.pattern_of_life(e, obs_by_id) for e in resolved]
    anomalies = []
    for e in resolved:
        anomalies.extend(tracks.detect_anomalies(e, obs_by_id))

    zones = geofence.load_zones(scenario.get("zones", []))
    zone_alerts = geofence.evaluate(observations, zones) if zones else []
    dwell = geofence.dwell_alerts(observations, zones) if zones else []

    return {
        "name": scenario.get("name", "unnamed scenario"),
        "observations": observations,
        "validation_problems": problems,
        "entities": resolved,
        "deconfliction": conflicts,
        "assessment": assessment,
        "tracks": track_list,
        "patterns_of_life": pols,
        "anomalies": anomalies,
        "zones": [z.to_dict() for z in zones],
        "zone_alerts": zone_alerts,
        "dwell_alerts": dwell,
        "counts": {
            "observations": len(observations),
            "entities": len(resolved),
            "disciplines": len({o.discipline for o in observations}),
            "sources": len({o.source for o in observations}),
            "tracks": len(track_list),
            "anomalies": len(anomalies),
            "zone_alerts": len(zone_alerts),
            "contradictions": len(assessment["contradictions"]),
            "deconfliction_flags": len(conflicts),
        },
    }


def observations_to_list(result: dict) -> list:
    """Serializable observations list from a run_scenario result."""
    return [o.to_dict() for o in result["observations"]]


def to_serializable(result: dict) -> dict:
    """A fully JSON-serializable view of a run_scenario result."""
    out = dict(result)
    out["observations"] = [o.to_dict() for o in result["observations"]]
    out["entities"] = [e.to_dict() for e in result["entities"]]
    return out
