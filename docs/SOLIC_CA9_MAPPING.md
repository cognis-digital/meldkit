# SOLIC Challenge Area 9 (Open Topic) — Capability Mapping

Vanguard addresses a concrete SOF enterprise gap: **trustworthy AI analytics at
the disconnected tactical edge.**

| SOF need | Confluex | Module |
|---|---|---|
| Fuse multi-source reporting into one picture | Provenance-tracked knowledge graph from OSINT/SIGINT-meta/MARINT reports | `graph`, `resolve` |
| **Fuse six INT disciplines into a Common Operating Picture** | OSINT/SIGINT-meta/GEOINT/HUMINT/MASINT/STRUCTURED → common `Observation` schema → resolved entities, corroboration, tracks, COP | `fusion.*` |
| **Grade source trust** | NATO Admiralty-style reliability × credibility → per-observation confidence | `fusion.admiralty` |
| **Corroborate & catch contradictions** | Corroboration bands + spatial/attribute contradiction flags across sources | `fusion.corroborate` |
| **Situational awareness / force protection** | Track association, pattern-of-life, anomaly/change detection, geofence keep-out/AOI alerts | `fusion.tracks`, `fusion.geofence` |
| **Analyst-ready products** | Fusion timeline, per-entity dossiers, self-contained HTML COP dashboard (no JS/CDN) | `fusion.cop` |
| Operate offline / air-gapped | Zero-dependency, self-hosted; optional local model only | whole package |
| Trustworthy, auditable outputs | Source citations on every entity + full tool execution trace | `model`, `agents` |
| Rapid analyst tasking | Natural-language-style query → source-cited answer | `agents`, `index` |
| Own the AI (no cloud egress) | Deterministic default provider; optional local Ollama model | `llm` |
| Interoperability | STIX 2.1 export + fusion JSON/CSV/STIX-like/symbol-agnostic exports | `stix`, `fusion.interop` |

## Scope guardrail (explicit)

Vanguard is a **defensive multi-INT fusion and situational-awareness** analytic.
It supports *understanding* and *force protection*. It contains **no** targeting,
target-nomination, prioritization-for-engagement, fire-control, kill-chain, or
strike-support capability, and its symbol-agnostic export deliberately omits
military-symbology identification codes. This is a fixed design constraint, not a
configuration option.

## TRL posture (honest)
- **Components (TRL 5–6):** extraction, resolution, TF-IDF retrieval, graph
  fusion, STIX export, and the orchestration loop are working, tested software
  with reproducible accuracy metrics (`RESULTS.md`).
- **SOF-tailored integration (prototype):** the specific mission use case,
  target-hardware edge packaging, and classified-enclave audit logging are the
  post-award prototype scope, demonstrable at the July 24 event.

As an Open Topic entry, Vanguard is intentionally adaptable to the single
highest-value SOF use case the sponsor identifies.
