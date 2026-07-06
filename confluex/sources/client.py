"""HTTP client with on-disk cache and offline mode (shared design with the
Cognis Lattice sources client)."""

from __future__ import annotations

import hashlib
import os
import urllib.request

USER_AGENT = "confluex/0.2 (+https://cognis.digital)"


class HttpClient:
    def __init__(self, cache_dir=None, offline: bool = False, timeout: int = 30):
        self.cache_dir = cache_dir
        self.offline = offline
        self.timeout = timeout
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)

    def _cache_path(self, url: str):
        if not self.cache_dir:
            return None
        h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
        return os.path.join(self.cache_dir, h + ".cache")

    def get(self, url: str) -> bytes:
        cp = self._cache_path(url)
        if self.offline:
            if cp and os.path.exists(cp):
                with open(cp, "rb") as f:
                    return f.read()
            raise RuntimeError(f"offline: no cached copy for {url}")
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            data = r.read()
        if cp:
            with open(cp, "wb") as f:
                f.write(data)
        return data
