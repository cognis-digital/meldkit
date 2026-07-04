import os

from obsidia import extract

D = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data"))


def _load():
    return extract.load_reports(os.path.join(D, "sample_reports.json")), \
        extract.load_gazetteer(os.path.join(D, "gazetteer.json"))


def test_regex_types():
    reports, _ = _load()
    r1 = next(r for r in reports if r["id"] == "R-001")
    types = {m["type"] for m in extract.extract_regex(r1)}
    assert "ipv4" in types
    assert "crypto-address" in types


def test_gazetteer_alias_maps_to_canonical():
    reports, gaz = _load()
    r1 = next(r for r in reports if r["id"] == "R-001")
    canon = {m["canonical"] for m in extract.extract_gazetteer(r1, gaz)}
    assert "Red Harbor Syndicate" in canon
    assert "Marek Voss" in canon


def test_sha256_and_email():
    reports, gaz = _load()
    ments = extract.extract(reports, gaz)
    types = {m["type"] for m in ments}
    assert "sha256" in types
    assert "email" in types
    assert "geo" in types
