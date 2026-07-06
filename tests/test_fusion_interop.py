import csv
import io
import json

from confluex.fusion import entities, interop
from confluex.fusion.schema import Observation


def _sample():
    obs = [
        Observation(discipline="GEOINT", source="a", timestamp="2026-01-01T00:00:00Z",
                    entity="MV X", entity_type="vessel", lat=9.0, lon=-79.0,
                    reliability="B", credibility="2"),
        Observation(discipline="OSINT", source="b", timestamp="2026-01-02T00:00:00Z",
                    entity="MV X", entity_type="vessel", text="seen at port"),
    ]
    res = entities.resolve_entities(obs)
    return obs, res


def test_json_export_shape():
    obs, res = _sample()
    d = json.loads(interop.to_json(obs, res))
    assert "observations" in d and "entities" in d
    assert len(d["observations"]) == 2


def test_csv_export_parses():
    obs, _ = _sample()
    text = interop.observations_to_csv(obs)
    rows = list(csv.DictReader(io.StringIO(text)))
    assert len(rows) == 2
    assert set(interop.OBS_COLUMNS).issubset(rows[0].keys())


def test_entities_csv():
    _obs, res = _sample()
    text = interop.entities_to_csv(res)
    rows = list(csv.DictReader(io.StringIO(text)))
    assert rows and rows[0]["canonical"] == "MV X"


def test_stix_bundle_shape():
    obs, res = _sample()
    b = interop.to_stix(obs, res)
    assert b["type"] == "bundle"
    types = {o["type"] for o in b["objects"]}
    assert "identity" in types
    assert "observed-data" in types
    assert "x-cognis-entity" in types
    assert "relationship" in types


def test_stix_deterministic():
    obs, res = _sample()
    assert interop.to_stix_json(obs, res) == interop.to_stix_json(obs, res)


def test_stix_observed_data_geo():
    obs, res = _sample()
    b = interop.to_stix(obs, res)
    od = [o for o in b["objects"] if o["type"] == "observed-data"]
    assert any(o["x_cognis_geo"] is not None for o in od)


def test_symbol_agnostic_has_no_symbol_codes():
    _obs, res = _sample()
    d = interop.to_symbol_agnostic(res)
    blob = json.dumps(d).lower()
    # explicitly symbol-agnostic: no APP-6 / 2525 / milsymbol codes
    assert "app6" not in blob and "app-6" not in blob
    assert "2525" not in blob
    assert "sidc" not in blob
    assert "symbol-agnostic" in blob


def test_symbol_agnostic_affiliation_neutral_default():
    _obs, res = _sample()
    d = interop.to_symbol_agnostic(res)
    for e in d["entities"]:
        assert e["affiliation"] in interop.AFFILIATIONS


def test_symbol_agnostic_entity_fields():
    _obs, res = _sample()
    d = interop.to_symbol_agnostic(res)
    e = d["entities"][0]
    for key in ("id", "label", "entity_type", "affiliation", "disciplines"):
        assert key in e
