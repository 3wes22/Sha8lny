# Role Graph Methodology

**Scope:** How Sha8lny derives the per-role competency graph that drives
assessment question allocation and scoring, and how those competencies are
crosswalked to O\*NET 30.1 occupational descriptors.

**Status:** Backed by `apps/assessments/role_graph_taxonomy.py` (curated-v3),
which is the single source of truth and **overrides** the legacy hand-written
graphs at the bottom of `role_graph_data.py`. Positioned as a **formative**
assessment instrument, not a psychometrically validated one (see Limitations).

Related: [`CLAIMS_REGISTER.md`](CLAIMS_REGISTER.md) (C3, C4),
[`DATASET_REGISTRY.md`](DATASET_REGISTRY.md) (O\*NET entry).

---

## 1. Structure

Each role is a graph of **dimensions** → **subskills**:

```
RoleGraph(role_key)
 └── CoreDimension(key, weight, assessment_weight, min_questions_per_stage)
      └── SubSkill(key, label, dimension, target_proficiency)
```

- **dimension.weight** — the dimension's share of the overall role score. Weights
  within a role sum to 1.0 (a residual-drift correction in
  `build_role_graph_from_taxonomy` snaps the final dimension so the sum is exact).
- **dimension.assessment_weight** — relative emphasis when allocating questions.
- **subskill.target_proficiency** — the job-ready bar (1–5) used to compute a
  per-subskill *gap* during scoring.

The overall assessment score is a **weighted roll-up** of per-dimension scores,
computed deterministically by the engine; the LLM's self-reported score is never
trusted (see `Backend/CLAUDE.md`, Assessments).

## 2. Dimension weights per role

Weights are editorial judgments about what matters most for **junior job
readiness** in the Egyptian/MENA market, reviewed against role-specific job
postings. They are heuristics, not measured importances.

### Backend Developer (11 dimensions)

| Dimension | Weight |
|---|---|
| python_fundamentals | 0.12 |
| django_orm | 0.12 |
| rest_api_design | 0.10 |
| database_design | 0.10 |
| system_design_fundamentals | 0.10 |
| authentication_security | 0.09 |
| async_and_task_queues | 0.09 |
| caching_strategy | 0.08 |
| testing | 0.08 |
| debugging_and_observability | 0.07 |
| python_packaging_and_tooling | 0.05 |

### Frontend Developer (11 dimensions)

| Dimension | Weight |
|---|---|
| javascript_fundamentals | 0.15 |
| react_core | 0.15 |
| css_layout_styling | 0.10 |
| react_hooks_depth | 0.10 |
| html_accessibility | 0.08 |
| state_management | 0.08 |
| performance_optimization | 0.08 |
| debugging_devtools | 0.08 |
| typescript_basics | 0.07 |
| testing | 0.06 |
| security_basics | 0.05 |

### Data Science / Data Engineering (11 dimensions)

| Dimension | Weight |
|---|---|
| sql_and_query_optimization | 0.14 |
| data_pipeline_design | 0.13 |
| data_modeling | 0.11 |
| distributed_data_processing | 0.10 |
| data_warehouse_and_lakehouse | 0.10 |
| storage_and_formats | 0.09 |
| streaming_and_messaging | 0.09 |
| data_quality_and_testing | 0.09 |
| python_for_data | 0.08 |
| debugging_data_pipelines | 0.06 |
| orchestration | 0.01 |

The other five roles (`fullstack`, `machine_learning_engineer`, `devops`,
`android`, `ui_ux_designer`) follow the same structure; their weights live in
`role_graph_taxonomy.py`.

## 3. Stage allocation

`StageAllocator.allocate_stage_one` selects ~5 **calibration subskills** per role
(high-leverage, dimension-diverse — at least 4 distinct dimensions). Stage 1 is
all `single_choice` calibration; stage 2 is demand-weighted follow-up targeting
the largest observed gaps (`Stage2Allocator`). The Tier-1 scenario corpus seeds
≥2 reviewed `single_choice` items per calibration subskill for every role (see
`scenario_corpus_audit --tier 1`).

## 4. O\*NET 30.1 crosswalk

Subskills are crosswalked to O\*NET **work-activity / skill element IDs** so the
competencies trace to an authoritative occupational taxonomy (public domain;
see `DATASET_REGISTRY.md`). The crosswalk is implemented in
`apps/roadmaps/onet_mapper.py` and is an honest **proof-of-concept depth**:
**Backend Developer is mapped in depth**; Frontend and Data Science reuse the
shared programming/troubleshooting elements where the mapping is clean; other
roles return no O\*NET links rather than fabricating them.

### Backend crosswalk (concrete element IDs)

| Competency keyword | O\*NET element | Title | Confidence |
|---|---|---|---|
| programming / python | `2.B.3.e` | Programming | 0.88–0.90 |
| rest api / api / database / sql / deploy | `2.B.4.g` | Systems Analysis | 0.76–0.82 |
| deploy | `2.B.4.h` | Systems Evaluation | 0.77 |
| authentication | `2.B.3.b` | Technology Design | 0.75 |
| testing | `2.B.3.m` | Quality Control Analysis | 0.84 |
| debug | `2.B.3.k` | Troubleshooting | 0.83 |

Each mapping resolves to `https://www.onetonline.org/find/descriptor/browse/<id>/`.
Confidences are authoring judgments, not measured agreement.

Frontend and Data Science inherit the `2.B.3.e` (Programming) and `2.B.3.k`
(Troubleshooting) elements for their programming/debugging subskills; specialized
subskills (e.g., `responsive_css`, `star_schema`) are intentionally left
unmapped because no clean O\*NET descriptor exists at this granularity.

## 5. External taxonomy ingestion map

`apps/assessments/scenario_corpus/taxonomy_map.py` declares how external
question-bank keys (LinkedIn-style quiz JSON, interview-question CSVs) translate
to curated `(role_key, subskill_key)` pairs, so future content adapters emit
draft scenarios pinned to the right competency. It ships **35 mappings** across
five roles; `tests/test_taxonomy_map.py` asserts every target resolves to a real
subskill (integrity gate) and that ≥15 mappings exist.

## 6. Limitations

- **Not psychometrically validated.** Weights, target proficiencies, and O\*NET
  confidences are expert judgments, not derived from item-response data.
- **O\*NET depth is a PoC** — only Backend is mapped thoroughly; this is
  documented future work, not hidden.
- **Phase sizing** (hours/weeks) elsewhere in the platform uses documented
  heuristics, not validated learning science.
- Expert review of open-ended items is supported by
  [`EXPERT_REVIEW_PACKET.md`](EXPERT_REVIEW_PACKET.md); running the review is a
  developer action item.
