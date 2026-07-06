"""Confluex — multi-INT fusion analytics package.

Additive layer on top of the core extract/resolve/graph pipeline. Everything
here is DEFENSIVE situational-awareness and force-protection decision-support:
it fuses heterogeneous intelligence into a common, source-cited understanding.

It is explicitly NOT a targeting, fire-control, kill-chain, or strike-support
system. There are no capabilities here for selecting, engaging, or prosecuting
targets — only for understanding a picture and protecting a force.

Modules
-------
schema        : the common Observation record every INT source normalizes to.
adapters_int  : normalizers for OSINT / SIGINT-metadata / GEOINT / HUMINT /
                MASINT / structured reporting (synthetic sample data only).
admiralty     : NATO Admiralty-style source reliability x info credibility.
entities      : cross-source entity resolution + de-confliction.
corroborate   : corroboration scoring + contradiction detection across sources.
tracks        : track association, pattern-of-life, anomaly/change detection.
geofence      : zone / geofence force-protection alerting.
cop           : common operating picture (timeline, dossiers, HTML dashboard).
interop       : JSON / CSV / STIX-2.1-like / symbol-agnostic entity exports.
scenario      : load a scenario of observations and run the full fusion.
"""

from __future__ import annotations

__all__ = [
    "schema", "adapters_int", "admiralty", "entities", "corroborate",
    "tracks", "geofence", "cop", "interop", "scenario",
]
