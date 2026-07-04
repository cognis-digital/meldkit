"""Accuracy + performance evaluation for the multi-INT FUSION layer.

Measures the fusion pipeline against a ground-truth goldset for the bundled
synthetic scenario, and benchmarks fusion throughput on synthetic observations.
Kept honest and CI-gated by tests/test_fusion_bench.py.
"""

from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from obsidia.fusion import (  # noqa: E402
    adapters_int, corroborate, entities, geofence, scenario,
)

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA = os.path.normpath(os.path.join(_HERE, "..", "data"))
_SCENARIO = os.path.join(_DATA, "scenario_maritime.json")
_GOLD = os.path.join(_HERE, "fusion_goldset.json")


def _load(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate() -> dict:
    gold = _load(_GOLD)
    res = scenario.run_scenario(scenario.load_scenario(_SCENARIO))
    ents = res["entities"]
    corr = {c["entity_id"]: c for c in res["assessment"]["corroboration"]}

    # --- Entity resolution: each expected entity resolves to exactly one node
    #     covering at least the expected number of INT disciplines. ---
    ent_hits = 0
    band_hits = 0
    band_total = 0
    for exp in gold["expected_entities"]:
        matches = [e for e in ents if exp["canonical_contains"].lower()
                   in e.canonical.lower()]
        ok = len(matches) == 1 and len(matches[0].disciplines) >= exp["min_disciplines"]
        ent_hits += 1 if ok else 0
        if "expected_band" in exp and matches:
            band_total += 1
            band_hits += 1 if corr.get(matches[0].id, {}).get("band") == exp["expected_band"] else 0
    entity_resolution_accuracy = round(ent_hits / len(gold["expected_entities"]), 4)

    # --- Resolution correctness: the IMO-linked sightings fuse to one vessel. ---
    imo_ent = [e for e in ents if e.identifiers.get("imo") == "9111111"]
    imo_ok = (len(imo_ent) == 1 and
              len(imo_ent[0].observation_ids)
              >= gold["resolution"]["vessel_imo_9111111_observation_count"])

    # --- Force protection: expected entities are flagged inside the keep-out. ---
    inside = {a["entity"] for a in res["zone_alerts"]
              if a["status"] == "inside" and a["zone"] == gold["force_protection"]["keep_out_zone"]}
    fp_expected = set(gold["force_protection"]["expect_inside_entities"])
    fp_recall = round(len(fp_expected & inside) / len(fp_expected), 4)

    # --- Contradictions: none expected in the clean scenario. ---
    contra_ok = len(res["assessment"]["contradictions"]) == gold["contradictions_expected"]

    return {
        "dataset": {"observations": res["counts"]["observations"],
                    "entities": res["counts"]["entities"],
                    "disciplines": res["counts"]["disciplines"]},
        "entity_resolution_accuracy": entity_resolution_accuracy,
        "corroboration_band_accuracy": round(band_hits / band_total, 4) if band_total else 1.0,
        "cross_source_fusion_correct": bool(imo_ok),
        "force_protection_recall": fp_recall,
        "contradiction_precision_ok": bool(contra_ok),
        "disciplines_fused": res["counts"]["disciplines"],
        "min_disciplines_expected": gold["min_disciplines_fused"],
    }


def _synth_observations(n):
    """n synthetic multi-INT observations spread across disciplines/entities."""
    recs_geo = []
    recs_osint = []
    for i in range(n):
        ent = f"Vessel-{i % 50}"
        recs_geo.append({"source": "geo", "timestamp": f"2026-01-01T{i % 24:02d}:00:00Z",
                         "entity": ent, "entity_type": "vessel",
                         "lat": 9.0 + (i % 100) / 100.0, "lon": -79.0 - (i % 100) / 100.0,
                         "speed_kn": 8})
        recs_osint.append({"source": "news", "timestamp": f"2026-01-02T{i % 24:02d}:00:00Z",
                           "title": f"report about {ent} near coast", "entity": ent,
                           "entity_type": "vessel"})
    return adapters_int.geoint(recs_geo) + adapters_int.osint(recs_osint)


def benchmark(sizes=(500, 2000, 8000)) -> list:
    rows = []
    for n in sizes:
        obs = _synth_observations(n // 2)  # produces ~n observations
        t0 = time.perf_counter()
        resolved = entities.resolve_entities(obs)
        t_resolve = time.perf_counter() - t0

        t0 = time.perf_counter()
        corroborate.assess(resolved, obs)
        t_assess = time.perf_counter() - t0

        zones = [geofence.Zone("AOI", 9.5, -79.5, 60.0, kind="area-of-interest")]
        t0 = time.perf_counter()
        geofence.evaluate(obs, zones)
        t_geo = time.perf_counter() - t0

        total = t_resolve + t_assess + t_geo
        rows.append({
            "observations": len(obs),
            "entities": len(resolved),
            "resolve_s": round(t_resolve, 4),
            "assess_s": round(t_assess, 4),
            "geofence_s": round(t_geo, 4),
            "observations_per_s": int(len(obs) / total) if total > 0 else None,
        })
    return rows


def main():
    print(json.dumps({"accuracy": evaluate(), "performance": benchmark()}, indent=2))


if __name__ == "__main__":
    main()
