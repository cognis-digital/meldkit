"""DEMO: corroboration scoring + contradiction detection.

Uses the synthetic overland border scenario, which contains a deliberate
spatial contradiction (an entity reported in two far-apart places nearly
simultaneously). Shows the corroboration bands and the flagged contradiction —
surfaced for analyst review, never auto-adjudicated.

Run:  python examples/corroboration_demo.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cognis_vanguard.fusion import scenario  # noqa: E402

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def main():
    res = scenario.run_scenario(scenario.load_scenario(
        os.path.join(D, "scenario_border_awareness.json")))
    print(f"Scenario: {res['name']}\n")

    print("Corroboration (breadth of independent support):")
    for s in res["assessment"]["corroboration"]:
        print(f"  [{s['band']:>13}] {s['canonical']:<12} score={s['score']:.2f} "
              f"int={','.join(s['disciplines'])} avg_conf={s['avg_confidence']:.2f}")

    contradictions = res["assessment"]["contradictions"]
    print(f"\nContradictions flagged: {len(contradictions)}")
    for c in contradictions:
        print(f"  - {c['kind']} on {c.get('entity_id', '')}: {c.get('note', '')}"
              + (f"  (~{c['implied_kmh']} km/h)" if "implied_kmh" in c else ""))

    assert any(c["kind"] == "spatial-implausible-move" for c in contradictions), \
        "expected a spatial contradiction in this scenario"
    print("\n[+] Spatial contradiction correctly surfaced for analyst review.")


if __name__ == "__main__":
    main()
