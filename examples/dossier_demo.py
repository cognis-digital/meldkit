"""DEMO: entity dossier generation.

Fuses the bundled scenario and prints a full dossier for the best-corroborated
entity: identity + provenance, corroboration, contradictions, track summary,
pattern-of-life, and any force-protection zone hits. Every element traces to
cited observations.

Run:  python examples/dossier_demo.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cognis_vanguard.fusion import cop, scenario  # noqa: E402

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def main():
    res = scenario.run_scenario(scenario.load_scenario(os.path.join(D, "scenario_maritime.json")))
    top = res["entities"][0]
    d = cop.dossier(res, top.id)
    e = d["entity"]

    print("=" * 64)
    print(f"  ENTITY DOSSIER — {e['canonical']}  ({e['entity_type']})")
    print("=" * 64)
    print(f"Aliases      : {e['aliases']}")
    print(f"Identifiers  : {e['identifiers']}")
    print(f"Disciplines  : {d['provenance']['disciplines']}")
    print(f"Sources      : {d['provenance']['sources']}")
    c = d["corroboration"]
    print(f"Corroboration: {c['band']} (score {c['score']:.2f}, "
          f"{c['discipline_count']} INT / {c['source_count']} sources)")
    print(f"Contradictions: {len(d['contradictions'])}")
    track = d["track"]
    if track:
        print(f"Track        : {track['point_count']} points, "
              f"{track['total_distance_km']} km")
    pol = d["pattern_of_life"]
    print(f"Active hours : {pol['active_hours_utc']} UTC")
    print(f"Zone alerts  : {len(d['zone_alerts'])}")
    print(f"Observations : {len(d['observations'])} (all cited)")
    print("\n[+] Dossier assembled from cited multi-INT observations only.")

    assert d["observations"], "dossier must cite its source observations"


if __name__ == "__main__":
    main()
