# Interoperability Export Profiles

`cognis_vanguard.fusion.interop` emits fused observations and resolved entities
in four formats. All exporters are deterministic and stdlib-only.

## JSON (`to_json`)

Full-fidelity: `{ "observations": [...], "entities": [...], "assessment": {...} }`.
The canonical loss-less export; every other format is a projection of this.

## CSV (`observations_to_csv`, `entities_to_csv`)

Flat tables for spreadsheets and quick triage.

Observation columns: `id, discipline, source, timestamp, entity, entity_type,
lat, lon, reliability, credibility, text`.

## STIX 2.1-like (`to_stix`, `to_stix_json`)

A STIX-**shaped** bundle. It follows STIX 2.1 conventions closely but is a
documented *profile*, not a certified-conformant producer — hence "STIX-like".

**Object model**

| STIX object | Represents | Notes |
|---|---|---|
| `identity` | the producing system | `identity_class: system` |
| `observed-data` | one `Observation` | one per observation; `number_observed: 1` |
| `x-cognis-entity` | one resolved entity | custom SCO (see below) |
| `relationship` | entity ⇽ observation | `relationship_type: derived-from` |

**Custom / non-standard fields (documented departures)**

- `x-cognis-entity` is a **custom object type** (`x-` prefixed per STIX custom
  rules) carrying `name`, `entity_type`, `aliases`, `x_cognis_disciplines`.
- `observed-data` here summarizes an observation rather than embedding a full
  `objects`/SCO refs map; discipline/source travel in `labels`
  (`discipline:GEOINT`, `source:sat-track`) and custom `x_cognis_*` properties
  (`x_cognis_text`, `x_cognis_geo`, `x_cognis_reliability`,
  `x_cognis_credibility`). A strict STIX consumer will ignore unknown `x_`
  properties safely.
- IDs are deterministic UUIDv5 (fixed namespace) so re-exporting identical input
  yields byte-identical bundles.
- Timestamps default to a fixed value when an observation lacks one, to keep the
  bundle deterministic.

## Symbol-agnostic entity schema (`to_symbol_agnostic`)

`schema: cognis-vanguard/symbol-agnostic-entity/1.0`

A deliberately **NATO-symbol-agnostic** entity record: it carries an
`entity_type` and a neutral `affiliation` hint
(`unknown`/`friend`/`neutral`/`suspect`/`pending`) but emits **no** military
symbology identification code — no MIL-STD-2525, no APP-6, no SIDC. This is by
design: the tool *describes* entities for understanding; it does not paint a
symbology/targeting overlay. A CI test asserts the emitted JSON contains none of
those code families.

`affiliation` defaults to `unknown` and only downgrades to `suspect` when the
reporting itself used a suspect/illicit label — it is descriptive context, never
a targeting designation.

## Determinism

Every exporter is a pure function of its input. `to_stix_json` and `to_json`
produce byte-identical output across runs for identical input, and this is gated
in `tests/test_fusion_interop.py`.
