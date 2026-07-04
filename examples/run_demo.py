"""End-to-end example. Run from repo root:  python examples/run_demo.py"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from obsidia import extract, report, stix  # noqa: E402
from obsidia.agents import Orchestrator  # noqa: E402

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

reports = extract.load_reports(os.path.join(D, "sample_reports.json"))
gaz = extract.load_gazetteer(os.path.join(D, "gazetteer.json"))

orch = Orchestrator(reports, gaz)
result = orch.answer("who controls wallet addr-B1 and what infrastructure", k=3)
print(report.render_text(result))

bundle = stix.bundle_from_graph(orch.graph)
print(f"\nGraph: {len(orch.graph.entities)} entities, {len(orch.graph.edges)} edges | "
      f"STIX objects: {len(bundle['objects'])}")
