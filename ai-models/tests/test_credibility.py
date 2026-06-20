"""Tests for the deterministic credibility scorer (Task 4.1)."""

from src.rag.credibility import (
    credibility_breakdown,
    credibility_score,
    is_credible,
    tier_of,
)


def test_tier_of_handles_strings_dicts_and_metadata():
    assert tier_of("Official") == "official"
    assert tier_of({"quality_tier": "curated"}) == "curated"
    assert tier_of({"metadata": {"quality_tier": "dev_fallback"}}) == "dev_fallback"
    assert tier_of({}) == "unknown"
    assert tier_of(42) == "unknown"


def test_is_credible_distinguishes_tiers():
    assert is_credible({"quality_tier": "official"}) is True
    assert is_credible({"quality_tier": "curated"}) is True
    assert is_credible({"quality_tier": "dev_fallback"}) is False
    assert is_credible({"quality_tier": "unknown"}) is False


def test_credibility_score_is_fraction_credible():
    docs = [
        {"quality_tier": "official"},
        {"quality_tier": "curated"},
        {"quality_tier": "dev_fallback"},
        {"quality_tier": "unknown"},
    ]
    assert credibility_score(docs) == 0.5


def test_credibility_score_empty_is_zero():
    assert credibility_score([]) == 0.0


def test_credibility_breakdown_reports_counts():
    docs = [
        {"metadata": {"quality_tier": "official"}},
        {"metadata": {"quality_tier": "official"}},
        {"metadata": {"quality_tier": "dev_fallback"}},
    ]
    breakdown = credibility_breakdown(docs)
    assert breakdown["total"] == 3
    assert breakdown["credible"] == 2
    assert abs(breakdown["score"] - (2 / 3)) < 1e-9
    assert breakdown["by_tier"]["official"] == 2
    assert breakdown["by_tier"]["dev_fallback"] == 1
