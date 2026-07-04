"""Geofence / zone alerting for FORCE PROTECTION situational awareness.

Define named zones (circular keep-out / restricted / area-of-interest) and test
observations against them. Emits informational proximity and entry/dwell alerts
so a protected force understands what is near it.

FRAMING (non-negotiable): zones are PROTECTIVE. Typical use is a keep-out radius
around a friendly location, a coastal area-of-interest for maritime domain
awareness, or a restricted airspace. Alerts describe *presence and proximity*
for warning and understanding. There is NO targeting: nothing here nominates,
prioritizes, or engages anything. An alert is a prompt for an analyst to look.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .schema import haversine_km


@dataclass
class Zone:
    name: str
    lat: float
    lon: float
    radius_km: float
    kind: str = "area-of-interest"   # keep-out | restricted | area-of-interest
    note: str = ""
    watch_entity_types: list = field(default_factory=list)  # empty == all

    def to_dict(self) -> dict:
        return {"name": self.name, "lat": self.lat, "lon": self.lon,
                "radius_km": self.radius_km, "kind": self.kind, "note": self.note,
                "watch_entity_types": list(self.watch_entity_types)}

    @classmethod
    def from_dict(cls, d: dict) -> "Zone":
        return cls(name=d["name"], lat=float(d["lat"]), lon=float(d["lon"]),
                   radius_km=float(d.get("radius_km", 1.0)),
                   kind=d.get("kind", "area-of-interest"), note=d.get("note", ""),
                   watch_entity_types=list(d.get("watch_entity_types", [])))


# Severity ordering for protective warning (higher == warn sooner/louder).
_KIND_SEVERITY = {"keep-out": 3, "restricted": 2, "area-of-interest": 1}


def evaluate(observations, zones, proximity_factor: float = 1.5) -> list:
    """Return alerts for observations inside or near a zone.

    proximity_factor: an observation within radius*proximity_factor but outside
    the radius yields a 'proximity' alert; inside yields an 'inside' alert.
    Sorted by severity then time so the most protection-relevant surface first.
    """
    alerts = []
    for o in observations:
        if not o.has_geo:
            continue
        for z in zones:
            if z.watch_entity_types and o.entity_type not in z.watch_entity_types:
                continue
            d = haversine_km(o.lat, o.lon, z.lat, z.lon)
            if d <= z.radius_km:
                status = "inside"
            elif d <= z.radius_km * proximity_factor:
                status = "proximity"
            else:
                continue
            alerts.append({
                "zone": z.name, "zone_kind": z.kind,
                "status": status,
                "entity": o.entity or "(unattributed)",
                "entity_type": o.entity_type,
                "observation": o.id,
                "discipline": o.discipline,
                "timestamp": o.timestamp,
                "distance_km": round(d, 3),
                "range_of_radius": round(d / z.radius_km, 3) if z.radius_km else None,
                "severity": _KIND_SEVERITY.get(z.kind, 1) + (1 if status == "inside" else 0),
                "note": z.note,
            })
    alerts.sort(key=lambda a: (-a["severity"], a["timestamp"], a["zone"]))
    return alerts


def dwell_alerts(observations, zones, min_points: int = 2) -> list:
    """Flag entities with >= min_points observations inside the same zone —
    a loiter/dwell indication for force-protection awareness (not targeting)."""
    inside = {}
    for a in evaluate(observations, zones):
        if a["status"] == "inside":
            key = (a["zone"], a["entity"].lower())
            inside.setdefault(key, []).append(a)
    out = []
    for (zone, entity), hits in sorted(inside.items()):
        if len(hits) >= min_points:
            ts = sorted(h["timestamp"] for h in hits)
            out.append({
                "kind": "dwell", "zone": zone,
                "entity": hits[0]["entity"], "entity_type": hits[0]["entity_type"],
                "count": len(hits), "first_seen": ts[0], "last_seen": ts[-1],
                "observations": sorted(h["observation"] for h in hits),
                "note": "repeated presence inside zone (loiter indication)",
            })
    return out


def load_zones(records) -> list:
    return [Zone.from_dict(r) for r in records]
