from obsidia.fusion import corroborate, entities
from obsidia.fusion.schema import Observation


def _o(entity, disc, src, ts="2026-01-01T00:00:00Z", lat=None, lon=None,
       etype="vessel", rel="B", cred="2"):
    return Observation(discipline=disc, source=src, timestamp=ts, entity=entity,
                       entity_type=etype, lat=lat, lon=lon,
                       reliability=rel, credibility=cred)


def _assess(obs):
    res = entities.resolve_entities(obs)
    return res, corroborate.assess(res, obs)


def test_multi_source_scores_higher_than_single():
    multi = [_o("X", "GEOINT", "a"), _o("X", "OSINT", "b"), _o("X", "HUMINT", "c")]
    single = [_o("Y", "GEOINT", "a")]
    _r1, a1 = _assess(multi)
    _r2, a2 = _assess(single)
    s_multi = a1["corroboration"][0]["score"]
    s_single = a2["corroboration"][0]["score"]
    assert s_multi > s_single


def test_bands_assigned():
    obs = [_o("X", "GEOINT", "a"), _o("X", "OSINT", "b"),
           _o("X", "HUMINT", "c"), _o("X", "MASINT", "d")]
    _r, a = _assess(obs)
    assert a["corroboration"][0]["band"] in ("strong", "moderate", "weak", "single-source")


def test_single_source_band():
    _r, a = _assess([_o("Solo", "GEOINT", "a")])
    assert a["corroboration"][0]["band"] == "single-source"


def test_spatial_contradiction_detected():
    # same vessel 1000+ km apart in 5 minutes -> implausible
    obs = [_o("Ghost", "GEOINT", "a", ts="2026-01-01T00:00:00Z", lat=0.0, lon=0.0),
           _o("Ghost", "GEOINT", "b", ts="2026-01-01T00:05:00Z", lat=20.0, lon=20.0)]
    _r, a = _assess(obs)
    assert any(c["kind"] == "spatial-implausible-move" for c in a["contradictions"])


def test_no_contradiction_for_plausible_move():
    obs = [_o("Real", "GEOINT", "a", ts="2026-01-01T00:00:00Z", lat=9.0, lon=-79.0),
           _o("Real", "GEOINT", "b", ts="2026-01-01T06:00:00Z", lat=9.1, lon=-79.1)]
    _r, a = _assess(obs)
    assert not any(c["kind"] == "spatial-implausible-move" for c in a["contradictions"])


def test_attribute_conflict_detected():
    obs = [_o("Falcon", "GEOINT", "a", etype="vessel"),
           _o("Falcon", "GEOINT", "b", etype="vessel")]
    # force an attribute conflict by mutating one attribute post-hoc
    obs[0].attributes["status"] = "underway"
    obs[1].attributes["status"] = "moored"
    res = entities.resolve_entities(obs)
    a = corroborate.assess(res, obs)
    assert any(c["kind"] == "attribute-conflict" and c["attribute"] == "status"
               for c in a["contradictions"])


def test_summary_counts():
    obs = [_o("X", "GEOINT", "a"), _o("X", "OSINT", "b")]
    _r, a = _assess(obs)
    s = a["summary"]
    assert s["entities"] == 1
    assert "contradiction_count" in s


def test_higher_admiralty_grade_lifts_score():
    hi = [_o("X", "GEOINT", "a", rel="A", cred="1")]
    lo = [_o("Y", "GEOINT", "a", rel="E", cred="5")]
    _r1, a1 = _assess(hi)
    _r2, a2 = _assess(lo)
    assert a1["corroboration"][0]["avg_confidence"] > a2["corroboration"][0]["avg_confidence"]


def test_colocation_bonus():
    obs = [_o("X", "GEOINT", "a", lat=9.0, lon=-79.0),
           _o("X", "OSINT", "b", lat=9.001, lon=-79.001)]
    _r, a = _assess(obs)
    assert a["corroboration"][0]["colocation"] > 0.0
