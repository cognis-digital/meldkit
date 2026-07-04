from obsidia.fusion import entities, tracks
from obsidia.fusion.schema import Observation


def _o(entity, ts, lat, lon, disc="GEOINT", src="s"):
    return Observation(discipline=disc, source=src, timestamp=ts, entity=entity,
                       entity_type="vessel", lat=lat, lon=lon)


def _resolve_one(obs):
    return entities.resolve_entities(obs)[0], {o.id: o for o in obs}


def test_associate_track_orders_by_time():
    obs = [_o("X", "2026-01-01T06:00:00Z", 9.1, -79.1),
           _o("X", "2026-01-01T00:00:00Z", 9.0, -79.0)]
    ent, by_id = _resolve_one(obs)
    tr = tracks.associate_track(ent, by_id)
    assert tr["points"][0]["ts"] < tr["points"][1]["ts"]
    assert tr["point_count"] == 2


def test_track_legs_computed():
    obs = [_o("X", "2026-01-01T00:00:00Z", 9.0, -79.0),
           _o("X", "2026-01-01T06:00:00Z", 9.5, -79.0)]
    ent, by_id = _resolve_one(obs)
    tr = tracks.associate_track(ent, by_id)
    assert len(tr["legs"]) == 1
    assert tr["legs"][0]["distance_km"] > 0
    assert tr["legs"][0]["speed_kmh"] is not None
    assert tr["total_distance_km"] > 0


def test_track_single_point_no_legs():
    obs = [_o("X", "2026-01-01T00:00:00Z", 9.0, -79.0)]
    ent, by_id = _resolve_one(obs)
    tr = tracks.associate_track(ent, by_id)
    assert tr["legs"] == []


def test_pattern_of_life_active_hours():
    obs = [_o("X", "2026-01-01T02:00:00Z", 9.0, -79.0),
           _o("X", "2026-01-02T02:00:00Z", 9.0, -79.0),
           _o("X", "2026-01-03T02:00:00Z", 9.0, -79.0)]
    ent, by_id = _resolve_one(obs)
    pol = tracks.pattern_of_life(ent, by_id)
    assert 2 in pol["active_hours_utc"]
    assert pol["primary_dwell"] is not None


def test_pattern_of_life_dwell_clusters():
    # two distinct location clusters far apart
    obs = [_o("X", "2026-01-01T00:00:00Z", 9.0, -79.0),
           _o("X", "2026-01-01T01:00:00Z", 9.001, -79.001),
           _o("X", "2026-01-02T00:00:00Z", 40.0, -70.0)]
    ent, by_id = _resolve_one(obs)
    pol = tracks.pattern_of_life(ent, by_id)
    assert len(pol["dwell_areas"]) == 2


def test_speed_anomaly_flagged():
    # steady slow legs then a huge jump
    obs = [_o("X", "2026-01-01T00:00:00Z", 9.00, -79.0),
           _o("X", "2026-01-01T01:00:00Z", 9.01, -79.0),
           _o("X", "2026-01-01T02:00:00Z", 9.02, -79.0),
           _o("X", "2026-01-01T03:00:00Z", 9.03, -79.0),
           _o("X", "2026-01-01T03:10:00Z", 12.0, -79.0)]
    ent, by_id = _resolve_one(obs)
    anoms = tracks.detect_anomalies(ent, by_id)
    assert any(a["kind"] == "speed-anomaly" for a in anoms)


def test_off_pattern_location_flagged():
    obs = [_o("X", f"2026-01-0{i}T02:00:00Z", 9.0, -79.0) for i in range(1, 6)]
    obs.append(_o("X", "2026-01-06T02:00:00Z", 40.0, -70.0))
    ent, by_id = _resolve_one(obs)
    anoms = tracks.detect_anomalies(ent, by_id)
    assert any(a["kind"] == "off-pattern-location" for a in anoms)


def test_detect_change_appeared_disappeared():
    prev = [_o("Alpha", "2026-01-01T00:00:00Z", 9.0, -79.0)]
    curr = [_o("Bravo", "2026-01-02T00:00:00Z", 9.0, -79.0)]
    change = tracks.detect_change(prev, curr)
    assert "bravo" in change["appeared"]
    assert "alpha" in change["disappeared"]


def test_detect_change_discipline_changed():
    prev = [_o("Alpha", "2026-01-01T00:00:00Z", 9.0, -79.0, disc="GEOINT")]
    curr = [_o("Alpha", "2026-01-02T00:00:00Z", 9.0, -79.0, disc="OSINT")]
    change = tracks.detect_change(prev, curr)
    assert "alpha" in change["discipline_changed"]
