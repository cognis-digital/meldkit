# Cognis Vanguard — Verification Results

Reproduce with: `python bench/run_all.py` (regenerates this file).

Environment: CPython 3.14.0 on Windows/AMD64. Deterministic inputs and default offline provider.

## Accuracy vs. ground-truth goldset

| Task | Metric |
|---|---|
| Entity extraction | P=1.000 / R=1.000 / F1=1.000 (tp=14, fp=0, fn=0) |
| Entity resolution accuracy | 1.000 |
| Retrieval precision@1 | 1.000 |
| Retrieval recall@3 | 1.000 |
| Retrieval MRR | 1.000 |
| STIX determinism (2 runs identical) | True |

## Performance (single-thread, stdlib only)

| Reports | Mentions | Extract (s) | Resolve (s) | Graph (s) | Index (s) | Query (ms) | Reports/s |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 500 | 3,000 | 0.0176 | 0.0072 | 0.0444 | 0.0112 | 3.13 | 6,225 |
| 2,000 | 12,000 | 0.0922 | 0.0515 | 0.2457 | 0.0454 | 15.576 | 4,600 |
| 8,000 | 48,000 | 0.3212 | 0.2287 | 1.0462 | 0.3005 | 64.949 | 4,218 |

## Live feed coverage

- **14 keyless live feeds** across: advisories=2, osint-news=5, situational=4, threat-intel=3
- Adapters: gdelt, ioc_lines, reliefweb, rss, usgs

All numbers are produced by `bench/run_all.py` and gated in CI by `tests/test_bench.py` / `tests/test_sources.py`. See `docs/LIMITATIONS.md`.
