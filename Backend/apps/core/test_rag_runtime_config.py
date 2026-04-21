import sys
from pathlib import Path
from types import SimpleNamespace


def test_rag_runtime_settings_use_backend_ai_settings():
    from apps.core.ai_settings import (
        CHROMA_PERSIST_DIR,
        EMBEDDING_MODEL,
        OLLAMA_HOST,
        OLLAMA_MODEL,
        OLLAMA_TEMPERATURE,
        OLLAMA_TIMEOUT_SECONDS,
    )
    from rag import runtime_settings

    expected_persist_dir = (
        Path(CHROMA_PERSIST_DIR)
        if CHROMA_PERSIST_DIR
        else runtime_settings.DEFAULT_CHROMA_PERSIST_DIR
    )

    assert runtime_settings.get_ollama_base_url() == OLLAMA_HOST
    assert runtime_settings.get_ollama_model() == OLLAMA_MODEL
    assert runtime_settings.get_ollama_timeout_seconds() == OLLAMA_TIMEOUT_SECONDS
    assert runtime_settings.get_ollama_temperature() == OLLAMA_TEMPERATURE
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


def test_rag_generator_uses_configured_ollama_settings(monkeypatch):
    import rag.generator as generator

    captured = {}

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"response": "generated"}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(generator, "check_ollama_available", lambda: True)
    monkeypatch.setattr(generator.requests, "post", fake_post)
    monkeypatch.setattr(
        generator,
        "get_ollama_base_url",
        lambda: "http://ollama.test:11434",
        raising=False,
    )
    monkeypatch.setattr(generator, "get_ollama_model", lambda: "gemma-test", raising=False)
    monkeypatch.setattr(generator, "get_ollama_timeout_seconds", lambda: 19, raising=False)
    monkeypatch.setattr(generator, "get_ollama_temperature", lambda: 0.15, raising=False)

    response = generator.generate_with_ollama("Plan my learning path.")

    assert response == "generated"
    assert captured["url"] == "http://ollama.test:11434/api/generate"
    assert captured["json"]["model"] == "gemma-test"
    assert captured["json"]["options"]["temperature"] == 0.15
    assert captured["timeout"] == 19
