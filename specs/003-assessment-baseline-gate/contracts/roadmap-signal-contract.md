# Roadmap Signal Contract

## Scope

This contract defines the structured staged-assessment output that roadmap generation consumes and that the current working-tree candidate must preserve before it becomes baseline.

## 1. Output shape

```json
{
  "role": "backend",
  "target_level": "job-ready",
  "subskill_gaps": [
    {
      "subskill_key": "http_api_design",
      "dimension_key": "api_service_design",
      "observed_level": 2.5,
      "target_level": 4,
      "gap": 1.5,
      "confidence": 0.78,
      "evidence_strength": "moderate"
    }
  ],
  "confidence_score": 0.82,
  "evidence_strength": "moderate",
  "priority_order": ["http_api_design", "service_decomposition", "backend_testing_strategy"],
  "prerequisite_links": {
    "service_decomposition": ["http_api_design"]
  },
  "generation_metadata": {
    "assessment_version": "staged-v1",
    "fallback_used": false,
    "trace_id": "trace_id",
    "model": "gemma4:e2b",
    "version": "curated-v1"
  }
}
```

## 2. Field semantics

| Field | Meaning | Consumer use |
|------|---------|--------------|
| `role` | Resolved role key for staged assessment output | Select roadmap template family and normalize downstream labeling |
| `target_level` | User target outcome for roadmap planning | Bound roadmap ambition |
| `subskill_gaps` | Detailed evidence by subskill | Determine what to teach first |
| `confidence_score` | Overall reliability of the assessment | Adjust roadmap aggressiveness or future follow-up |
| `evidence_strength` | Human-readable summary of signal quality | Display and analytics |
| `priority_order` | Ordered subskills for roadmap sequencing | Primary roadmap ordering input |
| `prerequisite_links` | Skill dependency map | Prevent invalid sequencing |
| `generation_metadata` | Trace, fallback, version, and model metadata | Auditability and debugging |

## 3. Consumer expectations

- `Backend/apps/roadmaps/services.py` prefers `assessment.assessment.target_career` first, then `roadmap_signal.role`, then `recommended_careers` when deriving the user-facing target career.
- Roadmap generation prefers `roadmap_signal.priority_order` and `roadmap_signal.subskill_gaps` over legacy summary-only fields when the signal exists.
- Humanized labels are a consumer concern. Producers may emit stable machine keys such as `http_api_design`.

## 4. Baseline review assertions

The candidate baseline is only acceptable if:

- `priority_order` never references keys missing from `subskill_gaps`.
- `prerequisite_links` resolve within the same payload.
- `confidence_score` is normalized to `0-1`.
- `generation_metadata.fallback_used` is explicit for every staged completion.
- `generation_metadata.version` matches the role-graph version used for the completed assessment.
- `recommended_careers` remains aligned with the same role graph that produced `roadmap_signal`.

## 5. Compatibility expectations

- `roadmap_signal` is additive during rollout.
- Existing summary fields such as `overall_score`, `skill_scores`, and `recommended_learning_paths` remain available while roadmap consumers migrate.
- If `roadmap_signal` is absent for legacy records, roadmap generation falls back to the older summary extraction path.
