"""TF-IDF retrieval over reports (stdlib only, no external ML deps).

Deterministic vector-space retrieval so the platform runs offline and returns
source-cited passages without any model download.
"""

from __future__ import annotations

import math
import re
from collections import Counter

_TOKEN = re.compile(r"[a-z0-9][a-z0-9._-]*")


def tokenize(text: str) -> list:
    return _TOKEN.findall(text.lower())


class TfidfIndex:
    def __init__(self, reports: list):
        self.reports = reports
        self.docs = [tokenize(r.get("text", "")) for r in reports]
        self.N = len(self.docs)
        self.df: Counter = Counter()
        for toks in self.docs:
            for t in set(toks):
                self.df[t] += 1
        self.vectors = [self._vec(toks) for toks in self.docs]

    def _idf(self, term: str) -> float:
        return math.log((1 + self.N) / (1 + self.df.get(term, 0))) + 1.0

    def _vec(self, toks: list) -> dict:
        tf = Counter(toks)
        total = sum(tf.values()) or 1
        return {t: (c / total) * self._idf(t) for t, c in tf.items()}

    @staticmethod
    def _cosine(a: dict, b: dict) -> float:
        if not a or not b:
            return 0.0
        common = set(a) & set(b)
        dot = sum(a[t] * b[t] for t in common)
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        return dot / (na * nb) if na and nb else 0.0

    def search(self, query: str, k: int = 5) -> list:
        qv = self._vec(tokenize(query))
        scored = []
        for i, dv in enumerate(self.vectors):
            s = self._cosine(qv, dv)
            if s > 0:
                scored.append((s, i))
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [{"report_id": self.reports[i]["id"], "score": round(s, 4),
                 "text": self.reports[i].get("text", "")} for s, i in scored[:k]]
