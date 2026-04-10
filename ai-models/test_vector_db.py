"""Smoke tests for the local vector database setup."""

from pathlib import Path
from importlib import import_module

import pytest


VECTOR_DB_PATH = Path(__file__).parent / "data" / "vector_db"


def test_vector_db_client_can_open_seeded_directory():
    try:
        chromadb = import_module("chromadb")
    except ImportError:
        pytest.skip("chromadb is not installed in this environment.")

    if not VECTOR_DB_PATH.exists():
        pytest.skip("Vector database directory is not seeded in this workspace.")

    client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))
    collections = client.list_collections()

    assert isinstance(collections, list)
