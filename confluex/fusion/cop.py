"""Common Operating Picture (COP) products.

  * timeline()        : merged, time-ordered event feed across all disciplines.
  * dossier()         : per-entity dossier (identity, provenance, corroboration,
                        contradictions, track summary, pattern-of-life, zone hits).
  * render_html()     : a SELF-CONTAINED HTML dashboard (inline CSS + a tiny
                        inline-SVG map, NO JS/CDN deps) showing the map, timeline,
                        and entity roster.

The COP is a decision-SUPPORT picture for understanding and force protection.
It presents what is known, how well it is corroborated, and what is unusual. It
contains no targeting, engagement, or fire-control content.
"""

from __future__ import annotations

import html


def timeline(result: dict) -> list:
    """Merged time-ordered event feed across disciplines."""
    events = []
    for o in result["observations"]:
        events.append({
            "timestamp": o.timestamp, "discipline": o.discipline, "source": o.source,
            "entity": o.entity, "entity_type": o.entity_type,
            "text": o.text, "obs": o.id,
            "geo": [o.lat, o.lon] if o.has_geo else None,
        })
    events.sort(key=lambda e: (e["timestamp"], e["obs"]))
    return events


def _index(result):
    obs_by_id = {o.id: o for o in result["observations"]}
    corr_by_ent = {c["entity_id"]: c for c in result["assessment"]["corroboration"]}
    track_by_ent = {t["entity_id"]: t for t in result["tracks"]}
    pol_by_ent = {p["entity_id"]: p for p in result["patterns_of_life"]}
    contra_by_ent = {}
    for c in result["assessment"]["contradictions"]:
        contra_by_ent.setdefault(c["entity_id"], []).append(c)
    anom_by_ent = {}
    for a in result["anomalies"]:
        anom_by_ent.setdefault(a["entity_id"], []).append(a)
    zone_by_ent = {}
    for z in result["zone_alerts"]:
        zone_by_ent.setdefault((z["entity"] or "").lower(), []).append(z)
    return (obs_by_id, corr_by_ent, track_by_ent, pol_by_ent,
            contra_by_ent, anom_by_ent, zone_by_ent)


def dossier(result: dict, entity_id: str) -> dict:
    ent = next((e for e in result["entities"] if e.id == entity_id), None)
    if ent is None:
        raise KeyError(f"no entity {entity_id!r} in result")
    (obs_by_id, corr, track, pol, contra, anom, zone_by_ent) = _index(result)
    obs = [obs_by_id[i].to_dict() for i in ent.observation_ids if i in obs_by_id]
    return {
        "entity": ent.to_dict(),
        "corroboration": corr.get(ent.id),
        "contradictions": contra.get(ent.id, []),
        "track": track.get(ent.id),
        "pattern_of_life": pol.get(ent.id),
        "anomalies": anom.get(ent.id, []),
        "zone_alerts": zone_by_ent.get(ent.canonical.lower(), []),
        "observations": obs,
        "provenance": {
            "disciplines": sorted(ent.disciplines),
            "sources": sorted(ent.sources),
            "observation_ids": list(ent.observation_ids),
        },
    }


def all_dossiers(result: dict) -> list:
    return [dossier(result, e.id) for e in result["entities"]]


def render_text(result: dict) -> str:
    """A compact terminal COP summary."""
    c = result["counts"]
    L = []
    L.append("=" * 72)
    L.append("  COGNIS VANGUARD  |  Common Operating Picture (situational awareness)")
    L.append("  Defensive fusion - understanding & force protection, not targeting")
    L.append("=" * 72)
    L.append(f"Scenario : {result['name']}")
    L.append(f"Fused    : {c['observations']} observations, {c['entities']} entities, "
             f"{c['disciplines']} INT disciplines, {c['sources']} sources")
    L.append(f"Analytics: {c['tracks']} tracks, {c['anomalies']} anomalies, "
             f"{c['contradictions']} contradictions, {c['deconfliction_flags']} deconfliction flags")
    if result["zones"]:
        L.append(f"Zones    : {len(result['zones'])} defined, {c['zone_alerts']} alerts, "
                 f"{len(result['dwell_alerts'])} dwell")
    L.append("")
    L.append("Top entities by corroboration:")
    for s in result["assessment"]["corroboration"][:8]:
        L.append(f"   [{s['band']:>13}] {s['canonical']:<24} "
                 f"score={s['score']:.2f}  int={','.join(s['disciplines'])}")
    if result["assessment"]["contradictions"]:
        L.append("")
        L.append("Contradictions (analyst review):")
        for x in result["assessment"]["contradictions"][:6]:
            L.append(f"   - {x['kind']} on {x.get('entity_id','')}: {x['note']}")
    if result["zone_alerts"]:
        L.append("")
        L.append("Force-protection zone alerts:")
        for a in result["zone_alerts"][:6]:
            L.append(f"   - [{a['status']}] {a['entity']} vs {a['zone']} "
                     f"({a['zone_kind']}) {a['distance_km']}km")
    L.append("")
    L.append("NOTE: Decision-support only. Every item traces to cited observations.")
    return "\n".join(L)


