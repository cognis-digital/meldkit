from cognis_vanguard.fusion import adapters_int
from cognis_vanguard.fusion.adapters_int import (
    geoint, humint, masint, normalize, osint, sigint_meta, structured,
)


def test_osint_adapter():
    obs = osint([{"source": "n", "timestamp": "2026-01-01T00:00:00Z",
                  "title": "vessel seen", "entity": "MV X", "entity_type": "vessel"}])
    assert len(obs) == 1
    assert obs[0].discipline == "OSINT"
    assert obs[0].entity == "MV X"
    assert obs[0].text == "vessel seen"


def test_sigint_is_metadata_only_and_drops_content():
    obs = sigint_meta([{"emitter_id": "EM-1", "freq_band": "VHF", "bearing": 90,
                        "timestamp": "t", "content": "SECRET COMMS PAYLOAD"}])
    assert obs[0].discipline == "SIGINT"
    assert obs[0].entity == "EM-1"
    assert "content" not in obs[0].attributes
    assert "SECRET" not in obs[0].text
    assert "SECRET" not in str(obs[0].attributes)


def test_sigint_carries_only_externals():
    obs = sigint_meta([{"emitter_id": "EM-9", "link": "relay", "timestamp": "t"}])
    assert obs[0].attributes.get("emitter_id") == "EM-9"
    assert obs[0].attributes.get("link") == "relay"


def test_geoint_track_point():
    obs = geoint([{"entity": "MV X", "entity_type": "vessel", "lat": 9.0,
                   "lon": -79.0, "speed_kn": 8, "timestamp": "t", "imo": "999"}])
    assert obs[0].has_geo
    assert obs[0].attributes.get("speed_kn") == 8


def test_humint_report_and_default_grade():
    obs = humint([{"report": "worker saw crates", "timestamp": "t"}])
    assert obs[0].text == "worker saw crates"
    # default HUMINT grade is cautious C3
    assert obs[0].reliability == "C"
    assert obs[0].credibility == "3"


def test_humint_explicit_grade_preserved():
    obs = humint([{"report": "x", "timestamp": "t", "reliability": "A", "credibility": "1"}])
    assert obs[0].reliability == "A" and obs[0].credibility == "1"


def test_masint_sensor_event():
    obs = masint([{"sensor": "acoustic-1", "phenomenology": "acoustic",
                   "measurement": 138, "unit": "dB", "timestamp": "t"}])
    assert obs[0].discipline == "MASINT"
    assert obs[0].attributes["phenomenology"] == "acoustic"
    assert obs[0].attributes["measurement"] == 138


def test_structured_synthesizes_text():
    obs = structured([{"entity": "MV X", "entity_type": "vessel",
                       "imo": "999", "flag_state": "Panama", "timestamp": "t"}])
    assert "999" in obs[0].text or obs[0].attributes.get("imo") == "999"
    assert obs[0].attributes.get("flag_state") == "Panama"


def test_normalize_dispatch():
    obs = normalize("osint", [{"title": "x", "timestamp": "t"}])
    assert obs[0].discipline == "OSINT"


def test_normalize_unknown_discipline_raises():
    try:
        normalize("bogusint", [])
        assert False, "expected KeyError"
    except KeyError:
        pass


def test_adapters_registry_complete():
    for name in ("osint", "sigint", "geoint", "humint", "masint", "structured"):
        assert name in adapters_int.ADAPTERS


def test_default_grades_applied_when_missing():
    obs = osint([{"title": "x", "timestamp": "t"}])
    assert obs[0].reliability and obs[0].credibility
