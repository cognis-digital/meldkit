# Architecture

```
 reports ─► extract ─► resolve ─► graph (provenance) ─┬─► correlate
                          │                            └─► stix / report
                          └─► index (TF-IDF) ─► retrieve
                                     │
                 agents.Orchestrator ┴─ retrieve → extract → correlate → summarize (LLM optional)
```

| Module | Responsibility |
|---|---|
| `model` | `Entity`, `Edge`, `KnowledgeGraph` with provenance; O(1) indexed edges. |
| `extract` | Regex + gazetteer entity extraction. |
| `resolve` | Alias/mention resolution with source sets. |
| `index` | Stdlib TF-IDF retrieval (cosine). |
| `graph` | Build provenance graph + co-occurrence correlation. |
| `agents` | Deterministic multi-agent tool loop + execution trace. |
| `llm` | Pluggable providers: deterministic (default) or Ollama (optional). |
| `stix` | STIX 2.1 export with deterministic IDs + source references. |
| `report` | Human-readable / JSON products. |
| `cli` | `obsidia` entry point. |

## Principles

1. **Provenance first** — every entity/edge cites its source report.
2. **Offline / self-hosted** — zero dependencies; optional local model only.
3. **Deterministic core** — reproducible outputs; only the optional generative
   backend can introduce variability (default provider is deterministic too).
4. **Auditable** — the orchestrator records every tool call.
5. **Composable** — each module is independently usable and tested.
