"""DEMO: track association + pattern-of-life + anomaly detection.

Builds a track for an entity from geolocated sightings, summarizes its routine
(active hours + dwell areas), and flags an off-pattern excursion. This is
descriptive situational awareness for force protection — not prediction of
where to act, and not targeting.

Run:  python examples/tracks_pattern_demo.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cognis_vanguard.fusion import adapters_int, entities, tracks  # noqa: E402


def main():
    # Five days of routine activity at one dwell area, then one off-pattern trip.
    recs = []
    for day in range(1, 6):
        recs.append({"source": "sat", "timestamp": f"2026-04-0{day}T02:00:00Z",
                     "entity": "Skiff-3", "entity_type": "vessel",
                     "lat": 9.000 + day * 0.001, "lon": -79.000, "speed_kn": 5})
        recs.append({"source": "sat", "timestamp": f"2026-04-0{day}T14:00:00Z",
                     "entity": "Skiff-3", "entity_type": "vessel",
                     "lat": 9.002, "lon": -79.001, "speed_kn": 6})
    recs.append({"source": "sat", "timestamp": "2026-04-06T02:00:00Z",
                 "entity": "Skiff-3", "entity_type": "vessel",
                 "lat": 12.0, "lon": -80.5, "speed_kn": 30})

    obs = adapters_int.geoint(recs)
    ent = entities.resolve_entities(obs)[0]
    by_id = {o.id: o for o in obs}

    track = tracks.associate_track(ent, by_id)
    print(f"Track for {track['canonical']}: {track['point_count']} points, "
          f"{track['total_distance_km']} km total across {len(track['legs'])} legs")

    pol = tracks.pattern_of_life(ent, by_id)
    print(f"Pattern-of-life: active hours (UTC) {pol['active_hours_utc']}, "
          f"{len(pol['dwell_areas'])} dwell area(s); primary dwell {pol['primary_dwell']}")

    anomalies = tracks.detect_anomalies(ent, by_id)
    print(f"\nAnomalies flagged: {len(anomalies)}")
    for a in anomalies:
        print(f"  - {a['kind']}: {a.get('note', '')}")

    assert anomalies, "expected at least one off-pattern anomaly"
    print("\n[+] Off-pattern excursion detected against the entity's own baseline.")


if __name__ == "__main__":
    main()
