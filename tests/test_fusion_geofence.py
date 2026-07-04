from obsidia.fusion import geofence
from obsidia.fusion.schema import Observation


def _o(entity, lat, lon, ts="2026-01-01T00:00:00Z", etype="vessel"):
    return Observation(discipline="GEOINT", source="s", timestamp=ts, entity=entity,
                       entity_type=etype, lat=lat, lon=lon)


ZONE = geofence.Zone(name="Pier", lat=9.0, lon=-79.0, radius_km=3.0, kind="keep-out")


def test_inside_alert():
    alerts = geofence.evaluate([_o("X", 9.0, -79.0)], [ZONE])
    assert alerts and alerts[0]["status"] == "inside"


def test_proximity_alert():
    # ~3.5 km away (just outside 3km, within 1.5x)
    alerts = geofence.evaluate([_o("X", 9.0, -79.032)], [ZONE])
    assert alerts and alerts[0]["status"] == "proximity"


def test_far_no_alert():
    alerts = geofence.evaluate([_o("X", 40.0, -70.0)], [ZONE])
    assert alerts == []


def test_no_geo_no_alert():
    o = Observation(discipline="OSINT", source="s", timestamp="t", entity="X")
    assert geofence.evaluate([o], [ZONE]) == []


def test_keep_out_higher_severity_than_aoi():
    ko = geofence.Zone("KO", 9.0, -79.0, 3.0, kind="keep-out")
    aoi = geofence.Zone("AOI", 9.0, -79.0, 3.0, kind="area-of-interest")
    alerts = geofence.evaluate([_o("X", 9.0, -79.0)], [ko, aoi])
    # highest-severity first
    assert alerts[0]["zone_kind"] == "keep-out"


def test_watch_entity_types_filter():
    z = geofence.Zone("Air", 9.0, -79.0, 3.0, watch_entity_types=["aircraft"])
    assert geofence.evaluate([_o("Vessel", 9.0, -79.0, etype="vessel")], [z]) == []
    assert geofence.evaluate([_o("Jet", 9.0, -79.0, etype="aircraft")], [z])


def test_dwell_alert():
    obs = [_o("X", 9.0, -79.0, ts="2026-01-01T00:00:00Z"),
           _o("X", 9.001, -79.001, ts="2026-01-01T01:00:00Z"),
           _o("X", 9.0, -79.0, ts="2026-01-01T02:00:00Z")]
    dwell = geofence.dwell_alerts(obs, [ZONE], min_points=2)
    assert dwell and dwell[0]["count"] >= 2


def test_dwell_needs_min_points():
    obs = [_o("X", 9.0, -79.0)]
    assert geofence.dwell_alerts(obs, [ZONE], min_points=2) == []


def test_zone_roundtrip():
    z2 = geofence.Zone.from_dict(ZONE.to_dict())
    assert z2.name == ZONE.name and z2.radius_km == ZONE.radius_km


def test_load_zones():
    zones = geofence.load_zones([{"name": "Z", "lat": 1.0, "lon": 2.0, "radius_km": 5}])
    assert len(zones) == 1 and zones[0].name == "Z"


def test_alerts_sorted_by_severity():
    ko = geofence.Zone("KO", 9.0, -79.0, 3.0, kind="keep-out")
    aoi = geofence.Zone("AOI", 9.0, -79.0, 20.0, kind="area-of-interest")
    alerts = geofence.evaluate([_o("X", 9.0, -79.0)], [aoi, ko])
    sev = [a["severity"] for a in alerts]
    assert sev == sorted(sev, reverse=True)
