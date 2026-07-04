"""DEMO: change detection between two observation snapshots.

Compares a "yesterday" and "today" picture and reports which entities newly
appeared, which disappeared, and which changed the INT disciplines observing
them — a situational-awareness delta for the analyst.

Run:  python examples/change_detection_demo.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cognis_vanguard.fusion import adapters_int, tracks  # noqa: E402


def main():
    prev = adapters_int.geoint([
        {"source": "sat", "timestamp": "2026-06-01T00:00:00Z", "entity": "Alpha",
         "entity_type": "vessel", "lat": 9.0, "lon": -79.0},
        {"source": "sat", "timestamp": "2026-06-01T01:00:00Z", "entity": "Bravo",
         "entity_type": "vessel", "lat": 9.1, "lon": -79.1},
    ])
    curr = adapters_int.geoint([
        {"source": "sat", "timestamp": "2026-06-02T00:00:00Z", "entity": "Bravo",
         "entity_type": "vessel", "lat": 9.1, "lon": -79.1},
    ]) + adapters_int.osint([
        {"source": "news", "timestamp": "2026-06-02T02:00:00Z", "title": "Charlie arrives",
         "entity": "Charlie", "entity_type": "vessel"},
        {"source": "news", "timestamp": "2026-06-02T03:00:00Z", "title": "Bravo also seen ashore",
         "entity": "Bravo", "entity_type": "vessel"},
    ])

    change = tracks.detect_change(prev, curr)
    print("Change detection (yesterday -> today):")
    print(f"  appeared    : {change['appeared']}")
    print(f"  disappeared : {change['disappeared']}")
    print(f"  int changed : {change['discipline_changed']}")
    print(f"  summary     : {change['summary']}")

    assert "charlie" in change["appeared"]
    assert "alpha" in change["disappeared"]
    assert "bravo" in change["discipline_changed"]
    print("\n[+] Appearances, disappearances, and INT-coverage changes detected.")


if __name__ == "__main__":
    main()
