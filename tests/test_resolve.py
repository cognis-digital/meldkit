import os

from confluex import extract
from confluex.resolve import resolve

D = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data"))


def _resolved():
    reports = extract.load_reports(os.path.join(D, "sample_reports.json"))
    gaz = extract.load_gazetteer(os.path.join(D, "gazetteer.json"))
    return resolve(extract.extract(reports, gaz))


def test_addr_merges_across_reports():
    r = _resolved()
    addr = next(x for x in r if x["type"] == "crypto-address" and x["canonical"] == "addr-B1")
    assert set(addr["sources"]) == {"R-001", "R-004"}


def test_org_alias_merges():
    r = _resolved()
    gf = next(x for x in r if x["type"] == "org" and x["canonical"] == "Grey Ferry Logistics")
    assert set(gf["sources"]) == {"R-002", "R-003"}
