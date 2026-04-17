# Data Model: Two-Stage Adaptive Assessment Question Generation

## 1. RoleGraph

Represents the role-specific capability map used by staged assessment generation and scoring.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `role_key` | string | Canonical machine key for the role | Required, unique within supported roles |
| `role_label` | string | Human-readable role name | Required |
| `dimensions` | list of `CoreDimension` | Ordered list of assessment dimensions for the role | Required, 3-5 items |
| `version` | string | Version tag for cache invalidation and handoff tracking | Required |

**Relationships**:

- One `RoleGraph` contains many `CoreDimension` records.

## 2. CoreDimension

Represents a weighted assessment area within a role graph.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `key` | string | Stable dimension identifier | Required |
| `label` | string | Human-readable dimension name | Required |
| `weight` | number | Relative contribution to calibration and prioritization | Required, 0-1 |
| `subskills` | list of `SubSkill` | Ordered list of subskills in this dimension | Required, 3-6 items |

**Validation rules**:

- Sum of dimension weights for one role graph must equal `1.0`.

## 3. SubSkill

Represents a measurable capability target inside a role graph.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `key` | string | Stable subskill identifier | Required, unique within role |
| `label` | string | Human-readable subskill name | Required |
| `dimension` | string | Parent dimension key | Required, must map to an existing dimension |
| `target_proficiency` | integer | Expected role proficiency on a 1-5 scale | Required, 1-5 |
| `prerequisites` | list of strings | Earlier subskill keys that should come first | Optional, must resolve within the same role graph |

## 4. StageQuestion

Represents a generated assessment question bound to a stage and graph target.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `id` | string | Stable stage-scoped question identifier | Required, unique within assessment |
| `stage` | integer | Assessment stage number | Required, `1` or `2` |
| `subskill_key` | string | Targeted subskill | Required |
| `dimension_key` | string | Targeted dimension | Required |
| `question_text` | string | User-facing prompt | Required |
| `question_type` | enum | `multiple_choice`, `scale`, `text` | Required |
| `interaction_mode` | enum | Frontend render mode | Required |
| `options` | list | Structured answer options for choice questions | Optional for non-choice types |
| `difficulty` | integer | Intended difficulty band | Required, 1-5 |
| `estimated_seconds` | integer | Expected answer time | Required, positive |

## 5. StageResponse

Represents a user answer recorded against a staged question.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `question_id` | string | Linked `StageQuestion` identifier | Required |
| `answer` | string or number | Submitted answer payload | Required |
| `timestamp` | string | Submission time | Optional |

## 6. SubSkillEvidence

Represents deterministic scoring evidence for one subskill.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `subskill_key` | string | Targeted subskill | Required |
| `dimension_key` | string | Parent dimension | Required |
| `observed_level` | number | Measured current level | Required, 0-5 |
| `target_level` | integer | Expected level from role graph | Required, 1-5 |
| `gap` | number | Difference between target and observed level | Required |
| `confidence` | number | Confidence score for the observed level | Required, 0-1 |
| `evidence_strength` | enum | `strong`, `moderate`, `weak` | Required |

## 7. GapProfile

Represents the intermediate calibration result after stage one.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `role_key` | string | Resolved role key | Required |
| `subskill_evidence` | list of `SubSkillEvidence` | Evidence records produced from stage one | Required |
| `high_priority_gaps` | list of strings | Ordered subskill keys needing immediate follow-up | Required |
| `uncertain_areas` | list of strings | Subskill keys with low confidence requiring clarification | Required |
| `overall_calibration` | number | Composite calibration score | Required, 0-100 |

## 8. RoadmapSignal

Represents the final structured assessment output consumed by roadmap generation.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `role` | string | Role label or role key used for roadmap generation | Required |
| `target_level` | string | Derived user target level for the role | Required |
| `subskill_gaps` | list of `SubSkillEvidence` | Ordered evidence records from the full staged assessment | Required |
| `confidence_score` | number | Overall confidence in the assessment result | Required, 0-1 |
| `evidence_strength` | string | Summary label for overall evidence quality | Required |
| `priority_order` | list of strings | Ordered subskill keys for roadmap prioritization | Required |
| `prerequisite_links` | object | Mapping of subskill key to prerequisite keys | Required |
| `generation_metadata` | object | Trace, fallback, and validation metadata | Required |

## 9. Assessment (staged extension)

Represents the persisted assessment session across both stages.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `stage` | enum | `stage_1`, `stage_2`, `completed` | Required for new staged assessments |
| `stage_one_questions` | list of `StageQuestion` | Persisted calibration questions | Optional for legacy records |
| `stage_one_responses` | list of `StageResponse` | Persisted calibration responses | Optional |
| `stage_two_questions` | list of `StageQuestion` | Persisted targeted questions | Optional until stage two generation completes |
| `stage_two_responses` | list of `StageResponse` | Persisted targeted responses | Optional |
| `gap_profile` | `GapProfile` | Intermediate stage-one output | Optional until stage one submission completes |
| `roadmap_signal` | `RoadmapSignal` | Final structured assessment output | Optional until completion |
| `generation_metadata` | object | Cache, fallback, validation, and trace metadata | Optional |

**State transitions**:

- `stage_1` + generation pending -> `stage_1` ready
- `stage_1` ready -> `stage_2` generating
- `stage_2` generating -> `stage_2` ready
- `stage_2` ready -> `completed`
- Any staged state -> `failed` generation status

## 10. AssessmentResult (staged extension)

Represents the user-facing finalized result object.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `overall_score` | number | High-level score retained for compatibility | Required |
| `skill_scores` | object | Summary score map retained for compatibility | Required |
| `recommended_learning_paths` | list | Existing summary guidance retained for compatibility | Required |
| `roadmap_signal` | `RoadmapSignal` | New structured roadmap-ready output | Required for staged completions |

## Relationships Summary

- One `RoleGraph` contains many `CoreDimension` records.
- One `CoreDimension` contains many `SubSkill` records.
- One staged `Assessment` contains stage-one and stage-two `StageQuestion` and `StageResponse` collections.
- One staged `Assessment` produces one `GapProfile` and one final `RoadmapSignal`.
- One `AssessmentResult` belongs to one `Assessment` and stores the final `RoadmapSignal` alongside compatibility summaries.
