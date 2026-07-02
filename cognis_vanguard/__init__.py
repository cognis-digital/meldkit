"""Cognis Vanguard — self-hosted, edge-capable multi-INT fusion & agent
orchestration for austere/disconnected environments.

Ingests heterogeneous reporting, extracts and resolves entities, builds a
provenance-tracked knowledge graph, retrieves with source citations, and runs a
deterministic multi-agent tool loop. The reasoning/summarization backend is
pluggable: a deterministic offline provider (default, testable) or a local
open-weight model served via Ollama (self-hosted, no cloud egress).

(c) 2026 Cognis Digital LLC (Wyoming, USA). Source-available under COCL-1.0.
"""

__version__ = "0.3.0"
__all__ = [
    "model", "extract", "resolve", "index", "graph",
    "agents", "llm", "vision", "smalltarget", "stix", "report",
]
