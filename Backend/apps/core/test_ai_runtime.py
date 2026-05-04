import pytest


@pytest.mark.django_db
def test_gemma_client_generate_text_routes_career_matching_to_gemini_flash():
    from apps.core.gemma_client import GemmaClient

    client = GemmaClient(
        provider="gemini",
        timeout_seconds=5,
        retry_count=0,
        task_type="career_matching",
    )

    client._post_generate = lambda payload: {  # type: ignore[method-assign]
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": "Career advice goes here.",
                        }
                    ]
                }
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 12,
            "candidatesTokenCount": 18,
        },
    }

    result = client.generate_text(
        prompt="Help me plan my backend learning path.",
        system="You are a career advisor.",
    )

    assert result.text == "Career advice goes here."
    assert result.payload is None
    assert result.metadata.source == "llm"
    assert result.metadata.model == "gemini-2.5-flash"
    assert result.metadata.provider == "gemini"
    assert result.prompt_tokens == 12
    assert result.completion_tokens == 18


@pytest.mark.django_db
def test_gemma_client_generate_structured_repairs_invalid_json_once():
    from apps.core.gemma_client import GemmaClient

    responses = iter(
        [
            {
                "candidates": [{"content": {"parts": [{"text": "This is not valid JSON."}]}}],
                "usageMetadata": {"promptTokenCount": 4, "candidatesTokenCount": 6},
            },
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": '{"questions": [{"id": 1, "question": "What is your target role?"}]}',
                                }
                            ]
                        }
                    }
                ],
                "usageMetadata": {"promptTokenCount": 7, "candidatesTokenCount": 9},
            },
        ]
    )

    client = GemmaClient(
        provider="gemini",
        timeout_seconds=5,
        retry_count=0,
        task_type="assessment_question_generation",
    )
    prompts: list[str] = []

    def fake_post_generate(payload):
        prompts.append(payload["prompt"])
        return next(responses)

    client._post_generate = fake_post_generate  # type: ignore[method-assign]

    result = client.generate_structured(
        prompt="Generate one assessment question.",
        system="Return JSON only.",
        required_keys=("questions",),
    )

    assert result.text.startswith('{"questions"')
    assert result.payload == {
        "questions": [{"id": 1, "question": "What is your target role?"}]
    }
    assert result.metadata.model == "gemini-2.5-flash-lite"
    assert len(prompts) == 2
    assert "Repair the following invalid JSON response" in prompts[1]


@pytest.mark.django_db
def test_gemma_client_generate_text_retries_rate_limits(monkeypatch):
    import httpx

    from apps.core.gemma_client import GemmaClient

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    responses = iter(
        [
            httpx.Response(
                429,
                request=httpx.Request("POST", "https://gemini.test"),
                json={"error": {"message": "rate limit exceeded"}},
            ),
            httpx.Response(
                200,
                request=httpx.Request("POST", "https://gemini.test"),
                json={
                    "candidates": [
                        {"content": {"parts": [{"text": "Retry succeeded."}]}}
                    ],
                    "usageMetadata": {
                        "promptTokenCount": 3,
                        "candidatesTokenCount": 5,
                    },
                },
            ),
        ]
    )

    sleep_calls: list[float] = []

    def fake_post(url, json, timeout):  # noqa: ARG001
        return next(responses)

    monkeypatch.setattr("apps.core.llm_provider.httpx.post", fake_post)
    monkeypatch.setattr("apps.core.gemma_client.sleep", lambda seconds: sleep_calls.append(seconds))

    client = GemmaClient(
        provider="gemini",
        api_key="test-key",
        timeout_seconds=5,
        retry_count=1,
        retry_backoff_seconds=0.25,
        task_type="classification",
    )

    result = client.generate_text(
        prompt="Classify this user intent.",
        system="Return a short label.",
    )

    assert result.text == "Retry succeeded."
    assert result.metadata.provider == "gemini"
    assert sleep_calls == [0.25]


@pytest.mark.django_db
def test_gemma_client_rejects_placeholder_gemini_key():
    from apps.core.gemma_client import GemmaClient

    client = GemmaClient(
        provider="gemini",
        api_key="your-gemini-api-key",
        retry_count=0,
    )

    with pytest.raises(Exception) as error_info:
        client.generate_text(prompt="Test prompt", system="Test system")

    assert "placeholder" in str(error_info.value).lower()
