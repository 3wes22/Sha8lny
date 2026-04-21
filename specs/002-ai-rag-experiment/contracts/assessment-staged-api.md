# Assessment Staged API Contract

## Scope

This contract defines the staged assessment API behavior that the current working-tree candidate must preserve before it can become the branch baseline.

## 1. Create assessment

### Request

`POST /assessment/`

```json
{
  "assessment_type": "skills",
  "target_career": "Backend Developer"
}
```

### Required behavior

- New `skills` assessments are created in staged mode.
- The response exposes stage and generation readiness explicitly.
- The initial create response may return before stage-one generation completes.

### Response shape

```json
{
  "id": "uuid",
  "assessment_type": "skills",
  "target_career": "Backend Developer",
  "stage": "stage_1",
  "generation_status": "pending",
  "active_questions": [],
  "gap_profile_summary": null,
  "questions": [],
  "responses": [],
  "presentation": {
    "submission_state": "stage_1_generating",
    "question_count": 0,
    "current_index": 0,
    "progress_ratio": 0,
    "estimated_minutes": 8
  }
}
```

## 2. Get assessment session

### Request

`GET /assessment/{assessment_id}/`

### Required behavior

- Staged assessments return the active stage and only the active question set.
- The response preserves a readable shape for legacy assessments during rollout.
- The frontend can decide whether to poll, render questions, or show a transition state without guessing.

### Response fields

| Field | Required | Notes |
|------|----------|-------|
| `stage` | Yes for staged records | `stage_1`, `stage_2`, `completed` |
| `generation_status` | Yes for staged records | `pending`, `processing`, `completed`, `failed` |
| `active_questions` | Yes for staged records | Current-stage questions only |
| `gap_profile_summary` | Optional | Present after stage-one processing |
| `presentation.submission_state` | Yes | Must distinguish ready, generating, analyzing, completed, and failed states |

### `presentation.submission_state` values

- `stage_1_generating`
- `stage_1_ready`
- `stage_1_analyzing`
- `stage_2_ready`
- `stage_2_analyzing`
- `completed`
- `failed`

## 3. Submit assessment stage

### Request

`POST /assessment/{assessment_id}/submit/`

```json
{
  "responses": [
    {
      "question_id": "s1_q1",
      "answer": "mid",
      "timestamp": "2026-04-14T00:00:00Z"
    }
  ]
}
```

### Required behavior

- Submission is stage-aware for staged assessments.
- If the current stage is `stage_1`, the backend stores stage-one responses, computes the gap profile, and starts stage-two generation.
- If the current stage is `stage_2`, the backend stores stage-two responses and starts final evaluation.
- Legacy assessments remain compatible until explicit sunset work is planned and accepted separately.

### Response shape for stage-one submission

```json
{
  "message": "Stage one submitted successfully and stage two is being prepared",
  "assessment": {
    "id": "uuid",
    "stage": "stage_1",
    "generation_status": "processing",
    "active_questions": [],
    "presentation": {
      "submission_state": "stage_1_analyzing"
    }
  },
  "result_id": null,
  "submission_state": "stage_1_analyzing"
}
```

### Response shape for stage-two submission

```json
{
  "message": "Assessment submitted successfully and queued for final analysis",
  "assessment": {
    "id": "uuid",
    "stage": "stage_2",
    "generation_status": "processing",
    "active_questions": [],
    "presentation": {
      "submission_state": "stage_2_analyzing"
    }
  },
  "result_id": null,
  "submission_state": "stage_2_analyzing"
}
```

## 4. Get assessment result

### Request

`GET /assessment/{assessment_id}/result/`

### Required behavior

- In-flight work still returns processing responses.
- Completed staged results expose `roadmap_signal`.
- Compatibility summary fields remain present during rollout.

### Completed response shape

```json
{
  "id": "result_uuid",
  "assessment": "assessment_uuid",
  "overall_score": 74.5,
  "skill_scores": {
    "api_service_design": 68,
    "data_persistence": 72
  },
  "strengths": ["Strong debugging discipline"],
  "areas_for_improvement": ["Service decomposition"],
  "recommended_careers": [
    {
      "title": "Backend Developer",
      "match_score": 92,
      "reasoning": "This staged result is calibrated against the curated backend developer graph."
    }
  ],
  "recommended_learning_paths": [
    { "skill": "HTTP API Design", "priority": "high", "resources": [] }
  ],
  "roadmap_signal": {
    "role": "backend",
    "target_level": "job-ready",
    "subskill_gaps": [],
    "confidence_score": 0.82,
    "evidence_strength": "moderate",
    "priority_order": ["http_api_design", "service_decomposition"],
    "prerequisite_links": {
      "service_decomposition": ["http_api_design"]
    },
    "generation_metadata": {
      "assessment_version": "staged-v1",
      "fallback_used": false,
      "trace_id": "trace",
      "version": "curated-v1"
    }
  },
  "submission_state": "completed"
}
```

## 5. Baseline review assertions

The current working-tree candidate can only become baseline if these assertions remain true:

- `POST /assessment/` returns staged `skills` assessments in `stage_1` with `stage_1_generating`.
- Once stage one is ready, the detail response exposes exactly 5 active questions.
- Stage-one submit returns `stage_1_analyzing`, and the next ready detail response exposes `stage_2_ready`.
- Once stage two is ready, the detail response exposes exactly 5 active questions.
- The completed result exposes `roadmap_signal`, `submission_state = completed`, and compatibility summary fields.
- The typed frontend `AssessmentSubmissionState` union continues to cover every staged state emitted by the backend.

## 6. Compatibility rules

- New `skills` assessments use the staged contract.
- Legacy single-stage assessments remain readable and completable during rollout.
- Existing `questions` and `responses` fields remain available until consumers explicitly migrate away from them.
- Typed frontend consumers in `Frontend/src/lib/api.ts` add staged fields without dropping the legacy compatibility shape prematurely.
