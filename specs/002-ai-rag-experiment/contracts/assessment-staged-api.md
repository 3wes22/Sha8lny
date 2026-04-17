# Assessment Staged API Contract

## Scope

This contract defines the external API behavior required for the staged skills-assessment rollout. It covers new assessments created after the migration and the compatibility rules for legacy records.

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
- The response must expose current stage and generation readiness explicitly.
- Stage-one question generation may still be processing on first response.

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

- Must return the active stage and only the active question set for staged assessments.
- Must preserve a readable shape for legacy assessments during rollout.
- Must expose enough information for the frontend to decide whether to poll, render questions, or show transition state.

### Response fields

| Field | Required | Notes |
|------|----------|-------|
| `stage` | Yes for staged records | `stage_1`, `stage_2`, `completed` |
| `generation_status` | Yes for staged records | `pending`, `processing`, `completed`, `failed` |
| `active_questions` | Yes for staged records | Current stage question list |
| `gap_profile_summary` | Optional | Present after stage one processing |
| `presentation.submission_state` | Yes | Must distinguish stage-ready and stage-analyzing states |

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

- Endpoint is stage-aware for staged assessments.
- If current stage is `stage_1`, submission must store stage-one responses, trigger deterministic scoring, and start stage-two generation.
- If current stage is `stage_2`, submission must store stage-two responses and trigger final evaluation.
- Legacy assessments may continue to use compatibility behavior until sunset.

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

- Must continue to use processing responses for in-flight work.
- Must expose `roadmap_signal` on completion.
- Must keep compatibility summary fields during rollout.

### Completed response shape

```json
{
  "id": "result_uuid",
  "assessment": "assessment_uuid",
  "overall_score": 74.5,
  "skill_scores": {
    "technical_depth": 68,
    "tooling": 72
  },
  "strengths": ["Strong debugging discipline"],
  "areas_for_improvement": ["REST API design depth"],
  "recommended_learning_paths": [
    { "skill": "REST API Design", "priority": "high", "resources": [] }
  ],
  "roadmap_signal": {
    "role": "backend",
    "target_level": "mid",
    "subskill_gaps": [],
    "confidence_score": 0.82,
    "evidence_strength": "moderate",
    "priority_order": ["api_design", "database"],
    "prerequisite_links": {
      "database": ["api_design"]
    },
    "generation_metadata": {
      "fallback_used": false,
      "trace_id": "trace"
    }
  },
  "submission_state": "completed"
}
```

## 5. Compatibility rules

- New `skills` assessments must use the staged contract.
- Legacy single-stage assessments remain readable and completable during rollout.
- Existing `questions` and `responses` fields remain available until frontend and roadmap consumers finish migration.
- Frontend typed consumers in `Frontend/src/lib/api.ts` must add staged fields without removing the legacy compatibility shape immediately.
