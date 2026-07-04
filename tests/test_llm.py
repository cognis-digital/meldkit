from obsidia.llm import DeterministicProvider, OllamaProvider


def test_deterministic_provider_extracts_relevant_sentence():
    p = DeterministicProvider()
    ctx = ["The wallet addr-B1 was used by Marek Voss.", "Weather was clear that day."]
    out = p.complete("wallet addr-B1", context=ctx, max_sentences=1)
    assert "addr-B1" in out
    assert "Weather" not in out


def test_deterministic_provider_is_deterministic():
    p = DeterministicProvider()
    ctx = ["Alpha bravo charlie.", "Bravo charlie delta.", "Charlie delta echo."]
    assert p.complete("bravo charlie", context=ctx) == p.complete("bravo charlie", context=ctx)


def test_ollama_provider_degrades_gracefully_when_unavailable():
    # Should not raise on construction; availability is a safe boolean probe.
    p = OllamaProvider(host="http://127.0.0.1:9")
    assert p.available() is False
