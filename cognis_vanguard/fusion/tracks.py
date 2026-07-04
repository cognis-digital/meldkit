"""Track & pattern analytics for SITUATIONAL AWARENESS and FORCE PROTECTION.

  * track association  : link geolocated sightings of the same entity into an
    ordered track (by time), computing leg distances/speeds.
  * pattern-of-life    : summarize an entity's routine — active hours, typical
    locations (spatial clusters), and recurring dwell areas.
  * anomaly / change   : flag legs that deviate from the entity's own norm
    (speed spike, off-pattern hour, appearance far from usual area).

FRAMING: this describes *what is happening and what is unusual* so a protected
force can understand its environment. It performs NO targeting, prediction of
where to strike, or engagement recommendation. Anomalies are informational
flags for an analyst, not cues to action.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone

from .schema import haversine_km


def _parse_ts(ts: str):
    if not ts:
        return None
    s = ts.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        try:
            dt = datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def associate_track(entity, obs_by_id: dict) -> dict:
    """Build a time-ordered track from an entity's geolocated observations."""
    pts = []
    for oid in entity.observation_ids:
        o = obs_by_id.get(oid)
        if o is not None and o.has_geo:
            dt = _parse_ts(o.timestamp)
            pts.append((dt, o))
    pts = [p for p in pts if p[0] is not None]
    pts.sort(key=lambda p: (p[0], p[1].id))

    legs = []
    total_km = 0.0
    for i in range(1, len(pts)):
        (t0, a), (t1, b) = pts[i - 1], pts[i]
        dist = haversine_km(a.lat, a.lon, b.lat, b.lon)
        hours = max((t1 - t0).total_seconds() / 3600.0, 0.0)
        speed = (dist / hours) if hours > 1e-6 else None
        total_km += dist
        legs.append({
            "from_obs": a.id, "to_obs": b.id,
            "from_ts": a.timestamp, "to_ts": b.timestamp,
            "distance_km": round(dist, 3),
            "elapsed_h": round(hours, 4),
            "speed_kmh": round(speed, 2) if speed is not None else None,
        })
    return {
        "entity_id": entity.id,
        "canonical": entity.canonical,
        "points": [{"ts": o.timestamp, "lat": o.lat, "lon": o.lon, "obs": o.id}
                   for _dt, o in pts],
        "point_count": len(pts),
        "legs": legs,
        "total_distance_km": round(total_km, 3),
    }


def _cluster_locations(points, radius_km: float = 5.0) -> list:
    """Greedy spatial clustering of (lat,lon,...) points into dwell areas."""
    clusters = []
    for p in points:
        placed = False
        for c in clusters:
            if haversine_km(p["lat"], p["lon"], c["lat"], c["lon"]) <= radius_km:
                n = c["count"]
                c["lat"] = (c["lat"] * n + p["lat"]) / (n + 1)
                c["lon"] = (c["lon"] * n + p["lon"]) / (n + 1)
                c["count"] = n + 1
                placed = True
                break
        if not placed:
            clusters.append({"lat": p["lat"], "lon": p["lon"], "count": 1})
    for c in clusters:
        c["lat"] = round(c["lat"], 5)
        c["lon"] = round(c["lon"], 5)
    clusters.sort(key=lambda c: (-c["count"], c["lat"], c["lon"]))
    return clusters


def pattern_of_life(entity, obs_by_id: dict, radius_km: float = 5.0) -> dict:
    """Summarize an entity's routine: active hours, weekday activity, and the
    spatial clusters (dwell areas) it frequents. Descriptive only."""
    obs = [obs_by_id[i] for i in entity.observation_ids if i in obs_by_id]
    hours = Counter()
    weekdays = Counter()
    geo_points = []
    for o in obs:
        dt = _parse_ts(o.timestamp)
        if dt is not None:
            hours[dt.hour] += 1
            weekdays[dt.strftime("%a")] += 1
        if o.has_geo:
            geo_points.append({"lat": o.lat, "lon": o.lon, "obs": o.id})
    clusters = _cluster_locations(geo_points, radius_km)
    active_hours = [h for h, _ in sorted(hours.items(), key=lambda x: (-x[1], x[0]))[:4]]
    return {
        "entity_id": entity.id,
        "canonical": entity.canonical,
        "observation_count": len(obs),
        "active_hours_utc": sorted(active_hours),
        "hour_histogram": dict(sorted(hours.items())),
        "weekday_histogram": dict(weekdays),
        "dwell_areas": clusters,
        "primary_dwell": clusters[0] if clusters else None,
    }


