import os

from obsidia import extract, graph, stix

D = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data"))


def _graph():
    reports = extract.load_reports(os.path.join(D, "sample_reports.json"))
    gaz = extract.load_gazetteer(os.path.join(D, "gazetteer.json"))
    return graph.build_graph(reports, gaz)


def test_graph_has_provenance():
    g = _graph()
    for e in g.entities.values():
        assert e.sources, f"entity {e.value} missing provenance"


def test_correlate_finds_cofinancing():
    g = _graph()
    links = graph.correlate(g, "addr-B1", "crypto-address")
    values = {a["value"] for a in links}
    # addr-B1 co-mentioned with Marek Voss / Red Harbor Syndicate
    assert "Marek Voss" in values


def test_stix_deterministic_and_shaped():
    g = _graph()
    b = stix.bundle_from_graph(g)
    assert b["type"] == "bundle"
    types = {o["type"] for o in b["objects"]}
    assert {"identity", "indicator", "relationship"} <= types
    assert stix.to_json(b) == stix.to_json(stix.bundle_from_graph(g))
