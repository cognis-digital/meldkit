"""Accuracy evaluation against the ground-truth goldset."""

from __future__ import annotations

import json
import os

from obsidia import extract as extractmod
from obsidia import graph as graphmod
from obsidia import stix
from obsidia.index import TfidfIndex
from obsidia.resolve import resolve

from .metrics import mrr, precision_at_k, prf, recall_at_k

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA = os.path.normpath(os.path.join(_HERE, "..", "data"))


def _load(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate() -> dict:
    reports = _load(os.path.join(_DATA, "sample_reports.json"))
    gaz = _load(os.path.join(_DATA, "gazetteer.json"))
    gold = _load(os.path.join(_HERE, "goldset.json"))

    # --- Extraction: unique (type, canonical, source_ref) triples ---
    mentions = extractmod.extract(reports, gaz)
    pred_triples = {(m["type"], m["canonical"], m["source_ref"]) for m in mentions}
    gold_triples = set()
    for rid, ents in gold["entities"].items():
        for etype, canon in ents:
            gold_triples.add((etype, canon, rid))
    extraction = prf(pred_triples, gold_triples)

    # --- Resolution: expected merged source sets ---
    resolved = resolve(mentions)
    res_index = {(r["type"], r["canonical"].lower()): set(r["sources"]) for r in resolved}
    correct = 0
    for exp in gold["resolution"]:
        got = res_index.get((exp["type"], exp["canonical"].lower()), set())
        if got == set(exp["expected_sources"]):
            correct += 1
    resolution_accuracy = round(correct / len(gold["resolution"]), 4)

    # --- Retrieval: precision@1, recall@3, MRR averaged over queries ---
    index = TfidfIndex(reports)
    p1s, r3s, mrrs = [], [], []
    for q in gold["queries"]:
        ranked = [h["report_id"] for h in index.search(q["q"], k=5)]
        p1s.append(precision_at_k(ranked, q["relevant"], 1))
        r3s.append(recall_at_k(ranked, q["relevant"], 3))
        mrrs.append(mrr(ranked, q["relevant"]))
    retrieval = {
        "precision_at_1": round(sum(p1s) / len(p1s), 4),
        "recall_at_3": round(sum(r3s) / len(r3s), 4),
        "mrr": round(sum(mrrs) / len(mrrs), 4),
    }

    # --- Determinism: identical STIX bundle across two graph builds ---
    g1 = graphmod.build_graph(reports, gaz)
    g2 = graphmod.build_graph(reports, gaz)
    determinism = stix.to_json(stix.bundle_from_graph(g1)) == stix.to_json(stix.bundle_from_graph(g2))

    return {
        "dataset": {"reports": len(reports), "gold_entities": len(gold_triples)},
        "extraction": extraction,
        "resolution_accuracy": resolution_accuracy,
        "retrieval": retrieval,
        "determinism": determinism,
    }


def main():
    print(json.dumps(evaluate(), indent=2))


if __name__ == "__main__":
    main()
