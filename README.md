<h1 align="center">🟣 Confluex</h1>
<p align="center"><b>Self-hosted, edge-capable multi-INT fusion &amp; agent orchestration</b><br>
<i>Turn heterogeneous reporting into a source-cited, provenance-tracked picture — offline, at the tactical edge.</i></p>

<p align="center">
<img alt="license" src="https://img.shields.io/badge/license-COCL--1.0-6D28D9">
<img alt="python" src="https://img.shields.io/badge/python-3.9%2B-6D28D9">
<img alt="deps" src="https://img.shields.io/badge/dependencies-none%20(stdlib)-6D28D9">
<img alt="status" src="https://img.shields.io/badge/status-v0.4.0-6D28D9">
</p>

---

> **Built for:** SOLIC Accelerator / ONIX OTA — **Challenge Area 9: Open Topic (SOF enterprise).**
> SOF teams must turn OSINT, signals metadata, captured media, and reporting into decisions **without cloud reachback**. Vanguard is an AI analytic node you *own*: it ingests, fuses, and reasons over intelligence entirely on your hardware — air-gapped if needed — with every output traceable to its sources.

## Install

**Prerequisite:** Python **3.9+** (no other runtime deps — pure stdlib). The
one-command installers create a local `.venv` and install the `confluex` CLI.
Clone first: `git clone https://github.com/cognis-digital/cognis-vanguard && cd cognis-vanguard`

<details open><summary><b>Windows (PowerShell)</b></summary>

```powershell
.\install.ps1
.\.venv\Scripts\Activate.ps1      # activate this shell
confluex --help
confluex demo                      # end-to-end demo on bundled reporting
```
</details>

<details open><summary><b>macOS</b></summary>

```bash
./install.sh
source .venv/bin/activate         # activate this shell
confluex --help
confluex demo
```
</details>

<details open><summary><b>Linux</b></summary>

```bash
./install.sh
source .venv/bin/activate         # activate this shell
confluex --help
confluex demo
```
</details>

<details><summary><b>Docker</b></summary>

```bash
docker build -t cognis-vanguard .
docker run --rm cognis-vanguard --help
docker run --rm cognis-vanguard demo        # any confluex subcommand works
```
</details>

The installers are idempotent (safe to re-run) and print next-steps on
completion. `make install` / `make test` / `make demo` wrap the same flow on
POSIX systems.

## What it does

- 🧷 **Entity extraction** — regex indicators (IPv4, email, URL, SHA-256, crypto address, geo) + gazetteer named entities (orgs, persons, vessels, aliases).
- 🔗 **Resolution & fusion** — merges aliases/mentions into a provenance-tracked **knowledge graph** (every node/edge cites its source reports).
- 🔎 **Retrieval** — stdlib TF-IDF search returning source-cited passages.
- 🧠 **Multi-agent orchestration** — a deterministic tool loop (retrieve → extract → correlate → summarize) with a full **execution trace** for auditability.
- 🔌 **Pluggable reasoning** — deterministic offline provider by default (no model needed); optional **local open-weight model via Ollama** (self-hosted, no cloud egress).
- 📷 **Captured-media exploitation** — pluggable vision backend: deterministic CA-CFAR small-target detection (finds a swimmer/small craft/person as a 1–2 pixel target) or an optional local multimodal model; frames become graph-ready reports.
- 📤 **STIX 2.1 export** — deterministic bundles with source references.
- 🔒 **Offline / air-gap** — pure Python stdlib, **zero dependencies**.

## 🧩 Multi-INT fusion & Common Operating Picture (v0.4)

The `confluex.fusion` layer normalizes **six INT disciplines** into one
common `Observation` schema and fuses them into a source-cited, corroboration-
graded **Common Operating Picture** — for **situational awareness and force
protection only**.

- 🛰️ **INT-source adapters** — OSINT text, **SIGINT metadata (no content)**,
  GEOINT/location tracks, HUMINT-style reports, MASINT sensor events, and
  structured reporting, all normalized to one schema (synthetic data only).
