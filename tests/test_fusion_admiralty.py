from cognis_vanguard.fusion import admiralty
from cognis_vanguard.fusion.schema import Observation


def _obs(rel="", cred=""):
    return Observation(discipline="OSINT", source="s", timestamp="t",
                       reliability=rel, credibility=cred)


def test_grade_parses_code():
    g = admiralty.grade("B2")
    assert g["reliability"] == "B"
    assert g["credibility"] == "2"
    assert 0.0 < g["confidence"] <= 1.0


def test_grade_best_is_high():
    assert admiralty.grade("A1")["confidence"] == 1.0


def test_grade_worst_is_low():
    assert admiralty.grade("E5")["confidence"] < 0.3


def test_grade_bad_code_falls_back():
    g = admiralty.grade("ZZ")
    assert g["reliability"] == "F"
    assert g["credibility"] == "6"


def test_grade_ordering_monotone():
    a1 = admiralty.grade("A1")["confidence"]
    c3 = admiralty.grade("C3")["confidence"]
    e5 = admiralty.grade("E5")["confidence"]
    assert a1 > c3 > e5


def test_reliability_weight_bounds():
    for code in "ABCDEF":
        w = admiralty.reliability_weight(code)
        assert 0.0 <= w <= 1.0


def test_credibility_weight_bounds():
    for code in "123456":
        w = admiralty.credibility_weight(code)
        assert 0.0 <= w <= 1.0


def test_observation_confidence_neutral_when_ungraded():
    assert admiralty.observation_confidence(_obs()) == 0.5


def test_observation_confidence_uses_codes():
    hi = admiralty.observation_confidence(_obs("A", "1"))
    lo = admiralty.observation_confidence(_obs("E", "5"))
    assert hi > lo


def test_default_grade_for_disciplines():
    assert admiralty.default_grade_for("HUMINT") == "C3"
    assert admiralty.default_grade_for("SIGINT") == "B2"
    assert len(admiralty.default_grade_for("UNKNOWN")) == 2