# --------------------------------------------------------------------------- HTML
def _project(points, width, height, pad=28):
    """Equirectangular projection of (lat,lon) points into an SVG viewbox."""
    if not points:
        return [], (0, 0, 1, 1)
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    minlat, maxlat = min(lats), max(lats)
    minlon, maxlon = min(lons), max(lons)
    dlat = (maxlat - minlat) or 1.0
    dlon = (maxlon - minlon) or 1.0
    out = []
    for lat, lon, meta in [(p[0], p[1], p[2]) for p in points]:
        x = pad + (lon - minlon) / dlon * (width - 2 * pad)
        y = pad + (maxlat - lat) / dlat * (height - 2 * pad)
        out.append((round(x, 1), round(y, 1), meta))
    return out, (minlat, minlon, maxlat, maxlon)


_DISC_COLOR = {
    "OSINT": "#22d3ee", "SIGINT": "#a78bfa", "GEOINT": "#34d399",
    "HUMINT": "#fbbf24", "MASINT": "#f472b6", "IMINT": "#60a5fa",
    "STRUCTURED": "#cbd5e1",
}


def _svg_map(result, width=680, height=360):
    pts = []
    for o in result["observations"]:
        if o.has_geo:
            pts.append((o.lat, o.lon, o))
    zpts = [(z["lat"], z["lon"], z) for z in result["zones"]]
    proj, _bbox = _project([(p[0], p[1], p[2]) for p in pts + zpts], width, height)
    n_obs = len(pts)
    parts = [f'<svg viewBox="0 0 {width} {height}" width="100%" '
             f'preserveAspectRatio="xMidYMid meet" role="img" '
             f'aria-label="fused geospatial picture">']
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#0b1020"/>')
    # grid
    for gx in range(0, width, 68):
        parts.append(f'<line x1="{gx}" y1="0" x2="{gx}" y2="{height}" stroke="#16213e" stroke-width="1"/>')
    for gy in range(0, height, 60):
        parts.append(f'<line x1="0" y1="{gy}" x2="{width}" y2="{gy}" stroke="#16213e" stroke-width="1"/>')
    # zones (drawn as circles scaled by relative radius)
    for i, (x, y, meta) in enumerate(proj[n_obs:]):
        r = 20 + 8 * min(meta["radius_km"], 12)
        col = {"keep-out": "#ef4444", "restricted": "#f59e0b"}.get(meta["kind"], "#38bdf8")
        parts.append(f'<circle cx="{x}" cy="{y}" r="{r:.0f}" fill="none" '
                     f'stroke="{col}" stroke-width="1.5" stroke-dasharray="4 3" opacity="0.8"/>')
        parts.append(f'<text x="{x+4}" y="{y-6}" fill="{col}" font-size="10">'
                     f'{html.escape(meta["name"])}</text>')
    # observation markers
    for (x, y, o) in proj[:n_obs]:
        col = _DISC_COLOR.get(o.discipline, "#e2e8f0")
        parts.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{col}">'
                     f'<title>{html.escape(o.discipline)}: {html.escape(o.entity or o.text[:40])}</title></circle>')
    parts.append('</svg>')
    return "".join(parts)


