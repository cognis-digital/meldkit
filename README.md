<h1 align="center">🟣 Cognis Vanguard</h1>
<p align="center"><b>Self-hosted, edge-capable multi-INT fusion &amp; agent orchestration</b><br>
<i>Turn heterogeneous reporting into a source-cited, provenance-tracked picture — offline, at the tactical edge.</i></p>

<p align="center">
<img alt="license" src="https://img.shields.io/badge/license-COCL--1.0-6D28D9">
<img alt="python" src="https://img.shields.io/badge/python-3.9%2B-6D28D9">
<img alt="deps" src="https://img.shields.io/badge/dependencies-none%20(stdlib)-6D28D9">
<img alt="status" src="https://img.shields.io/badge/status-v0.1.0-6D28D9">
</p>

---

> **Built for:** SOLIC Accelerator / ONIX OTA — **Challenge Area 9: Open Topic (SOF enterprise).**
> SOF teams must turn OSINT, signals metadata, captured media, and reporting into decisions **without cloud reachback**. Vanguard is an AI analytic node you *own*: it ingests, fuses, and reasons over intelligence entirely on your hardware — air-gapped if needed — with every output traceable to its sources.

## What it does

- 🧷 **Entity extraction** — regex indicators (IPv4, email, URL, SHA-256, crypto address, geo) + gazetteer named entities (orgs, persons, vessels, aliases).
- 🔗 **Resolution & fusion** — merges aliases/mentions into a provenance-tracked **knowledge graph** (every node/edge cites its source reports).
- 🔎 **Retrieval** — stdlib TF-IDF search returning source-cited passages.
- 🧠 **Multi-agent orchestration** — a deterministic tool loop (retrieve → extract → correlate → summarize) with a full **execution trace** for auditability.
- 🔌 **Pluggable reasoning** — deterministic offline provider by default (no model needed); optional **local open-weight model via Ollama** (self-hosted, no cloud egress).
- 📷 **Captured-media exploitation** — pluggable vision backend: deterministic CA-CFAR small-target detection (finds a swimmer/small craft/person as a 1–2 pixel target) or an optional local multimodal model; frames become graph-ready reports.
- 📤 **STIX 2.1 export** — deterministic bundles with source references.
- 🔒 **Offline / air-gap** — pure Python stdlib, **zero dependencies**.

## Live feeds (14 keyless OSINT / situational / threat sources)

Vanguard ingests keyless live feeds — **GDELT**, **ReliefWeb**, **USGS**, **GDACS**,
**CISA advisories**, defense-news RSS, **DVIDS**, and **abuse.ch** IOC feeds —
and materializes each into a report that flows into extraction, the knowledge
graph, and retrieval. Fetches cache to disk for **offline / air-gap** replay.
See [`docs/FEEDS.md`](docs/FEEDS.md).

```bash
cognis-vanguard sources-stats                              # feed coverage
cognis-vanguard sources-ingest --feeds usgs_significant,feodo_iocs
cognis-vanguard demo-live --query "maritime narcotics trafficking vessel"
```

## Quick start

```bash
git clone https://github.com/cognis-digital/cognis-vanguard
cd cognis-vanguard
python -m cognis_vanguard demo --query "who controls wallet addr-B1" --stix out.stix.json
```

```bash
cognis-vanguard query --reports data/sample_reports.json --gazetteer data/gazetteer.json \
                      --q "vessel rendezvous grey ferry logistics"
cognis-vanguard correlate --reports data/sample_reports.json --gazetteer data/gazetteer.json --value addr-B1
cognis-vanguard graph --reports data/sample_reports.json --gazetteer data/gazetteer.json --stix
```

```python
from cognis_vanguard.agents import Orchestrator
orch = Orchestrator(reports, gazetteer)          # optional: provider=OllamaProvider("llama3")
result = orch.answer("who controls wallet addr-B1")   # source-cited, with execution trace
```

## Verification & proof

Measured against a **ground-truth goldset** and gated in CI. Reproduce with
`python bench/run_all.py` → [`RESULTS.md`](RESULTS.md).

| Task | Metric |
|---|---|
| Entity extraction | P/R/F1 = **1.00** (14/14, 0 FP) |
| Entity resolution accuracy | **1.00** |
| Retrieval precision@1 / recall@3 / MRR | **1.00 / 1.00 / 1.00** |
| STIX determinism | ✓ identical across runs |

Throughput (single-thread, stdlib only): **~6,500–8,500 reports/sec** for full
ingest→extract→resolve→graph→index; query latency ~30 ms at 8k reports.

## Honest scope

Vanguard is an **analytic aid**, not an autopilot. The default provider is
extractive (no generation); the optional Ollama backend adds generative
summarization on models *you* host. Extraction/resolution are deterministic
heuristics — strong on structured indicators and gazetteer entities, not a
substitute for an analyst. See [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md).

## Testing

```bash
python -m pytest -q      # 24 tests (20 unit + 4 verification gates)
python bench/run_all.py  # regenerate RESULTS.md
```

## License

Source-available under **COCL v1.0** (see [LICENSE](LICENSE)). Non-commercial use
free; commercial use requires a license (`licensing@cognis.digital`).

<p align="center"><sub>© 2026 Cognis Digital LLC · <a href="https://cognis.digital">cognis.digital</a></sub></p>
