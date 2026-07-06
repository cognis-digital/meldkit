# Confluex — Verification Results

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
| 500 | 3,000 | 0.0174 | 0.005 | 0.0314 | 0.0078 | 2.049 | 8,120 |
| 2,000 | 12,000 | 0.0674 | 0.0182 | 0.1304 | 0.0454 | 24.418 | 7,650 |
| 8,000 | 48,000 | 0.282 | 0.0952 | 0.5593 | 0.1391 | 32.188 | 7,437 |

## Multi-INT fusion accuracy (bundled synthetic scenario)

Fused 13 observations across 6 INT disciplines into 5 resolved entities.

| Fusion task | Metric |
|---|---|
| Cross-source entity resolution accuracy | 1.000 |
| Corroboration band accuracy | 1.000 |
| Cross-INT fusion correct (IMO-linked vessel) | True |
| Force-protection keep-out recall | 1.000 |
| Contradiction precision (clean scenario) | True |

### Fusion performance (single-thread, stdlib only)

| Observations | Entities | Resolve (s) | Assess (s) | Geofence (s) | Obs/s |
|---:|---:|---:|---:|---:|---:|
| 500 | 10 | 0.0052 | 0.0079 | 0.0007 | 36,342 |
| 2,000 | 10 | 0.0182 | 0.0227 | 0.0048 | 43,709 |
| 8,000 | 10 | 0.1744 | 0.044 | 0.0137 | 34,484 |

## Live feed coverage

- **14 keyless live feeds** across: advisories=2, osint-news=5, situational=4, threat-intel=3
- Adapters: gdelt, ioc_lines, reliefweb, rss, usgs

All numbers are produced by `bench/run_all.py` and gated in CI by `tests/test_bench.py` / `tests/test_sources.py`. See `docs/LIMITATIONS.md`.
