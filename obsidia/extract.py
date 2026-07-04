"""Entity extraction from free-text reports.

Regex extractors for structured indicators (IPv4, email, URL, SHA-256, crypto
address, lat/long) plus a gazetteer matcher for named entities (orgs, persons,
vessels, aliases). Deterministic and offline. An optional LLM backend can be
layered on top for open-ended extraction, but the tested core does not require
one.

Report schema: {"id": str, "timestamp": ISO8601, "text": str, "source": str}
"""

from __future__ import annotations

import json
import re

REGEXES = {
    "ipv4": re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"),
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "url": re.compile(r"https?://[^\s)]+"),
    "sha256": re.compile(r"\b[a-fA-F0-9]{64}\b"),
    "crypto-address": re.compile(r"\b(?:bc1[a-z0-9]{8,}|0x[a-fA-F0-9]{6,}|addr-[A-Za-z0-9]+)\b"),
    "geo": re.compile(r"-?\d{1,3}\.\d{3,},\s*-?\d{1,3}\.\d{3,}"),
}


def load_reports(path: str) -> list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_gazetteer(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _norm_value(etype: str, value: str) -> str:
    if etype in ("email", "url", "sha256"):
        return value.lower()
    return value


def extract_regex(report: dict) -> list:
    text = report.get("text", "")
    rid = report["id"]
    found = []
    for etype, rx in REGEXES.items():
        for m in rx.finditer(text):
            val = m.group(0)
            found.append({"type": etype, "value": _norm_value(etype, val),
                          "canonical": _norm_value(etype, val),
                          "source_ref": rid, "start": m.start(), "end": m.end()})
    return found


def extract_gazetteer(report: dict, gazetteer: dict) -> list:
    """gazetteer schema: {entity_type: {canonical: [aliases...]}}"""
    text = report.get("text", "")
    low = text.lower()
    rid = report["id"]
    found = []
    for etype, entries in gazetteer.items():
        for canonical, aliases in entries.items():
            for term in [canonical, *aliases]:
                for m in re.finditer(r"\b" + re.escape(term.lower()) + r"\b", low):
                    found.append({"type": etype, "value": text[m.start():m.end()],
                                  "canonical": canonical, "source_ref": rid,
                                  "start": m.start(), "end": m.end()})
    return found


def extract(reports: list, gazetteer: dict | None = None) -> list:
    gazetteer = gazetteer or {}
    out = []
    for r in reports:
        out.extend(extract_regex(r))
        out.extend(extract_gazetteer(r, gazetteer))
    return out
