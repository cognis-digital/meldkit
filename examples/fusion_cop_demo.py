"""DEMO: end-to-end multi-INT fusion -> Common Operating Picture.

Ingests the bundled synthetic maritime scenario across six INT disciplines,
fuses it, and prints the COP summary. Also writes a self-contained HTML COP
dashboard next to this file. Defensive situational awareness only.

Run:  python examples/fusion_cop_demo.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cognis_vanguard.fusion import cop, scenario  # noqa: E402

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def main():
    res = scenario.run_scenario(scenario.load_scenario(os.path.join(D, "scenario_maritime.json")))
    print(cop.render_text(res))

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cop_maritime.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(cop.render_html(res))
    print(f"\n[+] Self-contained COP dashboard written to {out}")
    print(f"[+] {res['counts']['disciplines']} INT disciplines fused into "
          f"{res['counts']['entities']} entities from {res['counts']['sources']} sources")


if __name__ == "__main__":
    main()
