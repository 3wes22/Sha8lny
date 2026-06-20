"""Tests for the faithfulness scorer scaffold (Task 4.1), with a mocked judge."""

import json

from scripts.eval_faithfulness import score_faithfulness


def _stub_judge(answer, passages):
    # Deterministic stub: "supported" iff any passage word appears in the answer.
    answer_l = answer.lower()
    return 1.0 if any(p.lower() in answer_l for p in passages) else 0.0


def test_score_faithfulness_on_three_item_sample(tmp_path):
    items = [
        {"answer": "Backend roles pay well", "passages": ["pay well"]},        # supported
        {"answer": "Use Docker multi-stage builds", "passages": ["multi-stage builds"]},  # supported
        {"answer": "Completely unrelated text", "passages": ["salary ranges"]},  # not supported
    ]
    result = score_faithfulness(items, _stub_judge, cache_dir=tmp_path)
    assert result["n"] == 3
    assert abs(result["faithfulness"] - (2 / 3)) < 1e-9


def test_score_faithfulness_caches_per_item(tmp_path):
    items = [{"answer": "x mentions y", "passages": ["y"]}]
    calls = {"n": 0}

    def counting_judge(answer, passages):
        calls["n"] += 1
        return _stub_judge(answer, passages)

    first = score_faithfulness(items, counting_judge, cache_dir=tmp_path)
    second = score_faithfulness(items, counting_judge, cache_dir=tmp_path)
    assert calls["n"] == 1  # second run served from disk cache
    assert first["per_item"][0]["cached"] is False
    assert second["per_item"][0]["cached"] is True
    # cache artifact written
    assert any(p.suffix == ".json" for p in tmp_path.iterdir())
    json.loads(next(tmp_path.glob("*.json")).read_text())
