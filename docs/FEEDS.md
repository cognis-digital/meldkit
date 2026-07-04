# Live Feeds

Obsidia integrates **14 keyless live feeds** that materialize into
reports (`{id, timestamp, source, text}`) and flow through the full pipeline
(extraction → resolution → knowledge graph → retrieval → orchestration). Every
fetch caches to disk, so ingestion also runs **offline / air-gapped**.

## Feeds

| Category | Feeds |
|---|---|
| osint-news | GDELT (conflict / maritime-security / narcotics), Defense News RSS, DVIDS |
| situational | ReliefWeb, USGS (significant + M4.5), GDACS alerts |
| advisories | CISA advisories, CISA ICS advisories |
| threat-intel | abuse.ch Feodo, URLhaus, ThreatFox (materialized as per-indicator reports) |

## Adapters

- **gdelt** — GDELT DOC 2.0 `artlist` JSON → article reports
- **reliefweb** — ReliefWeb API JSON → report titles
- **usgs** — USGS GeoJSON → event reports
- **rss** — generic RSS/Atom (`<item>`/`<entry>`), HTML stripped
- **ioc_lines** — IOC blocklists; extracts the first URL/IP **by pattern** (robust
  to header rows and differing CSV layouts)

## Usage

```bash
obsidia sources-list                       # browse feeds
obsidia sources-stats                       # coverage json
obsidia sources-ingest --cache .cache       # fetch -> reports
obsidia sources-ingest --offline --cache .cache   # air-gapped replay
obsidia demo-live --query "go-fast vessel near port"   # ingest + answer
```

```python
from obsidia.sources import HttpClient, collect
from obsidia.agents import Orchestrator
reports, errors = collect(HttpClient(cache_dir=".cache"))
orch = Orchestrator(reports, {})
print(orch.answer("maritime narcotics trafficking")["answer"])
```

## Notes

All 14 feeds are keyless. Respect each provider's terms of use and rate limits.
Feeds are ingested as *reporting* for analysis; corroborate before acting. See
`docs/LIMITATIONS.md` and `NOTICE`.
