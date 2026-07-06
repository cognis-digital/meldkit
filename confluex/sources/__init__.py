"""Live feed integration for Confluex.

Pulls keyless OSINT / situational-awareness / threat feeds and materializes them
as Vanguard *reports* (id, timestamp, source, text) that flow straight into
extraction, resolution, the knowledge graph, and retrieval. Every fetch caches
to disk so ingestion also runs offline / air-gapped.
"""

from __future__ import annotations

from .catalog import CATALOG
from .client import HttpClient
from .ingest import collect, stats

__all__ = ["CATALOG", "HttpClient", "collect", "stats"]
