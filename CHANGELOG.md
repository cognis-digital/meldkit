# Changelog

Adheres to [Semantic Versioning](https://semver.org/).

## [0.3.0] — 2026-07-02

### Added
- **Captured-media (photo/video) exploitation** (`vision.py`) with a pluggable
  backend: a deterministic offline provider that runs CA-CFAR small-target
  detection (finds a swimmer / small craft / person as a 1–2 pixel target) and
  returns a source-faithful description, plus an optional local Ollama multimodal
  provider (llava). `analyze_media` turns a frame into a graph-ready report;
  CLI `analyze-image`.
- `smalltarget.py` CA-CFAR detector (shared design with Vigil/Lookout).

## [0.2.0] — 2026-07-01

### Added
- **Live feed integration** (`cognis_vanguard.sources`): 14 keyless OSINT /
  situational-awareness / threat feeds (GDELT, ReliefWeb, USGS, GDACS, CISA
  advisories, defense news RSS, DVIDS, abuse.ch IOC feeds) materialized into
  Vanguard reports that flow into extraction, the knowledge graph, and retrieval.
- Adapters: GDELT, ReliefWeb, USGS GeoJSON, generic RSS/Atom, IOC-lines
  (pattern-based IP/URL extraction). HTTP client with offline/air-gap cache.
- CLI: `sources-list`, `sources-stats`, `sources-ingest`, `demo-live`
  (ingest live feeds and answer a query end-to-end).
- Feed coverage added to `bench/run_all.py` / `RESULTS.md`;
  `tests/test_sources.py` gates catalog, adapters, ingest, and graph integration.
- Live-verified: real USGS events and abuse.ch indicators ingested as reports.

## [0.1.0] — 2026-07-01

Initial public release.

### Added
- Entity extraction (regex indicators + gazetteer named entities) — `extract`.
- Entity resolution / alias merging with provenance — `resolve`.
- TF-IDF retrieval over reports (stdlib) — `index`.
- Provenance-tracked knowledge graph + correlation — `graph`, `model`.
- Deterministic multi-agent orchestrator (retrieve→extract→correlate→summarize)
  with an auditable execution trace — `agents`.
- Pluggable reasoning backend: deterministic offline provider (default) and
  optional local Ollama provider (self-hosted open-weight models) — `llm`.
- STIX 2.1 export with deterministic IDs and source references — `stix`.
- CLI (`cognis-vanguard`) with `demo`, `query`, `extract`, `correlate`, `graph`.
- Zero-dependency, offline / air-gap capable.
- Verification harness (`bench/`): ground-truth extraction/resolution/retrieval
  metrics + performance benchmarks; results in `RESULTS.md`.
- 20 tests + 4 verification gates; GitHub Actions CI across Python 3.9–3.13.
