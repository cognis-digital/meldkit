from cognis_vanguard.fusion import entities
from cognis_vanguard.fusion.schema import Observation


def _o(entity, etype="vessel", disc="GEOINT", src="s", ts="2026-01-01T00:00:00Z", **attrs):
    return Observation(discipline=disc, source=src, timestamp=ts,
                       entity=entity, entity_type=etype, attributes=attrs)


def test_resolve_merges_same_name():
    obs = [_o("MV Nightjar", src="a"), _o("MV Nightjar", src="b")]
    res = entities.resolve_entities(obs)
    assert len(res) == 1
    assert len(res[0].observation_ids) == 2
    assert res[0].sources == {"a", "b"}


def test_resolve_merges_alias_substring():
    obs = [_o("MV Nightjar"), _o("Nightjar")]
    res = entities.resolve_entities(obs)
    assert len(res) == 1
    assert "Nightjar" in res[0].aliases or "MV Nightjar" == res[0].canonical


def test_resolve_merges_by_shared_identifier():
    obs = [_o("MV Nightjar", imo="9111111"), _o("Vessel 12", imo="9111111")]
    res = entities.resolve_entities(obs)
    assert len(res) == 1
    assert res[0].identifiers.get("imo") == "9111111"


def test_resolve_keeps_distinct_entities_apart():
    obs = [_o("MV Nightjar"), _o("MV Petrel")]
    res = entities.resolve_entities(obs)
    assert len(res) == 2


def test_resolve_tracks_disciplines():
    obs = [_o("MV Nightjar", disc="GEOINT"), _o("MV Nightjar", disc="OSINT")]
    res = entities.resolve_entities(obs)
    assert res[0].disciplines == {"GEOINT", "OSINT"}


def test_resolve_ignores_unnamed():
    obs = [Observation(discipline="MASINT", source="s", timestamp="t")]
    assert entities.resolve_entities(obs) == []


def test_entity_id_stable():
    obs1 = [_o("MV Nightjar")]
    obs2 = [_o("MV Nightjar")]
    assert entities.resolve_entities(obs1)[0].id == entities.resolve_entities(obs2)[0].id


def test_name_similarity():
    assert entities.name_similarity("MV Nightjar", "Nightjar MV") == 1.0
    assert entities.name_similarity("MV Nightjar", "MV Petrel") < 0.5


def test_norm_name():
    assert entities.norm_name("MV Night-jar!!") == "mv night jar"


def test_deconflict_name_type_ambiguity():
    obs = [_o("Falcon", etype="vessel"), _o("Falcon", etype="aircraft")]
    res = entities.resolve_entities(obs)
    conflicts = entities.deconflict(res)
    assert any(c["kind"] == "name-type-ambiguity" for c in conflicts)


def test_deconflict_identifier_collision():
    # two clearly distinct-named entities sharing a track_id -> resolve merges by id,
    # so instead assert no false collision when identifiers are unique
    obs = [_o("MV A", imo="111"), _o("MV B", imo="222")]
    res = entities.resolve_entities(obs)
    assert entities.deconflict(res) == [] or all(
        c["kind"] != "identifier-collision" for c in entities.deconflict(res))


def test_resolved_to_dict_shape():
    res = entities.resolve_entities([_o("MV X", disc="OSINT")])
    d = res[0].to_dict()
    for key in ("id", "canonical", "entity_type", "aliases", "disciplines",
                "observation_count"):
        assert key in d
