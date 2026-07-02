"""CA-CFAR small/point-target detection (shared design with Cognis Vigil/Lookout).

Finds a 1-2 pixel target against a cluttered background — a swimmer, a small
craft, a person against terrain — by flagging pixels whose local contrast exceeds
k sigma over a ring of training cells. Pure stdlib. Non-kinetic search leads.
"""

from __future__ import annotations

import statistics


def ca_cfar(image, guard: int = 1, train: int = 4, k: float = 5.0) -> list:
    H = len(image)
    W = len(image[0]) if H else 0
    hits = []
    span = guard + train
    for r in range(H):
        for c in range(W):
            vals = []
            for dr in range(-span, span + 1):
                for dc in range(-span, span + 1):
                    if abs(dr) <= guard and abs(dc) <= guard:
                        continue
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < H and 0 <= cc < W:
                        vals.append(image[rr][cc])
            if len(vals) < 8:
                continue
            mean = sum(vals) / len(vals)
            std = statistics.pstdev(vals)
            if std > 0 and (image[r][c] - mean) / std >= k:
                hits.append((r, c, (image[r][c] - mean) / std))
    return hits


def detect_small_targets(image, k: float = 5.0, guard: int = 1, train: int = 4,
                         max_size: int = 8) -> list:
    snr_at = {(r, c): s for r, c, s in ca_cfar(image, guard, train, k)}
    seen, blobs = set(), []
    for start in snr_at:
        if start in seen:
            continue
        stack, comp = [start], []
        while stack:
            p = stack.pop()
            if p in seen or p not in snr_at:
                continue
            seen.add(p)
            comp.append(p)
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    q = (p[0] + dr, p[1] + dc)
                    if q in snr_at and q not in seen:
                        stack.append(q)
        if len(comp) > max_size:
            continue
        rows = [p[0] for p in comp]
        cols = [p[1] for p in comp]
        peak = max(snr_at[p] for p in comp)
        blobs.append({"row": round(sum(rows) / len(rows), 2),
                      "col": round(sum(cols) / len(cols), 2),
                      "size": len(comp), "peak_snr": round(peak, 2),
                      "confidence": round(min(0.99, (peak / (k * 2)) *
                                              (1.0 / (1 + 0.15 * (len(comp) - 1)))), 4)})
    blobs.sort(key=lambda b: -b["confidence"])
    return blobs


def demo_scene(seed: int = 42, H: int = 56, W: int = 56, n: int = 4,
               clutter: float = 0.05, amp: float = 0.45):
    import random as _r
    rng = _r.Random(seed)
    img = [[max(0.0, rng.gauss(0.2, clutter)) for _ in range(W)] for _ in range(H)]
    truth = set()
    for _ in range(n):
        r, c = rng.randint(5, H - 6), rng.randint(5, W - 6)
        img[r][c] += amp
        truth.add((r, c))
    return img, truth
