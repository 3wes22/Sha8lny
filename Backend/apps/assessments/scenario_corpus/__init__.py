"""Scenario RAG corpus for staged assessment question generation.

The authored, version-controlled source of truth for retrievable few-shot
examples. The derived Chroma index lives at
``apps.core.ai_settings.SCENARIO_VECTOR_DB_PATH`` and is rebuilt from this
package by ``manage.py rebuild_scenario_index``.

See ``specs/005-scenario-rag-corpus/`` for the full design.
"""
