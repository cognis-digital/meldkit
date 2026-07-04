"""The common Observation schema every INT source normalizes to.

A single, flat, JSON-serializable record so that OSINT text, SIGINT-style
metadata, GEOINT tracks, HUMINT reports, MASINT sensor events, and structured
reporting all become comparable objects the fusion layer can reason over.

Deterministic IDs (BLAKE2b over the identifying fields) so the same input
always produces the same observation id — a hard requirement for reproducible,
auditable intelligence products.

DEFENSIVE SCOPE: an Observation describes *what was observed and how well we
trust it*, for situational awareness and force protection. It carries no
targeting, engagement, or fire-control fields by design.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field, asdict

# The recognized INT disciplines (normalized, lowercased).
INT_DISCIPLINES = (
    "OSINT",     # open-source text / news / social
    "SIGINT",    # signals METADATA ONLY (no content) — emitter/link/comms externals
    "GEOINT",    # geospatial / imagery-derived location tracks
    "HUMINT",    # human reporting (source statements)
    "MASINT",    # measurement & signature sensor events (acoustic/seismic/EO/IR/RF)
    "IMINT",     # imagery-derived observation (subset of GEOINT, kept distinct)
    "STRUCTURED",  # already-structured feeds / logs / registries
)


def _round(x):
    if x is None:
        return None
    return round(float(x), 6)


@dataclass
class Observation:
    """One normalized observation from any INT source.

    Required-ish fields:
      discipline : one of INT_DISCIPLINES
      source     : short source/sensor/feed identifier
      timestamp  : ISO-8601 string (UTC recommended)
      text       : free-text summary (may be empty for pure-metadata obs)

    Optional situational fields:
      entity     : the entity this observation is about (name/callsign/id)
      entity_type: coarse type (person/vessel/vehicle/org/emitter/facility/...)
      lat, lon   : location if geolocated (decimal degrees)
      attributes : arbitrary discipline-specific key/values (no content payloads)
      reliability: Admiralty source-reliability code A..F (optional)
      credibility: Admiralty info-credibility code 1..6 (optional)
    """

    discipline: str
    source: str
    timestamp: str
    text: str = ""
    entity: str = ""
    entity_type: str = ""
    lat: float | None = None
    lon: float | None = None
    attributes: dict = field(default_factory=dict)
    reliability: str = ""     # A..F
    credibility: str = ""     # 1..6
    id: str = ""

    def __post_init__(self):
        self.discipline = (self.discipline or "").upper()
        self.lat = _round(self.lat)
        self.lon = _round(self.lon)
        if not self.id:
            self.id = self.make_id()

    def make_id(self) -> str:
        key = "|".join([
            self.discipline, self.source, self.timestamp,
            self.entity, self.entity_type,
            "" if self.lat is None else f"{self.lat:.6f}",
            "" if self.lon is None else f"{self.lon:.6f}",
            self.text,
        ])
        h = hashlib.blake2b(key.encode("utf-8"), digest_size=8).hexdigest()
        return f"obs--{h}"

    @property
    def has_geo(self) -> bool:
        return self.lat is not None and self.lon is not None

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    def to_report(self) -> dict:
        """Down-project to the core-pipeline report schema so an Observation can
        flow into extract/resolve/graph/index unchanged."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "source": f"{self.discipline}:{self.source}",
            "text": self.text or (f"{self.entity_type} {self.entity}".strip()),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Observation":
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in d.items() if k in known})


def validate(obs: Observation) -> list:
    """Return a list of human-readable validation problems (empty == valid)."""
    problems = []
    if obs.discipline not in INT_DISCIPLINES:
        problems.append(f"unknown discipline {obs.discipline!r}")
    if not obs.source:
        problems.append("missing source")
    if not obs.timestamp:
        problems.append("missing timestamp")
    if obs.lat is not None and not (-90.0 <= obs.lat <= 90.0):
        problems.append(f"lat out of range: {obs.lat}")
    if obs.lon is not None and not (-180.0 <= obs.lon <= 180.0):
        problems.append(f"lon out of range: {obs.lon}")
    if obs.reliability and obs.reliability not in "ABCDEF":
        problems.append(f"bad reliability code {obs.reliability!r}")
    if obs.credibility and obs.credibility not in "123456":
        problems.append(f"bad credibility code {obs.credibility!r}")
    return problems


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Great-circle distance in km between two decimal-degree points."""
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def observations_to_reports(observations) -> list:
    """Convenience: down-project many Observations to core reports."""
    return [o.to_report() for o in observations]
