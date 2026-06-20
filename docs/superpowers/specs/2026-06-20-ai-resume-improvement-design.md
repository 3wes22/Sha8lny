# AI Resume Improvement — Design

Date: 2026-06-20
Status: Approved

## Problem

The Career Tools "Optimize for ATS" button only runs a deterministic scorer
that returns a numeric score plus a generic checklist (e.g. "Add work
experience entries"). It never changes the resume, so the verb "Optimize" is
misleading and the suggestions are not tailored to the user's actual content.

## Goal

Replace the misleading action with real, content-aware AI assistance: send the
resume to Gemini (via the existing `GemmaClient`), get an improved summary,
stronger bullet suggestions, missing ATS keywords, and prioritized
recommendations. Let the user apply the rewritten summary back to the resume.

## Non-Goals (YAGNI)

- Auto-rewriting every work-experience entry field-by-field.
- Generating multiple resume variants.
- Streaming token output.
- Binary PDF/DOCX export (already deferred to v2).

## Backend

### `ResumeService.improve_with_ai(resume) -> dict`

1. Build context from the resume's structured sections (reuse
   `build_resume_document`) plus the current deterministic score and
   suggestions from `compute_ats_score`.
2. Call `GemmaClient(task_type="json_generation").generate_structured(...)`
   with a response JSON schema and `required_keys` for:
   - `improved_summary: str`
   - `strengthened_bullets: list[str]`
   - `missing_keywords: list[str]`
   - `recommendations: list[str]`
3. Return a payload:
   ```json
   {
     "ai_used": true,
     "ats_score": 72.0,
     "ats_grade": "C",
     "improved_summary": "…",
     "strengthened_bullets": ["…"],
     "missing_keywords": ["…"],
     "recommendations": ["…"]
   }
   ```
4. **Graceful fallback**: if the client raises `AIServiceError` (or any
   exception), return `ai_used: false` with the deterministic suggestions in
   `recommendations`, so the action never hard-fails when AI is offline.

### Endpoint

`POST /api/v1/career-tools/resumes/{id}/improve/` (detail action on
`ResumeViewSet`) → 200 with the improvement payload. User-scoped via the
existing `get_queryset`.

### Saving improvements

No new write endpoint. The frontend applies the rewritten summary using the
existing `PATCH /resumes/{id}/` (the `personal_info` field is already writable
on `ResumeSerializer`), then re-runs `optimize_ats` to refresh the score.

## Frontend (Career Tools resume card)

- Rename "Optimize for ATS" → **"Improve with AI"** (the ATS score badge stays
  and refreshes after applying).
- On click, call `careerToolsApi.improveResume(id)` and render a result panel:
  - Before/after summary (current summary vs. `improved_summary`).
  - Suggested stronger bullets.
  - Missing-keyword chips.
  - Prioritized recommendations.
  - A small `ai_used: false` notice when the deterministic fallback was used.
- An **"Apply summary"** button calls `careerToolsApi.updateResume(id, {
  personal_info: { …, summary } })` then `optimizeAts(id)` to refresh the grade.

## Testing (TDD)

### Backend
- `improve_with_ai` with a stubbed `GemmaClient.generate_structured` returns the
  four structured fields and `ai_used: true`.
- Fallback: when the stub raises, returns `ai_used: false` with deterministic
  recommendations.
- Endpoint returns 200 with the payload for the owner; 404 for non-owners.

### Frontend
- Clicking "Improve with AI" calls the improve API and renders the before/after
  summary and "Apply summary".
- Clicking "Apply summary" calls `updateResume` then `optimizeAts`.

## Risks / Notes

- Gemini quality varies; we only auto-apply the summary (one click), while
  bullets/keywords are advisory so we never clobber the user's work history.
- Token usage is tracked by `GemmaResponse`; surfaced in logs as with other AI
  calls.
