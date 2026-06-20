# Sha8lny Claims Register

Single source of truth for thesis ↔ implementation alignment.  
**Rule:** Every defended claim must be `Done` with evidence, or documented as an explicit limitation.

| ID | Claim | Target | Status | Evidence |
|----|-------|--------|--------|----------|
| C1 | Personalized learning roadmaps (RAG-retrieved roadmap.sh → normalized phases → gap reorder → Gemini copy) | Roadmap POST returns `metadata.generation.provenance.structure_source: roadmap.sh` | Done (fallback-aware) | `assembler.py` + `test_assembler.py` provenance contract; `structure_license_tier=dev_only`; deterministic fallback when Chroma absent |
| C2 | Roadmap references (per-phase provenance + O\*NET where mapped) | UI shows ≥1 external source link per phase | Done | `RoadmapSourcesPanel.tsx` (+ `RoadmapSourcesPanel.test.tsx` both paths); honest deterministic-template badge on fallback |
| C3 | AI skill assessment (documented derivation + optional LLM rubric) | `ROLE_GRAPH_METHODOLOGY.md` + expert review packet | Done (formative) | `ROLE_GRAPH_METHODOLOGY.md`; `engine.py` `score_open_ended` (llm_rubric/keyword) + `test_engine.py`; `EXPERT_REVIEW_PACKET.md` |
| C4 | Role graph weights (partial O\*NET crosswalk) | `docs/product/ROLE_GRAPH_METHODOLOGY.md`, ≥1 role mapped | Done | `ROLE_GRAPH_METHODOLOGY.md` (Backend O\*NET element IDs); `taxonomy_map.py` (35 mappings) + `test_taxonomy_map.py` integrity |
| C5 | RAG career advisor (visible per-query citations) | API `retrieved_documents`; frontend Sources per message | Done | `llm_service.py` public citation contract + `no_retrieval_context`; `MessageSources.tsx`; `advisory/tests.py` + `AdvisoryPage.test.tsx` |
| C6 | Egyptian job market (one-time Wuzzuf ingest) | ≥50 jobs with real `external_url`, `scraped_at` | Done | `ingest_jobs_csv`, `jobs_egypt_tech.csv`, `platform_metadata.source=wuzzuf` |
| C7 | Job–skill matching (embedding + LightGBM rerank) | `job_ranker.lgb` committed; order differs from overlap-only | Done | `ai-models/models/custom/job_ranker.lgb`, `JOB_RANKER_METHODOLOGY.md` |
| C8 | "Why this job?" explainability | API `explanation` object with `top_factors` | Done | `/jobs/match/` + `JobMatchExplanation.tsx` |
| C9 | Course ↔ milestone matching | ≥2 milestones with `match_score > 0` on demo roadmap | Done | `match_courses_for_roadmap` wired into generation (`services.py:914`) + `test_course_matching.py` roadmap-level test |
| C10 | LLM stack thesis accuracy | Gemini + Gemma/Ollama; thesis Ch.2 updated | Done | `ACADEMIC_SUMMARY.md` + `ADR-002-HOSTED-DEMO-AI-RUNTIME.md` document the Gemini-default + Ollama/Gemma fallback stack; deterministic fallbacks per module |
| C11 | Evaluation (expert review + retrieval audit) | Thesis §3.4 appendix tables | Done (faithfulness operator-gated) | `EVALUATION_REPORT.md` + `RAG_RETRIEVAL_EVAL.md` + `EVAL_REPORT.md` + `credibility.py`/tests + `EXPERT_REVIEW_PACKET.md`; LLM-judge faithfulness scaffolded (`eval_faithfulness.py`), real run is an operator step |

## Limitations (explicit, not silent gaps)

- No LLM fine-tuning (hardware/cost); hosted Gemini + local Gemma fallback only.
- No daily job scraping; one-time batch snapshot with `scraped_at`.
- No psychometric validation of assessment scores.
- O\*NET crosswalk depth limited to Backend Developer role in v1.
