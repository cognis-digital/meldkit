"""Captured-media (photo/video) exploitation with a pluggable vision backend.

The default provider is deterministic and offline: it runs CA-CFAR small-target
detection over an intensity grid and returns detected targets plus a source-faithful
text description — so captured-media analysis is testable with no model. An optional
OllamaVisionProvider calls a locally-served multimodal model (e.g. llava) and is
used only when reachable; the platform never depends on it.

`analyze_media` turns a frame into a Vanguard report that flows into the graph.
"""

from __future__ import annotations

import hashlib
import json
import urllib.request

from .smalltarget import detect_small_targets


class VisionProvider:
    def available(self) -> bool:
        return True

    def analyze(self, image, **kwargs) -> dict:
        raise NotImplementedError


class DeterministicVisionProvider(VisionProvider):
    """Offline small-target detector over an intensity grid (rows x cols)."""

    def analyze(self, image, k: float = 5.0, **kwargs) -> dict:
        blobs = detect_small_targets(image, k=k)
        if not blobs:
            text = "No small high-contrast targets detected in frame."
        else:
            pts = ", ".join(f"({b['row']},{b['col']})" for b in blobs[:5])
            text = (f"{len(blobs)} small high-contrast target(s) detected at {pts}; "
                    f"consistent with a small object or person against background "
                    f"(peak SNR {blobs[0]['peak_snr']}).")
        return {"targets": blobs, "text": text}


class OllamaVisionProvider(VisionProvider):
    """Optional local multimodal backend (Ollama, e.g. llava). Takes a base64 image."""

    def __init__(self, model: str = "llava", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host.rstrip("/")

    def available(self) -> bool:
        try:
            urllib.request.urlopen(self.host + "/api/tags", timeout=1)
            return True
        except Exception:
            return False

    def analyze(self, image_b64, prompt="Describe any people, vessels, or objects.",
                timeout: int = 90, **kwargs) -> dict:
        payload = json.dumps({"model": self.model, "prompt": prompt,
                              "images": [image_b64], "stream": False}).encode()
        req = urllib.request.Request(self.host + "/api/generate", data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"targets": [], "text": json.loads(r.read().decode()).get("response", "")}


def analyze_media(image, provider: VisionProvider = None, source="captured-media",
                  ts="", **kw) -> dict:
    """Analyze a captured-media frame -> a Vanguard report dict."""
    provider = provider or DeterministicVisionProvider()
    result = provider.analyze(image, **kw)
    rid = "media-" + hashlib.sha1(str(result["text"]).encode("utf-8")).hexdigest()[:10]
    return {"id": rid, "timestamp": ts, "source": source, "text": result["text"],
            "targets": result.get("targets", [])}
