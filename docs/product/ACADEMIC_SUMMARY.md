# Sha8lny — Academic Summary

*Two-page executive summary for the thesis committee. Every claim links to a
named evidence artifact; nothing here is asserted without one.*

## Problem

Egyptian CS graduates face a guidance gap: generic, foreign-market career advice
and no grounded, role-specific signal connecting **where they are** (skills) to
**where the market is** (jobs) and **how to close the distance** (learning). LLM
chatbots alone hallucinate salaries, programs, and requirements — unacceptable
for a decision as consequential as a career.

## Solution and what makes it defensible

Sha8lny is a full-stack platform (Django + React + a local `ai-models` package)
with five AI modules — assessment, roadmap, jobs, advisory, courses — unified by
a **shared, license-clean retrieval layer**. The thesis contribution is **not**
"we called an LLM API." It is:

1. **A measured retrieval stack**, not a single embedding lookup: structure-aware
   chunking → hybrid BM25+dense with reciprocal rank fusion → cross-encoder
   re-ranking → per-source citations with confidence tiers and an abstention
   floor. Built and **measured stage-by-stage** against a locked baseline:
   recall@5 **×5.2**, MRR **×5.0** ([`RAG_RETRIEVAL_EVAL.md`](RAG_RETRIEVAL_EVAL.md),
   [`RAG_ARCHITECTURE.md`](RAG_ARCHITECTURE.md)).
2. **Grounding with honest abstention.** Every answer carries visible sources;
   off-topic queries return *no* answer (`no_retrieval_context`) instead of a
   confident wrong one ([`EVALUATION_REPORT.md`](EVALUATION_REPORT.md) §1).
3. **A formative, documented assessment instrument** — competency graph with
   per-dimension weights and a partial O\*NET 30.1 crosswalk, deterministic
   weighted scoring (the LLM's self-score is never trusted), and an optional LLM
   rubric with a keyword fallback ([`ROLE_GRAPH_METHODOLOGY.md`](ROLE_GRAPH_METHODOLOGY.md)).
4. **A custom learning-to-rank job model** (LightGBM) evaluated by leave-one-group-out
   NDCG/MAP against skill-overlap and random baselines — a transparent
   weak-supervision *demonstrator*, not a black box (`EVAL_REPORT.md`).
5. **Data provenance discipline:** every source is license-screened with a USE /
   REJECT / dev-only decision *before* ingestion
   ([`DATASET_REGISTRY.md`](DATASET_REGISTRY.md)); roadmap.sh is used only as a
   flagged development fallback, never defended as the corpus.

## Architecture (plain language)

A modular-monolith Django backend exposes a JWT REST API; a React/TypeScript
frontend consumes it. The `ai-models` package holds the retrieval stack
(Chroma + sentence-transformers + rank-bm25 + a cross-encoder) and the LightGBM
ranker. Gemini is the hosted demo runtime with a local Ollama/Gemma fallback
([ADR-002](ADR-002-HOSTED-DEMO-AI-RUNTIME.md)); **every AI path has a
deterministic fallback**, so the system runs end-to-end offline with a dead API
key or missing vector store.

## Key results

| Result | Value | Source |
|---|---|---|
| Retrieval recall@5 (baseline → final) | 0.118 → 0.627 (×5.2) | `eval_results/retrieval/*.json` |
| Retrieval MRR | 0.109 → 0.553 (×5.0) | `RAG_RETRIEVAL_EVAL.md` |
| Job ranker ndcg@5 vs overlap / random | 0.589 / 0.560 / 0.160 | `job_ranker_eval.json` |
| Backend test suite | 333 passing | `cd Backend && pytest` |
| Scenario corpus | 8/8 roles, Tier-1 audit passes | `scenario_corpus_audit --tier 1` |

## Honest limitations (stated, not hidden)

- English-only corpus + English-centric embedder → Arabic/code-switched queries
  fail (the top upgrade for an Egyptian platform).
- Precision@5 (0.22) misses the 0.70 target — documented with root cause.
- Job ranker trained on synthetic fixtures with weak labels; real-postings
  upgrade path is scaffolded but is an operator step.
- Assessment is **formative**, not psychometrically validated; expert review is
  packaged but not yet run.
- No LLM fine-tuning (hardware/budget); faithfulness LLM-judge is Gemini-gated.

Full claim-by-claim status: [`CLAIMS_REGISTER.md`](CLAIMS_REGISTER.md).