def render_html(result: dict, title: str | None = None) -> str:
    """Self-contained COP dashboard: inline CSS, inline-SVG map, no JS/CDN."""
    title = title or f"COP — {result['name']}"
    tl = timeline(result)
    corr = {c["entity_id"]: c for c in result["assessment"]["corroboration"]}
    e = html.escape
    rows = []
    for ent in result["entities"]:
        c = corr.get(ent.id, {})
        band = c.get("band", "single-source")
        rows.append(
            f'<tr><td>{e(ent.canonical)}</td><td>{e(ent.etype)}</td>'
            f'<td>{e(", ".join(sorted(ent.disciplines)))}</td>'
            f'<td><span class="band {band}">{band}</span> {c.get("score", 0):.2f}</td>'
            f'<td>{len(ent.observation_ids)}</td></tr>')
    tl_rows = []
    for ev in tl:
        col = _DISC_COLOR.get(ev["discipline"], "#e2e8f0")
        tl_rows.append(
            f'<li><span class="disc" style="background:{col}">{e(ev["discipline"])}</span>'
            f'<span class="ts">{e(ev["timestamp"])}</span> '
            f'<b>{e(ev["entity"] or "-")}</b> — {e(ev["text"][:120])}</li>')
    alerts = "".join(
        f'<li class="alert {e(a["status"])}">[{e(a["status"]).upper()}] '
        f'{e(a["entity"])} vs <b>{e(a["zone"])}</b> ({e(a["zone_kind"])}) '
        f'{a["distance_km"]} km</li>' for a in result["zone_alerts"][:20]) or "<li>none</li>"
    contra = "".join(
        f'<li>{e(x["kind"])}: {e(x.get("note",""))}</li>'
        for x in result["assessment"]["contradictions"][:20]) or "<li>none</li>"
    c = result["counts"]
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<style>
:root{{--bg:#0b1020;--panel:#111a33;--ink:#e2e8f0;--mut:#94a3b8;--line:#1e2a4a;}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.5 system-ui,Segoe UI,Roboto,sans-serif}}
header{{padding:16px 20px;background:linear-gradient(90deg,#1e1b4b,#0b1020);border-bottom:1px solid var(--line)}}
h1{{margin:0;font-size:18px}} .sub{{color:var(--mut);font-size:12px;margin-top:4px}}
.wrap{{max-width:1100px;margin:0 auto;padding:16px;display:grid;gap:16px}}
.grid{{display:grid;grid-template-columns:1fr;gap:16px}}
@media(min-width:820px){{.grid{{grid-template-columns:1.4fr 1fr}}}}
.card{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px;overflow:auto}}
.card h2{{margin:0 0 10px;font-size:14px;color:#c7d2fe;text-transform:uppercase;letter-spacing:.06em}}
.kpis{{display:flex;flex-wrap:wrap;gap:10px}}
.kpi{{background:#0e1730;border:1px solid var(--line);border-radius:8px;padding:8px 12px;min-width:96px}}
.kpi b{{display:block;font-size:20px}} .kpi span{{color:var(--mut);font-size:11px}}
table{{width:100%;border-collapse:collapse;font-size:13px}} th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line)}}
th{{color:var(--mut);font-weight:600}}
ul{{list-style:none;margin:0;padding:0}} li{{padding:6px 4px;border-bottom:1px solid var(--line);font-size:13px}}
.disc{{display:inline-block;color:#0b1020;font-weight:700;font-size:10px;padding:1px 6px;border-radius:6px;margin-right:6px}}
.ts{{color:var(--mut);font-size:11px;margin-right:6px}}
.band{{padding:1px 6px;border-radius:6px;font-size:11px;font-weight:700;color:#0b1020}}
.band.strong{{background:#34d399}} .band.moderate{{background:#fbbf24}}
.band.weak{{background:#fb923c}} .band.single-source{{background:#94a3b8}}
.alert.inside{{color:#fca5a5}} .alert.proximity{{color:#fcd34d}}
.foot{{color:var(--mut);font-size:11px;text-align:center;padding:12px}}
.tag{{display:inline-block;background:#312e81;color:#c7d2fe;font-size:10px;padding:2px 8px;border-radius:99px}}
</style></head><body>
<header><h1>🟣 {e(title)}</h1>
<div class="sub">Confluex — multi-INT fusion Common Operating Picture ·
<span class="tag">DEFENSIVE · situational awareness &amp; force protection · not targeting</span></div></header>
<div class="wrap">
<div class="card kpis">
<div class="kpi"><b>{c['observations']}</b><span>observations</span></div>
<div class="kpi"><b>{c['entities']}</b><span>entities</span></div>
<div class="kpi"><b>{c['disciplines']}</b><span>INT disciplines</span></div>
<div class="kpi"><b>{c['sources']}</b><span>sources</span></div>
<div class="kpi"><b>{c['tracks']}</b><span>tracks</span></div>
<div class="kpi"><b>{c['anomalies']}</b><span>anomalies</span></div>
<div class="kpi"><b>{c['contradictions']}</b><span>contradictions</span></div>
<div class="kpi"><b>{c['zone_alerts']}</b><span>zone alerts</span></div>
</div>
<div class="grid">
<div class="card"><h2>Fused geospatial picture</h2>{_svg_map(result)}</div>
<div class="card"><h2>Entities</h2>
<table><thead><tr><th>Entity</th><th>Type</th><th>INT</th><th>Corroboration</th><th>Obs</th></tr></thead>
<tbody>{''.join(rows) or '<tr><td colspan=5>none</td></tr>'}</tbody></table></div>
</div>
<div class="grid">
<div class="card"><h2>Fusion timeline</h2><ul>{''.join(tl_rows)}</ul></div>
<div>
<div class="card"><h2>Force-protection zone alerts</h2><ul>{alerts}</ul></div>
<div class="card" style="margin-top:16px"><h2>Contradictions</h2><ul>{contra}</ul></div>
</div>
</div>
<div class="foot">Generated offline by Confluex · every item traces to cited
observations · decision-support only, analyst corroboration required · © Cognis Digital LLC</div>
</div></body></html>"""
