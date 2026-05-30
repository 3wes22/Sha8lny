from unittest.mock import patch

import pytest

from apps.core.health_checks import (
    check_gemini_live,
    get_ai_runtime_health,
    reset_gemini_probe_cache,
)


@pytest.mark.django_db
def test_get_ai_runtime_health_gemini_shape():
    reset_gemini_probe_cache()
    with patch("apps.core.health_checks.check_gemini_live") as mock_probe:
        mock_probe.return_value = {
            "reachable": True,
            "model": "gemini-2.5-flash-lite",
            "latency_ms": 120,
            "error": None,
        }
        with patch("apps.core.health_checks.AI_PROVIDER", "gemini"):
            with patch("apps.core.health_checks.GEMINI_API_KEY", "test-key"):
                health = get_ai_runtime_health()

    assert health["runtime"] == "gemini"
    assert health["provider_reachable"] is True
    assert health["gemini_live"]["reachable"] is True


def test_check_gemini_live_without_api_key():
    reset_gemini_probe_cache()
    with patch("apps.core.health_checks.GEMINI_API_KEY", ""):
        result = check_gemini_live()

    assert result["reachable"] is False
    assert "GEMINI_API_KEY" in (result["error"] or "")
