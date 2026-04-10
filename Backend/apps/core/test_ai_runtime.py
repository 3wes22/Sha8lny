import pytest


@pytest.mark.django_db
def test_gemma_client_generate_text_returns_metadata():
    from apps.core.gemma_client import GemmaClient

    client = GemmaClient(
        host="http://ollama.test",
        model="gemma-test",
        timeout_seconds=5,
        retry_count=0,
    )

    client._post_generate = lambda payload: {  # type: ignore[method-assign]
        "response": "Career advice goes here.",
        "prompt_eval_count": 12,
        "eval_count": 18,
    }

    result = client.generate_text(
        prompt="Help me plan my backend learning path.",
        system="You are a career advisor.",
    )

    assert result.text == "Career advice goes here."
    assert result.payload is None
    assert result.metadata.source == "llm"
    assert result.metadata.model == "gemma-test"
    assert result.metadata.provider == "ollama"
    assert result.prompt_tokens == 12
    assert result.completion_tokens == 18


@pytest.mark.django_db
def test_gemma_client_generate_structured_retries_until_valid_json():
    from apps.core.gemma_client import GemmaClient

    responses = iter(
        [
            {
                "response": "This is not valid JSON.",
                "prompt_eval_count": 4,
                "eval_count": 6,
            },
            {
                "response": '{"questions": [{"id": 1, "question": "What is your target role?"}]}',
                "prompt_eval_count": 7,
                "eval_count": 9,
            },
        ]
    )

    client = GemmaClient(
        host="http://ollama.test",
        model="gemma-test",
        timeout_seconds=5,
        retry_count=1,
    )
    client._post_generate = lambda payload: next(responses)  # type: ignore[method-assign]

    result = client.generate_structured(
        prompt="Generate one assessment question.",
        system="Return JSON only.",
        required_keys=("questions",),
    )

    assert result.text.startswith('{"questions"')
    assert result.payload == {
        "questions": [{"id": 1, "question": "What is your target role?"}]
    }
    assert result.metadata.model == "gemma-test"
