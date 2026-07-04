"""Human-readable and JSON products for Vanguard answers and graphs."""

from __future__ import annotations

import json


def render_json(result) -> str:
    return json.dumps(result, indent=2)


def render_text(result) -> str:
    L = []
    L.append("=" * 72)
    L.append("  COGNIS VANGUARD  |  Multi-INT Fusion Answer")
    L.append("  Cognis Digital LLC - source-cited, offline, provenance-tracked")
    L.append("=" * 72)
    L.append(f"Query : {result['query']}")
    L.append(f"Answer: {result['answer'] or '(no relevant reporting found)'}")
    L.append(f"Cited : {', '.join(result['citations']) or 'n/a'}")
    if result.get("pivot_entity"):
        p = result["pivot_entity"]
        L.append(f"Pivot : {p['type']} = {p['value']}")
    if result.get("correlated"):
        L.append("Correlated entities:")
        for c in result["correlated"][:10]:
            L.append(f"   - {c['type']}: {c['value']}  (weight={c['weight']}, "
                     f"reports={', '.join(c['shared_reports'])})")
    L.append("")
    L.append("Execution trace:")
    for step in result["trace"]:
        L.append(f"   [{step['tool']}] {step['note']}")
    L.append("")
    L.append("NOTE: Every output is traceable to cited reports. Analyst corroboration required.")
    return "\n".join(L)
