import os

from obsidia import extract
from obsidia.agents import Orchestrator

D = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data"))


def _orch():
    reports = extract.load_reports(os.path.join(D, "sample_reports.json"))
    gaz = extract.load_gazetteer(os.path.join(D, "gazetteer.json"))
    return Orchestrator(reports, gaz)


def test_answer_is_source_cited():
    result = _orch().answer("who controls wallet addr-B1", k=3)
    assert result["citations"], "answer must cite reports"
    assert all(c.startswith("R-") for c in result["citations"])


def test_execution_trace_records_tools():
    result = _orch().answer("infrastructure server 203.0.113.10", k=3)
    tools = [s["tool"] for s in result["trace"]]
    assert tools == ["retrieve", "extract", "correlate", "summarize"]


def test_answer_deterministic():
    a = _orch().answer("vessel grey ferry logistics", k=3)
    b = _orch().answer("vessel grey ferry logistics", k=3)
    assert a["answer"] == b["answer"]
    assert a["citations"] == b["citations"]
