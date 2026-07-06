from confluex.fusion.schema import (
    INT_DISCIPLINES, Observation, haversine_km, observations_to_reports, validate,
)


def _obs(**kw):
    base = dict(discipline="OSINT", source="s", timestamp="2026-01-01T00:00:00Z", text="hello")
    base.update(kw)
    return Observation(**base)


def test_observation_deterministic_id():
    a = _obs()
    b = _obs()
    assert a.id == b.id
    assert a.id.startswith("obs--")


def test_observation_id_changes_with_content():
    assert _obs(text="a").id != _obs(text="b").id


def test_discipline_uppercased():
    assert _obs(discipline="osint").discipline == "OSINT"


def test_has_geo():
    assert not _obs().has_geo
    assert _obs(lat=1.0, lon=2.0).has_geo


def test_lat_lon_rounded():
    o = _obs(lat=1.123456789, lon=2.0)
    assert o.lat == round(1.123456789, 6)


def test_to_report_projection():
    o = _obs(lat=9.0, lon=-79.0)
    r = o.to_report()
    assert r["id"] == o.id
    assert r["source"] == "OSINT:s"
    assert "text" in r and "timestamp" in r


def test_from_dict_roundtrip():
    o = _obs(entity="X", entity_type="vessel")
    o2 = Observation.from_dict(o.to_dict())
    assert o2.id == o.id
    assert o2.entity == "X"


def test_from_dict_ignores_unknown_keys():
    o = Observation.from_dict({"discipline": "OSINT", "source": "s",
                               "timestamp": "t", "bogus": 1})
    assert o.source == "s"


def test_validate_clean():
    assert validate(_obs()) == []


def test_validate_bad_discipline():
    problems = validate(_obs(discipline="NOTREAL"))
    assert any("discipline" in p for p in problems)


def test_validate_bad_geo():
    assert any("lat" in p for p in validate(_obs(lat=200.0, lon=0.0)))
    assert any("lon" in p for p in validate(_obs(lat=0.0, lon=999.0)))


def test_validate_bad_codes():
    assert any("reliability" in p for p in validate(_obs(reliability="Z")))
    assert any("credibility" in p for p in validate(_obs(credibility="9")))


def test_all_disciplines_valid():
    for d in INT_DISCIPLINES:
        assert validate(_obs(discipline=d)) == []


def test_haversine_zero():
    assert haversine_km(9.0, -79.0, 9.0, -79.0) == 0.0


def test_haversine_known_distance():
    # ~111 km per degree of latitude
    d = haversine_km(0.0, 0.0, 1.0, 0.0)
    assert 110 < d < 112


def test_observations_to_reports():
    reps = observations_to_reports([_obs(), _obs(text="two")])
    assert len(reps) == 2
    assert all("id" in r for r in reps)


def test_sigint_content_never_in_report_text():
    # pure-metadata obs down-projects to a text that is the metadata summary
    o = _obs(discipline="SIGINT", text="Signal metadata: emitter EM-1")
    assert "content" not in o.to_report()["text"].lower()
