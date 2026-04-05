# Data Model: Sha8alny Frontend Visual Reconstruction

## 1. ExperienceSurface

Represents a major user-facing screen or route that must adopt the reconstructed visual system.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `id` | string | Stable identifier for the screen | Required, unique |
| `route` | string | User-facing route path | Required |
| `audience` | enum | Primary audience segment (`student`, `job_seeker`, `professional`, `shared`) | Required |
| `purpose` | string | Primary user value delivered by the screen | Required |
| `primary_action` | string | Most important action on the screen | Required |
| `data_dependencies` | list | Backend data needed to render the screen | Required |
| `supports_empty_state` | boolean | Whether an empty-state treatment is needed | Required |
| `supports_processing_state` | boolean | Whether async or in-progress states must be shown | Required |

## 2. NavigationShell

Represents the global frame shared by authenticated product routes.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `primary_sections` | list | Main navigation destinations | Required |
| `secondary_actions` | list | User/profile/settings related actions | Required |
| `notification_summary` | object | Badge count and recent-notification data | Optional |
| `context_label` | string | Current section or route context | Optional |
| `responsive_mode` | enum | `desktop`, `tablet`, `mobile` | Required |

**Relationships**:

- One `NavigationShell` contains many `ExperienceSurface` instances.

## 3. RoadmapJourneyView

Represents the structured roadmap presentation shown to the user.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `roadmap_id` | string | Backend roadmap identifier | Required |
| `title` | string | User-facing roadmap name | Required |
| `summary` | string | Short framing text | Required |
| `phases` | list of `RoadmapNode` | Top-level roadmap phases | Required |
| `current_focus_node_id` | string | Node emphasized as next action | Optional |
| `completion_ratio` | number | Overall completion indicator | 0-100 |
| `presentation_mode` | enum | `atlas`, `stacked`, `detail` | Required |

## 4. RoadmapNode

Represents a phase, milestone, or course-like item inside the roadmap journey.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `id` | string | Stable node identifier | Required |
| `node_type` | enum | `phase`, `milestone`, `course` | Required |
| `title` | string | User-facing label | Required |
| `parent_id` | string | Parent node reference | Optional |
| `status` | enum | `locked`, `available`, `active`, `completed` | Required |
| `estimated_effort` | string | Relative effort label | Optional |
| `next_action` | string | Suggested next move | Optional |

**State transitions**:

- `locked -> available`
- `available -> active`
- `active -> completed`

## 5. AssessmentPresentationSession

Represents the guided assessment experience from question progression through results.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `assessment_id` | string | Backend assessment identifier | Required |
| `question_count` | number | Number of questions in the flow | Required |
| `current_index` | number | Active question position | Required |
| `progress_ratio` | number | Current completion value | 0-100 |
| `interaction_mode` | enum | `single_select`, `multi_select`, `scale`, `text`, `visual_choice` | Required |
| `submission_state` | enum | `draft`, `submitting`, `processing`, `completed`, `failed` | Required |
| `result_summary_available` | boolean | Whether results payload is ready | Required |

**State transitions**:

- `draft -> submitting`
- `submitting -> processing`
- `processing -> completed`
- `processing -> failed`

## 6. AssessmentOutcomePanel

Represents the result surface presented after or during assessment completion.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `assessment_id` | string | Associated assessment | Required |
| `status_message` | string | Current status explanation | Required |
| `score_summary` | string | High-level score or evaluation summary | Optional |
| `strengths` | list | Positive capability highlights | Optional |
| `growth_areas` | list | Recommended focus areas | Optional |
| `next_actions` | list | Available calls to action after results | Required |

## 7. JobOpportunityCard

Represents the reusable job presentation block across search, saved, and detail entry points.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `job_id` | string | Backend job identifier | Required |
| `title` | string | Job title | Required |
| `company_name` | string | Employer name | Required |
| `location` | string | Display location | Required |
| `job_type` | string | Employment type | Required |
| `is_saved` | boolean | Whether the user saved the job | Required |
| `external_action_available` | boolean | Whether apply URL exists | Required |

## 8. ContractTouchpoint

Represents a frontend surface that depends on a backend endpoint or payload behavior.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `surface_id` | string | Linked `ExperienceSurface` identifier | Required |
| `endpoint_group` | string | Backend route family | Required |
| `required_states` | list | States the UI expects | Required |
| `typed_consumer` | string | Frontend API consumer path | Required |
| `contract_risk` | enum | `low`, `medium`, `high` | Required |

## Relationships Summary

- One `NavigationShell` frames many `ExperienceSurface` items.
- One `RoadmapJourneyView` contains many `RoadmapNode` items.
- One `AssessmentPresentationSession` leads to one `AssessmentOutcomePanel`.
- Many `ExperienceSurface` items depend on one or more `ContractTouchpoint` records.
