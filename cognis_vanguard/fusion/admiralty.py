"""NATO Admiralty-style (a.k.a. NATO System) source-reliability x
information-credibility grading.

Source reliability : A (completely reliable) .. E (unreliable), F (cannot judge)
Info credibility   : 1 (confirmed) .. 5 (improbable), 6 (cannot judge)

We map each axis to a 0..1 numeric weight (higher == better) and combine them
into a single fused confidence. This is a well-known, doctrinally-familiar grading
scheme; the numeric mapping here is a transparent, documented heuristic — not an
official conversion — so downstream products can rank observations consistently.

Everything is for UNDERSTANDING/analytic weighting only.
"""

from __future__ import annotations

RELIABILITY = {
    "A": ("Completely reliable", 1.00),
    "B": ("Usually reliable", 0.80),
    "C": ("Fairly reliable", 0.60),
    "D": ("Not usually reliable", 0.40),
    "E": ("Unreliable", 0.20),
    "F": ("Reliability cannot be judged", 0.50),
}

CREDIBILITY = {
    "1": ("Confirmed by other sources", 1.00),
    "2": ("Probably true", 0.80),
    "3": ("Possibly true", 0.60),
    "4": ("Doubtful", 0.40),
    "5": ("Improbable", 0.20),
    "6": ("Truth cannot be judged", 0.50),
}


def reliability_weight(code: str) -> float:
    return RELIABILITY.get((code or "F").upper(), RELIABILITY["F"])[1]


def credibility_weight(code: str) -> float:
    return CREDIBILITY.get((code or "6"), CREDIBILITY["6"])[1]


def grade(code: str) -> dict:
    """Parse a 2-char Admiralty code like 'B2' into its components + weights."""
    code = (code or "").strip().upper()
    rel = code[0] if code and code[0] in RELIABILITY else "F"
    cred = code[1] if len(code) > 1 and code[1] in CREDIBILITY else "6"
    rw = reliability_weight(rel)
    cw = credibility_weight(cred)
    return {
        "code": rel + cred,
        "reliability": rel,
        "reliability_label": RELIABILITY[rel][0],
        "credibility": cred,
        "credibility_label": CREDIBILITY[cred][0],
        "reliability_weight": rw,
        "credibility_weight": cw,
        "confidence": round((rw * cw) ** 0.5, 4),  # geometric mean, 0..1
    }


def observation_confidence(obs) -> float:
    """Confidence in a single observation from its Admiralty codes.

    Falls back to a neutral 0.5 when an observation carries no grading, so
    ungraded feeds neither dominate nor are discarded.
    """
    if not obs.reliability and not obs.credibility:
        return 0.5
    return grade((obs.reliability or "F") + (obs.credibility or "6"))["confidence"]


def default_grade_for(discipline: str) -> str:
    """A conservative default Admiralty code by discipline when a feed does not
    provide one. Deliberately middling-to-cautious; documented, not doctrinal."""
    d = (discipline or "").upper()
    return {
        "OSINT": "C3",       # fairly reliable / possibly true
        "SIGINT": "B2",      # metadata externals tend to be dependable
        "GEOINT": "B2",
        "IMINT": "B2",
        "HUMINT": "C3",      # single-source human reporting: cautious
        "MASINT": "B2",      # instrumented measurement
        "STRUCTURED": "B2",
    }.get(d, "F6")
