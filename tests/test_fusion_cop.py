import os

from confluex.fusion import cop, scenario

D = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data"))
SCENARIO = os.path.join(D, "scenario_maritime.json")


def _result():
    return scenario.run_scenario(scenario.load_scenario(SCENARIO))


def test_scenario_loads_and_fuses():
    res = _result()
    assert res["counts"]["observations"] > 0
    assert res["counts"]["entities"] > 0
    assert res["counts"]["disciplines"] >= 5  # multi-INT


def test_timeline_ordered():
    res = _result()
    tl = cop.timeline(res)
    ts = [e["timestamp"] for e in tl]
    assert ts == sorted(ts)


def test_dossier_for_each_entity():
    res = _result()
    dossiers = cop.all_dossiers(res)
    assert len(dossiers) == len(res["entities"])
    for d in dossiers:
        assert "entity" in d and "provenance" in d
        assert "observation_ids" in d["provenance"]


def test_dossier_unknown_entity_raises():
    res = _result()
    try:
        cop.dossier(res, "ent--doesnotexist")
        assert False
    except KeyError:
        pass


def test_render_text_defensive_framing():
    txt = cop.render_text(_result())
    low = txt.lower()
    assert "not targeting" in low
    assert "force protection" in low


def test_render_html_self_contained():
    html = cop.render_html(_result())
    assert html.startswith("<!doctype html>")
    # no external resource loads (offline / CSP-safe)
    assert "http://" not in html.split("</head>")[0] or "example" in html
    assert "<script" not in html.lower()
    assert "cdn" not in html.lower()
    assert "src=\"http" not in html
    assert "@import" not in html


def test_render_html_has_map_and_defensive_note():
    html = cop.render_html(_result())
    assert "<svg" in html
    assert "not targeting" in html.lower()


def test_maritime_scenario_resolves_nightjar():
    res = _result()
    names = [e.canonical for e in res["entities"]]
    assert any("Nightjar" in n for n in names)


def test_zone_alerts_present():
    res = _result()
    assert res["counts"]["zone_alerts"] > 0


def test_no_validation_problems_in_sample():
    res = _result()
    assert res["validation_problems"] == {}


def test_to_serializable_is_json_ready():
    import json
    res = _result()
    s = scenario.to_serializable(res)
    json.dumps(s)  # must not raise
    assert isinstance(s["observations"][0], dict)
