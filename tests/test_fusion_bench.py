"""Gate the multi-INT fusion verification claims in RESULTS.md."""

from bench import fusion_evaluate


def test_entity_resolution_perfect():
    assert fusion_evaluate.evaluate()["entity_resolution_accuracy"] == 1.0


def test_cross_source_fusion_correct():
    assert fusion_evaluate.evaluate()["cross_source_fusion_correct"] is True


def test_force_protection_recall():
    assert fusion_evaluate.evaluate()["force_protection_recall"] == 1.0


def test_corroboration_band_accuracy():
    assert fusion_evaluate.evaluate()["corroboration_band_accuracy"] == 1.0


def test_contradiction_precision_clean():
    assert fusion_evaluate.evaluate()["contradiction_precision_ok"] is True


def test_multi_int_breadth():
    r = fusion_evaluate.evaluate()
    assert r["disciplines_fused"] >= r["min_disciplines_expected"]


def test_benchmark_shape():
    rows = fusion_evaluate.benchmark(sizes=(200,))
    assert rows and rows[0]["observations_per_s"] > 0
