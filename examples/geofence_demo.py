"""DEMO: geofence / zone alerting for FORCE PROTECTION.

Defines a keep-out radius around a friendly location and an area-of-interest,
then evaluates synthetic tracks against them. Emits proximity/inside alerts and
a dwell (loiter) indication. These are warnings for understanding and force
protection — the tool nominates, prioritizes, and engages nothing.

Run:  python examples/geofence_demo.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cognis_vanguard.fusion import adapters_int, geofence  # noqa: E402


def main():
    zones = geofence.load_zones([
        {"name": "Forward Base (keep-out 3km)", "lat": 9.35, "lon": -80.05,
         "radius_km": 3.0, "kind": "keep-out", "note": "friendly-force protection"},
        {"name": "Coastal AOI", "lat": 9.30, "lon": -79.98, "radius_km": 12.0,
         "kind": "area-of-interest"},
    ])

    obs = adapters_int.geoint([
        {"source": "radar", "timestamp": "2026-05-01T21:30:00Z", "entity": "Craft-A",
         "entity_type": "vessel", "lat": 9.351, "lon": -80.052},
        {"source": "radar", "timestamp": "2026-05-01T22:00:00Z", "entity": "Craft-A",
         "entity_type": "vessel", "lat": 9.349, "lon": -80.049},
        {"source": "radar", "timestamp": "2026-05-01T22:30:00Z", "entity": "Craft-A",
         "entity_type": "vessel", "lat": 9.352, "lon": -80.051},
        {"source": "sat", "timestamp": "2026-05-01T20:00:00Z", "entity": "MV Transit",
         "entity_type": "vessel", "lat": 9.31, "lon": -79.99},
    ])

    alerts = geofence.evaluate(obs, zones)
    print(f"Zone alerts: {len(alerts)}")
    for a in alerts:
        print(f"  [{a['status']:>9}] {a['entity']:<10} vs {a['zone']:<28} "
              f"({a['zone_kind']}) {a['distance_km']} km  sev={a['severity']}")

    dwell = geofence.dwell_alerts(obs, zones)
    print(f"\nDwell/loiter indications: {len(dwell)}")
    for d in dwell:
        print(f"  - {d['entity']} loitered in {d['zone']} ({d['count']} sightings, "
              f"{d['first_seen']} .. {d['last_seen']})")

    assert alerts, "expected zone alerts"
    assert dwell, "expected a dwell indication for the loitering craft"
    print("\n[+] Keep-out intrusion and loiter surfaced for force-protection awareness.")


if __name__ == "__main__":
    main()
