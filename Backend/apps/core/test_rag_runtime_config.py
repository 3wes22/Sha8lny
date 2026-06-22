import sys
from pathlib import Path
from types import SimpleNamespace

from apps.core.ai_bridge import ensure_ai_models_path


ensure_ai_models_path()


def test_rag_runtime_settings_use_backend_ai_settings():
    from apps.core.ai_settings import (
        CHROMA_PERSIST_DIR,
        EMBEDDING_MODEL,
        AI_PROVIDER,
        GEMINI_API_BASE_URL,
        GEMINI_FLASH_LITE_MODEL,
        GEMINI_FLASH_MODEL,
        LLM_TEMPERATURE,
        LLM_TIMEOUT_SECONDS,
    )
    from rag import runtime_settings

    expected_persist_dir = (
        Path(CHROMA_PERSIST_DIR)
        if CHROMA_PERSIST_DIR
        else runtime_settings.DEFAULT_CHROMA_PERSIST_DIR
    )

    assert runtime_settings.get_ai_provider() == AI_PROVIDER
    assert runtime_settings.get_gemini_api_base_url() == GEMINI_API_BASE_URL
    assert runtime_settings.get_gemini_flash_lite_model() == GEMINI_FLASH_LITE_MODEL
    assert runtime_settings.get_gemini_flash_model() == GEMINI_FLASH_MODEL
    assert runtime_settings.get_llm_timeout_seconds() == LLM_TIMEOUT_SECONDS
    assert runtime_settings.get_llm_temperature() == LLM_TEMPERATURE
    assert runtime_settings.get_embedding_model() == EMBEDDING_MODEL
    assert runtime_settings.get_chroma_persist_dir() == expected_persist_dir


def test_rag_embeddings_use_configured_embedding_model(monkeypatch):
    created = {}

    class FakeSentenceTransformer:
        def __init__(self, model_name):
            created["model_name"] = model_name

    monkeypatch.setitem(
        sys.modules,
        "numpy",
        SimpleNamespace(ndarray=object, dot=lambda *args, **kwargs: None),
    )
    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        SimpleNamespace(SentenceTransformer=FakeSentenceTransformer),
    )
    import rag.embeddings as embeddings

    monkeypatch.setattr(embeddings, "_model", None)
    monkeypatch.setattr(
        embeddings,
        "get_embedding_model",
        lambda: "sentence-transformers/custom-embed",
        raising=False,
    )

    embeddings.get_model()

    assert created["model_name"] == "sentence-transformers/custom-embed"


def test_rag_vector_store_uses_configured_chroma_persist_dir(monkeypatch, tmp_path):
    import rag.vector_store as vector_store

    captured = {}

    def fake_persistent_client(*, path, settings):
        captured["path"] = path
        captured["settings"] = settings
        return object()

    class FakeSettings:
        def __init__(self, anonymized_telemetry=False):
            self.anonymized_telemetry = anonymized_telemetry

    monkeypatch.setitem(
        sys.modules,
        "chromadb",
        SimpleNamespace(PersistentClient=fake_persistent_client),
    )
    monkeypatch.setitem(
        sys.modules,
        "chromadb.config",
        SimpleNamespace(Settings=FakeSettings),
    )
    monkeypatch.setattr(vector_store, "_client", None)
    monkeypatch.setattr(
        vector_store,
        "get_chroma_persist_dir",
        lambda: tmp_path / "custom-chroma",
        raising=False,
    )

    vector_store.get_client()

    assert captured["path"] == str(tmp_path / "custom-chroma")


def test_rag_generator_uses_configured_gemini_settings(monkeypatch):
    import rag.generator as generator

    captured = {}

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "candidates": [{"content": {"parts": [{"text": "generated"}]}}],
                "usageMetadata": {"promptTokenCount": 2, "candidatesTokenCount": 4},
            }

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(generator.httpx, "post", fake_post)
    monkeypatch.setattr(
        generator,
        "get_gemini_api_base_url",
        lambda: "https://gemini.test/v1beta",
        raising=False,
    )
    monkeypatch.setattr(generator, "get_gemini_flash_model", lambda: "gemini-2.5-flash", raising=False)
    monkeypatch.setattr(generator, "get_llm_timeout_seconds", lambda: 19, raising=False)
    monkeypatch.setattr(generator, "get_llm_temperature", lambda: 0.15, raising=False)
    # generate_with_gemini reads keys via get_gemini_api_keys() (plural, for
    # quota rotation); patch that so the request URL carries the test key.
    monkeypatch.setattr(generator, "get_gemini_api_keys", lambda: ["test-key"])

    response = generator.generate_with_gemini("Plan my learning path.")

    assert response == "generated"
    assert (
        captured["url"]
        == "https://gemini.test/v1beta/models/gemini-2.5-flash:generateContent?key=test-key"
    )
    assert captured["json"]["generationConfig"]["temperature"] == 0.15
    assert captured["timeout"] == 19