- 🔗 **Cross-source entity resolution + de-confliction** — merge the same entity
  across disciplines/aliases/identifiers; surface identity ambiguity for review.
- 🎖️ **Admiralty-style grading** — source-reliability × info-credibility →
  per-observation confidence, feeding **corroboration scoring** (strong→single-
  source) and **contradiction detection** across sources.
- 🧭 **Track & pattern analytics** — track association, pattern-of-life, outlier-
  resistant anomaly/change detection, and **force-protection geofence alerts**.
- 🗺️ **Common Operating Picture** — fusion timeline + entity dossiers + a
  **self-contained HTML COP dashboard** (inline SVG map/timeline, **no JS/CDN**).
- 🔁 **Interop** — JSON, CSV, **STIX 2.1-like** bundles, and a **symbol-agnostic
  entity schema** (no MIL-STD-2525/APP-6 codes — descriptive, not a targeting overlay).

```bash
confluex fuse --scenario data/scenario_maritime.json --html cop.html  # COP + dashboard
confluex dossier --entity Nightjar                                    # entity dossier
confluex export --format stix > out.stix.json                         # interop
confluex demo-fusion                                                  # one-shot demo
```

> **Not targeting.** This fuses intelligence for *understanding* and *force
> protection*. It performs no target nomination, prioritization, fire-control,
> kill-chain, or strike support. See [`docs/FUSION.md`](docs/FUSION.md) and
> [`docs/INTEROP.md`](docs/INTEROP.md).

## Live feeds (14 keyless OSINT / situational / threat sources)

Vanguard ingests keyless live feeds — **GDELT**, **ReliefWeb**, **USGS**, **GDACS**,
**CISA advisories**, defense-news RSS, **DVIDS**, and **abuse.ch** IOC feeds —
and materializes each into a report that flows into extraction, the knowledge
graph, and retrieval. Fetches cache to disk for **offline / air-gap** replay.
See [`docs/FEEDS.md`](docs/FEEDS.md).

```bash
confluex sources-stats                              # feed coverage
confluex sources-ingest --feeds usgs_significant,feodo_iocs
confluex demo-live --query "maritime narcotics trafficking vessel"
```

## Quick start

```bash
git clone https://github.com/cognis-digital/confluex
cd confluex
python -m confluex demo --query "who controls wallet addr-B1" --stix out.stix.json
```

```bash
confluex query --reports data/sample_reports.json --gazetteer data/gazetteer.json \
                      --q "vessel rendezvous grey ferry logistics"
confluex correlate --reports data/sample_reports.json --gazetteer data/gazetteer.json --value addr-B1
confluex graph --reports data/sample_reports.json --gazetteer data/gazetteer.json --stix
```

```python
from confluex.agents import Orchestrator
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
| Fusion: cross-source entity resolution (synthetic scenario) | **1.00** |
| Fusion: corroboration band accuracy | **1.00** |
| Fusion: force-protection keep-out recall | **1.00** |

Throughput (single-thread, stdlib only): **~6,500–8,500 reports/sec** for full
ingest→extract→resolve→graph→index; query latency ~30 ms at 8k reports. The
fusion layer resolves + assesses + geofences **~32k–54k observations/sec** on
the same single thread. All numbers regenerated by `bench/run_all.py`.

## Honest scope

Vanguard is an **analytic aid**, not an autopilot. The default provider is
extractive (no generation); the optional Ollama backend adds generative
summarization on models *you* host. Extraction/resolution are deterministic
heuristics — strong on structured indicators and gazetteer entities, not a
substitute for an analyst. See [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md).

## Testing

```bash
python -m pytest -q      # 145 tests (core + multi-INT fusion + verification gates)
python bench/run_all.py  # regenerate RESULTS.md (core + fusion accuracy/perf)
```

## License

Source-available under **COCL v1.0** (see [LICENSE](LICENSE)). Non-commercial use
free; commercial use requires a license (`licensing@cognis.digital`).

<p align="center"><sub>© 2026 Cognis Digital LLC · <a href="https://cognis.digital">cognis.digital</a></sub></p>
