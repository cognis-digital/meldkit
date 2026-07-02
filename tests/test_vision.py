from cognis_vanguard import smalltarget
from cognis_vanguard.vision import (
    DeterministicVisionProvider, OllamaVisionProvider, analyze_media,
)


def test_deterministic_provider_finds_planted_targets():
    img, truth = smalltarget.demo_scene()
    out = DeterministicVisionProvider().analyze(img, k=5.0)
    assert len(out["targets"]) >= len(truth) - 1  # recovers planted point targets
    assert "target" in out["text"].lower()


def test_blank_frame_reads_clear():
    import random
    rng = random.Random(1)
    blank = [[max(0.0, rng.gauss(0.2, 0.05)) for _ in range(40)] for _ in range(40)]
    out = DeterministicVisionProvider().analyze(blank, k=6.0)
    assert out["targets"] == [] or len(out["targets"]) <= 1


def test_analyze_media_returns_report():
    img, _ = smalltarget.demo_scene()
    rep = analyze_media(img, ts="2026-07-02T00:00:00Z")
    assert set(rep) >= {"id", "timestamp", "source", "text", "targets"}
    assert rep["id"].startswith("media-")


def test_ollama_vision_graceful_when_unavailable():
    assert OllamaVisionProvider(host="http://127.0.0.1:9").available() is False
