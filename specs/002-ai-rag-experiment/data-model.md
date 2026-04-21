# Data Model: Staged Assessment Baseline Review Gate

## 1. BaselineCandidate

Represents the current staged-assessment working tree snapshot under review.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `branch` | string | Feature branch being reviewed | Required, expected `002-ai-rag-experiment` |
| `candidate_scope` | list of strings | Files or modules included in the gate | Required, non-empty |
| `role_graph_version` | string | Declared graph version used by the candidate | Required |
| `contract_surfaces` | list of `ContractSurface` keys | Interfaces affected by the candidate | Required |
| `decision_status` | enum | Current review state | Required, one of `pending_review`, `evidence_collected`, `human_reviewed`, `accepted`, `revised`, `rejected` |

## 2. ContractSurface

Represents one externally meaningful behavior that the gate must evaluate.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `key` | string | Stable identifier such as `assessment_api` or `roadmap_signal` | Required, unique within the gate |
| `owner_area` | string | Owning module or layer | Required |
| `source_files` | list of strings | Files that define or consume this contract | Required |
| `invariants` | list of strings | Rules that must remain true for baseline acceptance | Required |
| `blocking` | boolean | Whether failure on this surface blocks baseline adoption | Required |

## 3. ReviewCriterion

Represents one gate criterion applied to the candidate baseline.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `key` | string | Stable criterion identifier | Required |
| `surface_key` | string | Linked `ContractSurface` key | Required |
| `question` | string | Human-readable review question | Required |
| `required_evidence` | list of strings | Commands, docs, or walkthroughs needed to answer the question | Required |
| `status` | enum | Review result for this criterion | Required, one of `not_started`, `pass`, `fail`, `needs_followup` |
| `blocking_reason` | string | Explanation when the criterion fails | Optional |

## 4. EvidenceArtifact

Represents one collected piece of evidence used by the gate.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `type` | enum | `diff_review`, `test_run`, `contract_review`, `manual_walkthrough`, `decision_note` | Required |
| `source` | string | Command, file path, or narrative source | Required |
| `scope` | string | What the evidence covers | Required |
| `outcome` | string | Short result summary | Required |
| `recorded_at` | string | When the evidence was collected | Required for stored review records |

## 5. RoleGraphContractSnapshot

Represents the curated role-graph baseline expectations used in the review.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `supported_roles` | list of strings | Roles that must exist in the mapping | Required, 6 entries for current scope |
| `dimension_count` | integer | Required dimensions per role | Required, exactly `4` for curated baseline |
| `subskill_range` | object | Allowed total subskill range per role | Required, `15-20` |
| `mapping_key_must_match_role_key` | boolean | Loader must reject mismatched mapping keys | Required, `true` |
| `version_bound_cache` | boolean | Stage-one cache must vary by graph version | Required, `true` |

## 6. AssessmentContractSnapshot

Represents the staged assessment API and frontend-state semantics that the gate must preserve.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `stage_values` | list of strings | Supported staged assessment phases | Required, includes `stage_1`, `stage_2`, `completed` |
| `submission_states` | list of strings | Typed frontend/backend submission states | Required |
| `stage_question_count` | object | Expected question count per stage | Required, `5` for both stages in current scope |
| `result_requires_roadmap_signal` | boolean | Completed staged result must expose roadmap-ready signal | Required, `true` |
| `legacy_compatibility_required` | boolean | Legacy records remain readable during rollout | Required, `true` |

## 7. RoadmapSignalSnapshot

Represents the downstream contract expected from staged assessment completion.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `role` | string | Role key emitted by staged assessment | Required |
| `subskill_gaps` | list | Structured gap evidence | Required |
| `priority_order` | list of strings | Ordered subskill keys for roadmap sequencing | Required |
| `prerequisite_links` | object | Dependency mapping across returned subskills | Required |
| `generation_metadata` | object | Must include fallback and trace semantics | Required |

## 8. BaselineDecisionRecord

Represents the human outcome of the review gate.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `outcome` | enum | Final review decision | Required, one of `accept`, `revise`, `reject` |
| `rationale` | string | Summary of why the decision was made | Required |
| `blocking_findings` | list of strings | Findings that prevent acceptance | Optional, required when outcome is `revise` or `reject` |
| `follow_up_actions` | list of strings | Next steps after the decision | Required for `accept` and `revise` |
| `approver` | string | Human reviewer or team owner | Required |
| `recorded_at` | string | Decision timestamp | Required |

## Relationships Summary

- One `BaselineCandidate` references many `ContractSurface` records.
- One `ContractSurface` can have many `ReviewCriterion` records.
- One gate execution collects many `EvidenceArtifact` records against one `BaselineCandidate`.
- One `BaselineDecisionRecord` is produced only after blocking `ReviewCriterion` records have been evaluated.
- `RoleGraphContractSnapshot`, `AssessmentContractSnapshot`, and `RoadmapSignalSnapshot` define the behavioral baseline that the candidate must satisfy.
