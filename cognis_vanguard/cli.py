"""Cognis Vanguard CLI."""

from __future__ import annotations

import argparse
import json
import os
import sys

from . import __version__
from . import extract as extractmod
from . import graph as graphmod
from . import report as reportmod
from . import stix as stixmod
from .agents import Orchestrator
from .sources import ingest as vfeeds
from .sources.client import HttpClient

_HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(_HERE, "..", "data"))


def _load(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _data(name):
    return os.path.join(DATA_DIR, name)


def cmd_demo(args):
    reports = _load(_data("sample_reports.json"))
    gaz = _load(_data("gazetteer.json"))
    orch = Orchestrator(reports, gaz)
    result = orch.answer(args.query or "financing network infrastructure wallet", k=3)
    print(reportmod.render_text(result))
    print(f"\nKnowledge graph: {len(orch.graph.entities)} entities, {len(orch.graph.edges)} edges")
    if args.stix:
        with open(args.stix, "w", encoding="utf-8") as f:
            f.write(stixmod.to_json(stixmod.bundle_from_graph(orch.graph)))
        print(f"[+] STIX 2.1 bundle -> {args.stix}")
    return 0


def cmd_query(args):
    reports = _load(args.reports)
    gaz = _load(args.gazetteer) if args.gazetteer else {}
    orch = Orchestrator(reports, gaz)
    result = orch.answer(args.q, k=args.k)
    print(reportmod.render_json(result) if args.json else reportmod.render_text(result))
    return 0


def cmd_extract(args):
    reports = _load(args.reports)
    gaz = _load(args.gazetteer) if args.gazetteer else {}
    print(json.dumps(extractmod.extract(reports, gaz), indent=2))
    return 0


def cmd_correlate(args):
    reports = _load(args.reports)
    gaz = _load(args.gazetteer) if args.gazetteer else {}
    g = graphmod.build_graph(reports, gaz)
    print(json.dumps(graphmod.correlate(g, args.value, args.type), indent=2))
    return 0


def cmd_graph(args):
    reports = _load(args.reports)
    gaz = _load(args.gazetteer) if args.gazetteer else {}
    g = graphmod.build_graph(reports, gaz)
    out = stixmod.to_json(stixmod.bundle_from_graph(g)) if args.stix else json.dumps(g.to_dict(), indent=2)
    print(out)
    return 0


def cmd_sources_list(args):
    for s in vfeeds.list_sources(category=args.category):
        print(f"{s['name']:22} {s['category']:14} {s['adapter']:10} {s['url'][:60]}")
    print(f"\n{len(vfeeds.list_sources(category=args.category))} feeds")
    return 0


def cmd_sources_stats(args):
    print(json.dumps(vfeeds.stats(), indent=2))
    return 0


def cmd_sources_ingest(args):
    client = HttpClient(cache_dir=args.cache, offline=args.offline)
    feeds = args.feeds.split(",") if args.feeds else None
    reports, errors = vfeeds.collect(client, feeds=feeds, limit_per=args.limit)
    print(f"ingested {len(reports)} reports from live feeds")
    if errors:
        print("feed errors:", json.dumps(errors, indent=2))
    for r in reports[:5]:
        print(f"  [{r['source']}] {r['text'][:90]}")
    return 0


def cmd_analyze_image(args):
    """Captured-media exploitation demo: small-target detection over a frame,
    materialized as a report and fused into the knowledge graph."""
    from . import smalltarget, vision
    img, truth = smalltarget.demo_scene()
    report = vision.analyze_media(img, source="captured-media", ts="2026-07-02T00:00:00Z", k=args.k)
    print(f"[captured-media] {report['text']}")
    print(f"targets: {len(report['targets'])} (planted: {len(truth)})")
    orch = Orchestrator([report], {})
    res = orch.answer("small object person vessel target", k=1)
    print(f"fused into graph: {len(orch.graph.entities)} entities; cited {res['citations']}")
    return 0


def cmd_demo_live(args):
    client = HttpClient(cache_dir=args.cache, offline=args.offline)
    reports, errors = vfeeds.collect(client, limit_per=args.limit)
    if not reports:
        print("no reports ingested (offline with empty cache?)")
        if errors:
            print(json.dumps(errors, indent=2))
        return 1
    orch = Orchestrator(reports, {})
    result = orch.answer(args.query, k=args.k)
    print(reportmod.render_text(result))
    print(f"\nIngested {len(reports)} live reports | graph: "
          f"{len(orch.graph.entities)} entities, {len(orch.graph.edges)} edges")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="cognis-vanguard",
                                description="Cognis Vanguard — self-hosted multi-INT fusion & orchestration")
    p.add_argument("--version", action="version", version=f"cognis-vanguard {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    d = sub.add_parser("demo", help="end-to-end demo on bundled reporting")
    d.add_argument("--query")
    d.add_argument("--stix")
    d.set_defaults(func=cmd_demo)

    q = sub.add_parser("query", help="answer a query with source citations")
    q.add_argument("--reports", required=True)
    q.add_argument("--gazetteer")
    q.add_argument("--q", required=True)
    q.add_argument("--k", type=int, default=3)
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=cmd_query)

    e = sub.add_parser("extract", help="extract entities from reports")
    e.add_argument("--reports", required=True)
    e.add_argument("--gazetteer")
    e.set_defaults(func=cmd_extract)

    c = sub.add_parser("correlate", help="entities co-mentioned with a target")
    c.add_argument("--reports", required=True)
    c.add_argument("--gazetteer")
    c.add_argument("--value", required=True)
    c.add_argument("--type")
    c.set_defaults(func=cmd_correlate)

    g = sub.add_parser("graph", help="emit knowledge graph (JSON or STIX)")
    g.add_argument("--reports", required=True)
    g.add_argument("--gazetteer")
    g.add_argument("--stix", action="store_true")
    g.set_defaults(func=cmd_graph)

    sl = sub.add_parser("sources-list", help="list live feeds")
    sl.add_argument("--category")
    sl.set_defaults(func=cmd_sources_list)

    ss = sub.add_parser("sources-stats", help="feed coverage statistics")
    ss.set_defaults(func=cmd_sources_stats)

    ing = sub.add_parser("sources-ingest", help="fetch live feeds -> reports")
    ing.add_argument("--feeds", help="comma-separated feed names")
    ing.add_argument("--offline", action="store_true")
    ing.add_argument("--cache", default=".cache")
    ing.add_argument("--limit", type=int, default=50)
    ing.set_defaults(func=cmd_sources_ingest)

    ai = sub.add_parser("analyze-image", help="captured-media small-target exploitation demo")
    ai.add_argument("--k", type=float, default=5.0)
    ai.set_defaults(func=cmd_analyze_image)

    dl = sub.add_parser("demo-live", help="ingest live feeds and answer a query")
    dl.add_argument("--query", default="maritime narcotics trafficking vessel")
    dl.add_argument("--k", type=int, default=3)
    dl.add_argument("--offline", action="store_true")
    dl.add_argument("--cache", default=".cache")
    dl.add_argument("--limit", type=int, default=50)
    dl.set_defaults(func=cmd_demo_live)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
