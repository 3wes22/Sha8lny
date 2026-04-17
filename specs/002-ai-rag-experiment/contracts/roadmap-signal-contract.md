# Roadmap Signal Contract

## Scope

This contract defines the structured assessment output that roadmap generation will consume after staged assessment completion.

## 1. Output shape

```json
{
  "role": "backend",
  "target_level": "mid",
  "subskill_gaps": [
    {
      "subskill_key": "api_design",
      "dimension_key": "technical_depth",
      "observed_level": 2.5,
      "target_level": 4,
      "gap": 1.5,
      "confidence": 0.78,
      "evidence_strength": "moderate"
    }
  ],
  "confidence_score": 0.82,
  "evidence_strength": "moderate",
  "priority_order": ["api_design", "database", "testing"],
  "prerequisite_links": {
    "database": ["api_design"]
  },
  "generation_metadata": {
    "assessment_version": "staged-v1",
    "fallback_used": false,
    "trace_id": "trace_id"
  }
}
```

## 2. Field semantics

| Field | Meaning | Consumer use |
|------|---------|--------------|
| `role` | Resolved role key or label | Select roadmap template family and enrichment path |
| `target_level` | User target level for roadmap planning | Bound roadmap ambition |
| `subskill_gaps` | Detailed evidence by subskill | Determine what to teach first |
| `confidence_score` | Overall reliability of the assessment | Adjust roadmap aggressiveness or follow-up prompts |
| `evidence_strength` | Human-readable summary of signal quality | Display and analytics |
| `priority_order` | Ordered subskills for roadmap sequencing | Main roadmap ordering input |
| `prerequisite_links` | Skill dependency map | Prevent invalid sequencing |
| `generation_metadata` | Trace and fallback metadata | Auditability and debugging |

## 3. Compatibility expectations

- `roadmap_signal` is additive during rollout.
- Existing summary fields such as `overall_score`, `skill_scores`, and `recommended_learning_paths` remain available while roadmap consumers migrate.
- Roadmap creation should prefer `roadmap_signal` when present and fall back to existing summary extraction when absent.

## 4. Quality expectations

- `priority_order` must never include keys missing from `subskill_gaps`.
- `prerequisite_links` keys must resolve within the same payload.
- `confidence_score` must be normalized to `0-1`.
- `generation_metadata.fallback_used` must be explicit for every staged completion.
