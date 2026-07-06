"""DEMO: interoperability exports (JSON / CSV / STIX 2.1-like / symbol-agnostic).

Fuses the bundled scenario and emits every export format, verifying the
symbol-agnostic entity schema carries NO military-symbology identification
codes by design (this tool describes entities; it does not paint a targeting
overlay).

Run:  python examples/interop_export_demo.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from confluex.fusion import interop, scenario  # noqa: E402

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def main():
    res = scenario.run_scenario(scenario.load_scenario(os.path.join(D, "scenario_maritime.json")))
    obs, ents = res["observations"], res["entities"]

    full = json.loads(interop.to_json(obs, ents, res["assessment"]))
    print(f"JSON export: {len(full['observations'])} observations, "
          f"{len(full['entities'])} entities, assessment included={'assessment' in full}")

    csv_text = interop.observations_to_csv(obs)
    print(f"CSV export: {csv_text.count(chr(10))} lines (incl. header)")

    stix = interop.to_stix(obs, ents)
    kinds = {}
    for o in stix["objects"]:
        kinds[o["type"]] = kinds.get(o["type"], 0) + 1
    print(f"STIX 2.1-like bundle: {len(stix['objects'])} objects {kinds}")
    assert interop.to_stix_json(obs, ents) == interop.to_stix_json(obs, ents), "STIX must be deterministic"

    sym = interop.to_symbol_agnostic(ents)
    blob = json.dumps(sym).lower()
    for banned in ("2525", "app-6", "app6", "sidc"):
        assert banned not in blob, f"symbol-agnostic export must not contain {banned}"
    print(f"Symbol-agnostic schema: {len(sym['entities'])} entities, "
          f"affiliations={sorted({e['affiliation'] for e in sym['entities']})}, "
          f"symbol codes present=False")

    print("\n[+] All four interop formats emitted; symbol-agnostic export verified clean.")


if __name__ == "__main__":
    main()
