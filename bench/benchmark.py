"""Performance benchmarks: throughput of ingest→extract→resolve→graph→index and
query latency at increasing report volumes."""

from __future__ import annotations

import json
import time

from obsidia import extract as extractmod
from obsidia import graph as graphmod
from obsidia.index import TfidfIndex
from obsidia.resolve import resolve

GAZ = {"vessel": {"MV Nightjar": ["Nightjar"]}}


def _synth(n):
    reps = []
    for i in range(n):
        reps.append({
            "id": f"S{i}", "timestamp": "2026-01-01T00:00:00Z", "source": "OSINT",
            "text": (f"Actor node {i} moved funds via wallet addr-{i} from server "
                     f"10.0.{i % 255}.{(i * 7) % 255}. Contact user{i}@ex.example "
                     f"referenced MV Nightjar near 9.{100 + i % 800},-79.{100 + i % 800}."),
        })
    return reps


def benchmark(sizes=(500, 2000, 8000)) -> list:
    rows = []
    for n in sizes:
        reps = _synth(n)
        t0 = time.perf_counter()
        mentions = extractmod.extract(reps, GAZ)
        t_extract = time.perf_counter() - t0

        t0 = time.perf_counter()
        resolve(mentions)
        t_resolve = time.perf_counter() - t0

        t0 = time.perf_counter()
        graphmod.build_graph(reps, GAZ)
        t_graph = time.perf_counter() - t0

        t0 = time.perf_counter()
        idx = TfidfIndex(reps)
        t_index = time.perf_counter() - t0

        t0 = time.perf_counter()
        idx.search("wallet addr-42 server infrastructure", k=5)
        t_query = time.perf_counter() - t0

        total = t_extract + t_resolve + t_graph + t_index
        rows.append({
            "reports": n,
            "mentions": len(mentions),
            "extract_s": round(t_extract, 4),
            "resolve_s": round(t_resolve, 4),
            "graph_s": round(t_graph, 4),
            "index_s": round(t_index, 4),
            "query_ms": round(t_query * 1000, 3),
            "reports_per_s": int(n / total) if total > 0 else None,
        })
    return rows


def main():
    print(json.dumps(benchmark(), indent=2))


if __name__ == "__main__":
    main()
