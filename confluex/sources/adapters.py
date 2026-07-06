"""Adapters: raw feed bytes -> Vanguard reports [{id, timestamp, source, text}].

Pure functions of their input, tested against local fixtures with no network.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import xml.etree.ElementTree as ET

_URL_RE = re.compile(r'https?://[^\s,"]+')


def _text(content) -> str:
    return content.decode("utf-8", "replace") if isinstance(content, (bytes, bytearray)) else content


def _rid(source: str, key: str) -> str:
    return source + "-" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]


def _report(source, key, timestamp, text):
    return {"id": _rid(source, key), "timestamp": timestamp or "", "source": source,
            "text": " ".join((text or "").split())}


def gdelt(content, source="gdelt") -> list:
    try:
        data = json.loads(_text(content))
    except json.JSONDecodeError:
        return []
    out = []
    for a in data.get("articles", []):
        title = a.get("title") or ""
        dom = a.get("domain") or ""
        text = f"{title} ({dom})"
        out.append(_report(source, a.get("url", title), a.get("seendate"), text))
    return out


def reliefweb(content, source="reliefweb") -> list:
    try:
        data = json.loads(_text(content))
    except json.JSONDecodeError:
        return []
    out = []
    for item in data.get("data", []):
        f = item.get("fields", {})
        title = f.get("title") or ""
        date = (f.get("date") or {}).get("created")
        out.append(_report(source, str(item.get("id", title)), date, title))
    return out


def usgs(content, source="usgs") -> list:
    try:
        data = json.loads(_text(content))
    except json.JSONDecodeError:
        return []
    out = []
    for feat in data.get("features", []):
        p = feat.get("properties", {})
        title = p.get("title") or f"M{p.get('mag')} {p.get('place')}"
        out.append(_report(source, str(feat.get("id", title)), str(p.get("time", "")), title))
    return out


def rss(content, source="rss") -> list:
    out = []
    try:
        root = ET.fromstring(_text(content))
    except ET.ParseError:
        return out

    def local(t):
        return t.split("}")[-1]

    for el in root.iter():
        if local(el.tag) not in ("item", "entry"):
            continue
        title = desc = date = link = ""
        for ch in el:
            lt = local(ch.tag)
            if lt == "title":
                title = ch.text or ""
            elif lt in ("description", "summary", "content"):
                desc = ch.text or ""
            elif lt in ("pubDate", "published", "updated"):
                date = ch.text or ""
            elif lt == "link":
                link = ch.text or ch.attrib.get("href", "")
        desc = re.sub(r"<[^>]+>", " ", desc)
        out.append(_report(source, link or title, date, f"{title}. {desc}"))
    return out


def ioc_lines(content, source="ioc_lines", limit=100) -> list:
    """Turn an IOC blocklist (csv/txt) into short per-indicator reports.

    Extracts the first URL or IP *by pattern* (not by column position), so it is
    robust to header rows and differing CSV layouts (Feodo/URLhaus/ThreatFox)."""
    out = []
    for line in _text(content).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        m = _URL_RE.search(line)
        val = m.group(0) if m else None
        if not val:
            for tok in re.split(r'[,\s"]+', line):
                try:
                    ipaddress.ip_address(tok)
                    val = tok
                    break
                except ValueError:
                    continue
        if val:
            out.append(_report(source, val, "", f"Threat indicator {val} reported by {source}."))
        if len(out) >= limit:
            break
    return out
