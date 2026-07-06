"""Run accuracy + performance and write bench/results.json and RESULTS.md."""

from __future__ import annotations

import json
import os
import platform
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bench import benchmark, evaluate, fusion_evaluate  # noqa: E402
from confluex.sources import ingest as vfeeds  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def build_results():
    return {
        "accuracy": evaluate.evaluate(),
        "performance": benchmark.benchmark(),
        "fusion_accuracy": fusion_evaluate.evaluate(),
        "fusion_performance": fusion_evaluate.benchmark(),
        "feeds": vfeeds.stats(),
        "environment": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "system": platform.system(),
            "machine": platform.machine(),
        },
    }


def render_md(res) -> str:
    a = res["accuracy"]
    e = a["extraction"]
    r = a["retrieval"]
    env = res["environment"]
    L = []
    L.append("# Confluex — Verification Results\n")
    L.append("Reproduce with: `python bench/run_all.py` (regenerates this file).\n")
    L.append(f"Environment: {env['implementation']} {env['python']} on "
             f"{env['system']}/{env['machine']}. Deterministic inputs and default offline provider.\n")
    L.append("## Accuracy vs. ground-truth goldset\n")
    L.append("| Task | Metric |")
    L.append("|---|---|")
    L.append(f"| Entity extraction | P={e['precision']:.3f} / R={e['recall']:.3f} / F1={e['f1']:.3f} "
             f"(tp={e['tp']}, fp={e['fp']}, fn={e['fn']}) |")
    L.append(f"| Entity resolution accuracy | {a['resolution_accuracy']:.3f} |")
    L.append(f"| Retrieval precision@1 | {r['precision_at_1']:.3f} |")
    L.append(f"| Retrieval recall@3 | {r['recall_at_3']:.3f} |")
    L.append(f"| Retrieval MRR | {r['mrr']:.3f} |")
    L.append(f"| STIX determinism (2 runs identical) | {a['determinism']} |")
    L.append("")
    L.append("## Performance (single-thread, stdlib only)\n")
    L.append("| Reports | Mentions | Extract (s) | Resolve (s) | Graph (s) | Index (s) | Query (ms) | Reports/s |")
    L.append("|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in res["performance"]:
        L.append(f"| {row['reports']:,} | {row['mentions']:,} | {row['extract_s']} | {row['resolve_s']} | "
                 f"{row['graph_s']} | {row['index_s']} | {row['query_ms']} | {row['reports_per_s']:,} |")
    L.append("")
    fa = res.get("fusion_accuracy")
    if fa:
        L.append("## Multi-INT fusion accuracy (bundled synthetic scenario)\n")
        L.append(f"Fused {fa['dataset']['observations']} observations across "
                 f"{fa['dataset']['disciplines']} INT disciplines into "
                 f"{fa['dataset']['entities']} resolved entities.\n")
        L.append("| Fusion task | Metric |")
        L.append("|---|---|")
        L.append(f"| Cross-source entity resolution accuracy | {fa['entity_resolution_accuracy']:.3f} |")
        L.append(f"| Corroboration band accuracy | {fa['corroboration_band_accuracy']:.3f} |")
        L.append(f"| Cross-INT fusion correct (IMO-linked vessel) | {fa['cross_source_fusion_correct']} |")
        L.append(f"| Force-protection keep-out recall | {fa['force_protection_recall']:.3f} |")
        L.append(f"| Contradiction precision (clean scenario) | {fa['contradiction_precision_ok']} |")
        L.append("")
        fp = res.get("fusion_performance")
        if fp:
            L.append("### Fusion performance (single-thread, stdlib only)\n")
            L.append("| Observations | Entities | Resolve (s) | Assess (s) | Geofence (s) | Obs/s |")
            L.append("|---:|---:|---:|---:|---:|---:|")
            for row in fp:
                L.append(f"| {row['observations']:,} | {row['entities']:,} | "
                         f"{row['resolve_s']} | {row['assess_s']} | {row['geofence_s']} | "
                         f"{row['observations_per_s']:,} |")
            L.append("")

    f = res.get("feeds")
    if f:
        L.append("## Live feed coverage\n")
        L.append(f"- **{f['total']} keyless live feeds** across: "
                 + ", ".join(f"{k}={v}" for k, v in f["by_category"].items()))
        L.append(f"- Adapters: {', '.join(f['adapters'])}")
        L.append("")
    L.append("All numbers are produced by `bench/run_all.py` and gated in CI by "
             "`tests/test_bench.py` / `tests/test_sources.py`. See `docs/LIMITATIONS.md`.\n")
    return "\n".join(L)


def main():
    res = build_results()
    with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    with open(os.path.join(ROOT, "RESULTS.md"), "w", encoding="utf-8") as f:
        f.write(render_md(res))
    print("[+] wrote bench/results.json and RESULTS.md")
    print(render_md(res))


if __name__ == "__main__":
    main()
