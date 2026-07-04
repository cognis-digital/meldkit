"""Fetch feeds and materialize Vanguard reports; coverage stats."""

from __future__ import annotations

from . import adapters
from .catalog import CATALOG

ADAPTERS = {
    "gdelt": adapters.gdelt,
    "reliefweb": adapters.reliefweb,
    "usgs": adapters.usgs,
    "rss": adapters.rss,
    "ioc_lines": adapters.ioc_lines,
}

_BY_NAME = {s["name"]: s for s in CATALOG}
DEFAULT_FEEDS = ["gdelt_conflict", "reliefweb_reports", "usgs_significant",
                 "cisa_advisories", "feodo_iocs"]


def get_source(name: str) -> dict:
    if name not in _BY_NAME:
        raise KeyError(f"unknown feed: {name}")
    return _BY_NAME[name]


def list_sources(category=None) -> list:
    return [s for s in CATALOG if category is None or s["category"] == category]


def collect(client, feeds=None, limit_per: int = 50):
    """Fetch feeds -> (reports, errors). Report ids are de-duplicated."""
    reports = []
    errors = {}
    seen = set()
    for name in (feeds or DEFAULT_FEEDS):
        try:
            src = get_source(name)
            adapter = ADAPTERS[src["adapter"]]
            for rep in adapter(client.get(src["url"]), source=name)[:limit_per]:
                if rep["id"] in seen:
                    continue
                seen.add(rep["id"])
                reports.append(rep)
        except Exception as e:
            errors[name] = str(e)
    return reports, errors


def stats() -> dict:
    by_cat = {}
    keyless = 0
    for s in CATALOG:
        by_cat[s["category"]] = by_cat.get(s["category"], 0) + 1
        keyless += 1 if s["keyless"] else 0
    return {"total": len(CATALOG), "keyless": keyless,
            "by_category": dict(sorted(by_cat.items())),
            "adapters": sorted(ADAPTERS)}