def detect_anomalies(entity, obs_by_id: dict, speed_sigma: float = 2.5,
                     radius_km: float = 5.0) -> list:
    """Flag observations/legs that deviate from the entity's own baseline.

    * speed anomaly : a leg whose speed exceeds mean + speed_sigma*std of legs.
    * off-pattern hour : an observation at an hour the entity is rarely active.
    * off-pattern place : a geo point far from every established dwell area.
    """
    anomalies = []
    track = associate_track(entity, obs_by_id)
    speeds = [leg["speed_kmh"] for leg in track["legs"] if leg["speed_kmh"] is not None]
    if len(speeds) >= 3:
        # Outlier-resistant baseline: median + robust spread (MAD), so a single
        # extreme leg cannot inflate the ceiling and mask itself.
        ordered = sorted(speeds)
        median = ordered[len(ordered) // 2]
        deviations = sorted(abs(s - median) for s in speeds)
        mad = deviations[len(deviations) // 2]
        if mad > 1e-6:
            spread = mad * 1.4826
        else:
            # Degenerate MAD (many identical baseline legs): use a floor tied to
            # the typical speed so a large jump still trips the ceiling.
            spread = max(median * 0.5, 1.0)
        ceiling = median + speed_sigma * spread
        for leg in track["legs"]:
            if leg["speed_kmh"] is not None and leg["speed_kmh"] > ceiling:
                anomalies.append({
                    "kind": "speed-anomaly", "entity_id": entity.id,
                    "leg": [leg["from_obs"], leg["to_obs"]],
                    "speed_kmh": leg["speed_kmh"],
                    "baseline_median_kmh": round(median, 2),
                    "note": "leg speed exceeds entity's own baseline",
                })

    pol = pattern_of_life(entity, obs_by_id, radius_km)
    rare_hours = {h for h, c in pol["hour_histogram"].items()
                  if c == 1 and pol["observation_count"] >= 5}
    for oid in entity.observation_ids:
        o = obs_by_id.get(oid)
        if o is None:
            continue
        dt = _parse_ts(o.timestamp)
        if dt is not None and dt.hour in rare_hours:
            anomalies.append({
                "kind": "off-pattern-hour", "entity_id": entity.id,
                "observation": o.id, "hour_utc": dt.hour,
                "note": "activity at an hour outside the entity's routine",
            })
        # Compare only against ESTABLISHED dwell areas (>=2 points); a lone
        # off-pattern appearance forms a singleton cluster we must not treat as
        # its own baseline.
        established = [c for c in pol["dwell_areas"] if c["count"] >= 2]
        if o.has_geo and established:
            nearest = min(haversine_km(o.lat, o.lon, c["lat"], c["lon"])
                          for c in established)
            if nearest > max(radius_km * 6, 50.0):
                anomalies.append({
                    "kind": "off-pattern-location", "entity_id": entity.id,
                    "observation": o.id,
                    "distance_from_dwell_km": round(nearest, 1),
                    "note": "appearance far from established dwell areas",
                })
    return anomalies


def detect_change(prev_obs: list, curr_obs: list) -> dict:
    """Change detection between two observation snapshots: which entities are
    newly appearing, which disappeared, and which changed disciplines."""
    def _by_ent(obs):
        m = defaultdict(set)
        for o in obs:
            if o.entity:
                m[o.entity.lower()].add(o.discipline)
        return m
    a, b = _by_ent(prev_obs), _by_ent(curr_obs)
    appeared = sorted(set(b) - set(a))
    disappeared = sorted(set(a) - set(b))
    changed = sorted(e for e in (set(a) & set(b)) if a[e] != b[e])
    return {
        "appeared": appeared,
        "disappeared": disappeared,
        "discipline_changed": changed,
        "summary": {"appeared": len(appeared), "disappeared": len(disappeared),
                    "changed": len(changed)},
    }
