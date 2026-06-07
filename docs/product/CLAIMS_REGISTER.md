# Sha8lny Claims Register

Single source of truth for thesis ↔ implementation alignment.  
**Rule:** Every defended claim must be `Done` with evidence, or documented as an explicit limitation.

| ID | Claim | Target | Status | Evidence |
|----|-------|--------|--------|----------|
| C1 | Personalized learning roadmaps (RAG-retrieved roadmap.sh → normalized phases → gap reorder → Gemini copy) | Roadmap POST returns `metadata.generation.provenance.structure_source: roadmap.sh` | In Progress | `assembler.py` wired; requires Chroma `career_knowledge` seeded for non-fallback path |
| C2 | Roadmap references (per-phase provenance + O\*NET where mapped) | UI shows ≥1 external source link per phase | In Progress | `RoadmapSourcesPanel.tsx` + `metadata.generation.provenance` |
| C3 | AI skill assessment (documented derivation + optional LLM rubric) | `ROLE_GRAPH_METHODOLOGY.md` + expert review table | Not Started | Week 3 |
| C4 | Role graph weights (partial O\*NET crosswalk) | `docs/product/ROLE_GRAPH_METHODOLOGY.md`, ≥1 role mapped | Not Started | Week 3 |
| C5 | RAG career advisor (visible per-query citations) | API `retrieved_documents`; frontend Sources per message | Not Started | Week 3 |
| C6 | Egyptian job market (one-time Wuzzuf ingest) | ≥50 jobs with real `external_url`, `scraped_at` | Done | `ingest_jobs_csv`, `jobs_egypt_tech.csv`, `platform_metadata.source=wuzzuf` |
| C7 | Job–skill matching (embedding + LightGBM rerank) | `job_ranker.lgb` committed; order differs from overlap-only | Done | `ai-models/models/custom/job_ranker.lgb`, `JOB_RANKER_METHODOLOGY.md` |
| C8 | "Why this job?" explainability | API `explanation` object with `top_factors` | Done | `/jobs/match/` + `JobMatchExplanation.tsx` |
| C9 | Course ↔ milestone matching | ≥2 milestones with `match_score > 0` on demo roadmap | Not Started | Week 3 verify |
| C10 | LLM stack thesis accuracy | Gemini + Gemma/Ollama; thesis Ch.2 updated | Not Started | Week 4 |
| C11 | Evaluation (expert review + retrieval audit) | Thesis §3.4 appendix tables | Not Started | Week 4 |

## Limitations (explicit, not silent gaps)

- No LLM fine-tuning (hardware/cost); hosted Gemini + local Gemma fallback only.
- No daily job scraping; one-time batch snapshot with `scraped_at`.
- No psychometric validation of assessment scores.
- O\*NET crosswalk depth limited to Backend Developer role in v1.
