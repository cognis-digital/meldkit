"""Deterministic multi-agent orchestrator.

Exposes analytic tools (retrieve, extract, correlate, summarize) and a default
plan that chains them into a single source-cited answer. Every tool call is
logged to an execution trace for auditability. The orchestration is
deterministic; only the optional LLM summarizer can introduce variability, and
the default provider is deterministic too.
"""

from __future__ import annotations

from collections import Counter

from .extract import extract
from .graph import build_graph, correlate
from .index import TfidfIndex
from .llm import DeterministicProvider


class Orchestrator:
    def __init__(self, reports: list, gazetteer: dict | None = None, provider=None):
        self.reports = reports
        self.by_id = {r["id"]: r for r in reports}
        self.gazetteer = gazetteer or {}
        self.index = TfidfIndex(reports)
        self.graph = build_graph(reports, self.gazetteer)
        self.provider = provider or DeterministicProvider()
        self.trace: list = []

    def _log(self, tool, args, note):
        self.trace.append({"tool": tool, "args": args, "note": note})

    def tool_retrieve(self, query, k=5):
        hits = self.index.search(query, k)
        self._log("retrieve", {"query": query, "k": k}, f"{len(hits)} hits")
        return hits

    def tool_extract(self, report_ids):
        reps = [self.by_id[i] for i in report_ids if i in self.by_id]
        ents = extract(reps, self.gazetteer)
        self._log("extract", {"report_ids": report_ids}, f"{len(ents)} mentions")
        return ents

    def tool_correlate(self, value, etype=None):
        res = correlate(self.graph, value, etype)
        self._log("correlate", {"value": value, "type": etype}, f"{len(res)} links")
        return res

    def tool_summarize(self, query, report_ids, max_sentences=3):
        ctx = [self.by_id[i]["text"] for i in report_ids if i in self.by_id]
        out = self.provider.complete(query, context=ctx, max_sentences=max_sentences)
        self._log("summarize", {"query": query, "report_ids": report_ids}, f"{len(out)} chars")
        return out

    def answer(self, query, k=3):
        """Plan: retrieve -> extract -> correlate(pivot) -> summarize."""
        self.trace = []
        hits = self.tool_retrieve(query, k)
        rids = [h["report_id"] for h in hits]
        ents = self.tool_extract(rids)
        counts = Counter((e["type"], e["canonical"]) for e in ents)
        pivot = counts.most_common(1)[0][0] if counts else None
        links = self.tool_correlate(pivot[1], pivot[0]) if pivot else []
        summary = self.tool_summarize(query, rids)
        return {
            "query": query,
            "answer": summary,
            "citations": rids,
            "pivot_entity": ({"type": pivot[0], "value": pivot[1]} if pivot else None),
            "correlated": links,
            "entities": ents,
            "trace": self.trace,
        }
