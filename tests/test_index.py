import os

from obsidia import extract
from obsidia.index import TfidfIndex, tokenize

D = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data"))


def test_tokenize_keeps_indicators():
    toks = tokenize("wallet addr-B1 at 203.0.113.10")
    assert "addr-b1" in toks
    assert "203.0.113.10" in toks


def test_search_ranks_relevant_first():
    reports = extract.load_reports(os.path.join(D, "sample_reports.json"))
    idx = TfidfIndex(reports)
    hits = idx.search("wallet addr-B1", k=3)
    assert hits
    assert hits[0]["report_id"] in {"R-001", "R-004"}
