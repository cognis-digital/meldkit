"""DEMO: cross-source entity resolution & de-confliction.

Shows how the same vessel, reported under different labels ("MV Nightjar",
"Nightjar") and linked by a shared IMO across GEOINT / OSINT / STRUCTURED /
HUMINT, collapses to a single resolved entity — while genuinely distinct
entities stay separate. Also surfaces a de-confliction flag for an ambiguous
name reused across entity types.

Run:  python examples/entity_resolution_demo.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from obsidia.fusion import adapters_int, entities  # noqa: E402


def main():
    obs = []
    obs += adapters_int.geoint([
        {"source": "sat", "timestamp": "2026-01-01T00:00:00Z", "entity": "MV Nightjar",
         "entity_type": "vessel", "lat": 9.0, "lon": -79.0, "imo": "9111111"},
        {"source": "sat", "timestamp": "2026-01-01T06:00:00Z", "entity": "Nightjar",
         "entity_type": "vessel", "lat": 9.1, "lon": -79.1, "imo": "9111111"},
    ])
    obs += adapters_int.osint([
        {"source": "news", "timestamp": "2026-01-02T00:00:00Z",
         "title": "MV Nightjar chartered for coastal transit", "entity": "MV Nightjar",
         "entity_type": "vessel"},
        {"source": "news", "timestamp": "2026-01-02T00:00:00Z",
         "title": "Separate vessel MV Petrel reported engine trouble", "entity": "MV Petrel",
         "entity_type": "vessel"},
    ])
    # An ambiguous name reused across types (to trigger de-confliction).
    obs += adapters_int.osint([
        {"source": "news", "timestamp": "2026-01-03T00:00:00Z", "title": "Falcon spotted",
         "entity": "Falcon", "entity_type": "vessel"},
        {"source": "news", "timestamp": "2026-01-03T00:00:00Z", "title": "Falcon overhead",
         "entity": "Falcon", "entity_type": "aircraft"},
    ])

    resolved = entities.resolve_entities(obs)
    print(f"{len(obs)} observations -> {len(resolved)} resolved entities\n")
    for e in resolved:
        d = e.to_dict()
        print(f"  {d['canonical']:<14} type={d['entity_type']:<9} "
              f"obs={d['observation_count']} int={','.join(d['disciplines'])} "
              f"aliases={d['aliases']} ids={d['identifiers']}")

    conflicts = entities.deconflict(resolved)
    print(f"\nDe-confliction flags: {len(conflicts)}")
    for c in conflicts:
        print(f"  - {c['kind']}: {c.get('note', '')}")

    nightjar = [e for e in resolved if "Nightjar" in e.canonical]
    assert nightjar and len(nightjar) == 1, "Nightjar aliases should fuse to one entity"
    assert any(c["kind"] == "name-type-ambiguity" for c in conflicts), "expected Falcon flag"
    print("\n[+] Nightjar aliases fused to a single entity; Falcon ambiguity flagged.")


if __name__ == "__main__":
    main()
