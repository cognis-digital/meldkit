# Multi-INT Fusion Layer

The `cognis_vanguard.fusion` package turns heterogeneous intelligence reporting
into one source-cited, corroboration-graded **Common Operating Picture (COP)**
for situational awareness and force protection.

> **Scope, non-negotiable.** This layer is for *understanding* and *force
> protection* only. It fuses intelligence so an analyst and a protected force
> can comprehend their environment. It performs **no** targeting, target
> nomination, prioritization for engagement, fire-control, kill-chain, or strike
> support. Anomalies, zone alerts, and contradictions are informational prompts
> for an analyst — never cues to act, and never engagement recommendations. All
> bundled data is synthetic.

## Pipeline

```
 INT sources (synthetic)                 common schema         fusion analytics
 ┌───────────────────────┐   adapters   ┌──────────────┐   ┌────────────────────┐
 │ OSINT  SIGINT-meta     │ ───────────▶ │ Observation  │ ─▶│ entity resolution   │
 │ GEOINT HUMINT          │              │  (normalized)│   │ + de-confliction    │
 │ MASINT STRUCTURED      │              └──────────────┘   │ corroboration/contra│
 └───────────────────────┘                                 │ tracks / PoL / anom │
                                                            │ geofence alerting   │
                                                            └─────────┬──────────┘
                                                                      ▼
                                                     COP: timeline + dossiers + HTML
                                                     interop: JSON/CSV/STIX/symbols
```

## The common Observation schema (`schema.py`)

Every source normalizes to one flat, JSON-serializable `Observation`:

| Field | Meaning |
|---|---|
| `discipline` | `OSINT` / `SIGINT` / `GEOINT` / `HUMINT` / `MASINT` / `IMINT` / `STRUCTURED` |
| `source` | short source/sensor/feed id |
| `timestamp` | ISO-8601 (UTC recommended) |
| `text` | free-text summary (may be empty for pure-metadata obs) |
| `entity`, `entity_type` | the thing observed (name/callsign/id) and coarse type |
| `lat`, `lon` | location, if geolocated (decimal degrees) |
| `attributes` | discipline-specific externals (no content payloads) |
| `reliability`, `credibility` | Admiralty codes (`A`..`F`, `1`..`6`) |

IDs are a deterministic BLAKE2b hash of the identifying fields — the same input
always yields the same `obs--…` id. An `Observation` can down-project to the
core report schema (`.to_report()`) so it flows through the existing
extract/resolve/graph/index pipeline unchanged.

**SIGINT is metadata-only.** The SIGINT adapter parses emitter externals
(emitter id, link, bearing, band, time) and explicitly **drops** any `content`
field it is handed. There is no communications-content ingestion anywhere.

## Source grading (`admiralty.py`)

NATO Admiralty-style grading: source **reliability** (`A`..`F`) × information
**credibility** (`1`..`6`), each mapped to a documented 0–1 weight and combined
by geometric mean into a per-observation confidence. Ungraded feeds get a
neutral 0.5 so they neither dominate nor are discarded. The numeric mapping is a
transparent heuristic, not an official conversion.

## Fusion analytics

- **Entity resolution & de-confliction** (`entities.py`) — merges observations
  of the same entity across disciplines using (1) shared identifiers
  (`imo`/`mmsi`/`emitter_id`/`track_id`/…), (2) alias/substring name match, and
  (3) token-set name similarity. De-confliction *surfaces* ambiguity (same name
  across types; one identifier claimed by multiple entities) for analyst review
  — it never auto-decides identity.
- **Corroboration & contradiction** (`corroborate.py`) — a corroboration score
  and band (`strong`/`moderate`/`weak`/`single-source`) from the breadth of
  independent support (distinct disciplines, distinct sources, Admiralty
  confidence, spatio-temporal agreement); contradiction detection flags
  implausible movement between consecutive fixes and mutually-exclusive
  attribute assertions.
- **Track & pattern analytics** (`tracks.py`) — track association from
  geolocated sightings; pattern-of-life (active hours, dwell-area clustering);
  outlier-resistant (median/MAD) anomaly detection for speed, off-pattern hour,
  and off-pattern location; and snapshot-to-snapshot change detection.
- **Geofence / zone alerting** (`geofence.py`) — protective keep-out /
  restricted / area-of-interest zones with inside/proximity alerts, severity
  ordering, and dwell (loiter) indications, framed strictly for force
  protection.

## Common Operating Picture (`cop.py`)

- `timeline(result)` — merged, time-ordered cross-discipline event feed.
- `dossier(result, entity_id)` / `all_dossiers(result)` — per-entity dossier
  (identity, provenance, corroboration, contradictions, track, pattern-of-life,
  zone hits, cited observations).
- `render_text(result)` — terminal COP summary.
- `render_html(result)` — a **self-contained** HTML dashboard (inline CSS +
  inline-SVG map, **no JS, no CDN, no external requests**) suitable for an
  air-gapped enclave.

## Running it

```bash
# Ingest a scenario and print the COP; optionally write the HTML dashboard.
cognis-vanguard fuse --scenario data/scenario_maritime.json --html cop.html

# Per-entity dossiers (all, or filtered by name/id).
cognis-vanguard dossier --entity Nightjar

# Interop exports.
cognis-vanguard export --format stix    > out.stix.json
cognis-vanguard export --format csv     > observations.csv
cognis-vanguard export --format symbols > entities.symbols.json

# One-shot demo on the bundled maritime scenario.
cognis-vanguard demo-fusion
```

Or from Python:

```python
from cognis_vanguard.fusion import scenario, cop, interop
res = scenario.run_scenario(scenario.load_scenario("data/scenario_maritime.json"))
print(cop.render_text(res))
open("cop.html", "w", encoding="utf-8").write(cop.render_html(res))
bundle = interop.to_stix(res["observations"], res["entities"])
```

See [`examples/`](../examples) for eight runnable demos (all exit 0) and
[`INTEROP.md`](INTEROP.md) for the export profiles.

## Honest limitations

- Resolution/corroboration/anomaly logic is deterministic heuristics, tuned and
  measured on synthetic scenarios (`bench/fusion_evaluate.py`, gated in CI). On
  real, noisy, adversarial data these are analyst *aids*, not adjudicators.
- Name similarity is token-set based (no transliteration/phonetic matching).
- Anomaly thresholds (speed sigma, dwell radius) are defaults; real deployments
  should tune them per operating area.
- Confidence weights are a documented heuristic, not doctrine.
