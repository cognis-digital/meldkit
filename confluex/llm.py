"""Pluggable reasoning/summarization backends.

Default is a deterministic, offline provider (no model, fully testable) that
produces extractive, source-faithful summaries. An optional OllamaProvider uses
a locally-served open-weight model (self-hosted; no cloud egress) and is used
only when reachable — the platform never depends on it to function.
"""

from __future__ import annotations

import json
import re
import urllib.request


class Provider:
    def available(self) -> bool:
        return True

    def complete(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError


class DeterministicProvider(Provider):
    """Extractive summarizer: selects the sentences from the provided context
    most relevant to the prompt. Deterministic and offline."""

    def complete(self, prompt: str, context=None, max_sentences: int = 3, **kwargs) -> str:
        sents = []
        for c in (context or []):
            sents.extend(s.strip() for s in re.split(r"(?<=[.!?])\s+", c) if s.strip())
        q = set(re.findall(r"[a-z0-9]+", prompt.lower()))
        scored = []
        for idx, s in enumerate(sents):
            toks = set(re.findall(r"[a-z0-9]+", s.lower()))
            overlap = len(q & toks)
            if overlap:
                scored.append((overlap, -idx, s))
        scored.sort(key=lambda x: (-x[0], -x[1]))
        return " ".join(s for _, _, s in scored[:max_sentences])


class OllamaProvider(Provider):
    """Optional local open-weight backend via Ollama."""

    def __init__(self, model: str = "llama3", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host.rstrip("/")

    def available(self) -> bool:
        try:
            urllib.request.urlopen(self.host + "/api/tags", timeout=1)
            return True
        except Exception:
            return False

    def complete(self, prompt: str, context=None, timeout: int = 60, **kwargs) -> str:
        full = prompt
        if context:
            full = "Context:\n" + "\n".join(context) + "\n\nTask:\n" + prompt
        payload = json.dumps({"model": self.model, "prompt": full, "stream": False}).encode()
        req = urllib.request.Request(self.host + "/api/generate", data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode()).get("response", "")
