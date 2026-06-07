"""Human-readable ranking explanations from feature vectors."""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np

from recommendations.feature_engineering import FEATURE_NAMES


def explain_ranking(
    feature_vector: np.ndarray,
    *,
    matching_skills: Sequence[str],
    missing_skills: Sequence[str],
    feature_importances: Sequence[float] | None = None,
    top_k: int = 3,
) -> dict[str, Any]:
    """
    Build explanation payload for API consumers.

    Uses weighted feature contribution (value × importance) when importances
  are available; otherwise ranks by raw feature value.
    """
    vector = np.asarray(feature_vector, dtype=np.float32).reshape(-1)
    if feature_importances is not None and len(feature_importances) == len(vector):
        weights = np.asarray(feature_importances, dtype=np.float32)
        contributions = vector * weights
    else:
        contributions = vector

    ranked_indices = np.argsort(-np.abs(contributions))[:top_k]
    top_factors = []
    for index in ranked_indices:
        name = FEATURE_NAMES[int(index)]
        top_factors.append(
            {
                "feature": name,
                "value": round(float(vector[index]), 4),
                "contribution": round(float(contributions[index]), 4),
            }
        )

    return {
        "matching_skills": list(matching_skills),
        "missing_skills": list(missing_skills),
        "top_factors": top_factors,
    }
