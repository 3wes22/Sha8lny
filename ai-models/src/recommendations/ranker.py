"""
LightGBM job ranker — loads committed model or falls back to overlap sort.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import numpy as np

from recommendations.explainer import explain_ranking
from recommendations.feature_engineering import (
    FEATURE_NAMES,
    build_feature_vector,
    required_skill_overlap_ratio,
)

_MODEL: Any = None
_MODEL_PATH: Path | None = None


def default_model_path() -> Path:
    return (
        Path(__file__).resolve().parent.parent.parent
        / "models"
        / "custom"
        / "job_ranker.lgb"
    )


def load_ranker(model_path: Path | None = None) -> Any | None:
    global _MODEL, _MODEL_PATH
    path = model_path or default_model_path()
    if _MODEL is not None and _MODEL_PATH == path:
        return _MODEL
    if not path.exists():
        _MODEL = None
        _MODEL_PATH = path
        return None
    try:
        import lightgbm as lgb

        booster = lgb.Booster(model_file=str(path))
        _MODEL = booster
        _MODEL_PATH = path
        return booster
    except Exception:
        _MODEL = None
        _MODEL_PATH = path
        return None


def _overlap_score(user_skills: set[str], required_skills: set[str]) -> float:
    if not required_skills:
        return 0.0
    return required_skill_overlap_ratio(
        {str(item).strip() for item in user_skills},
        {str(item).strip() for item in required_skills},
    ) * 100.0


def _normalize_scores(raw_scores: list[float]) -> list[int]:
    if not raw_scores:
        return []
    minimum = min(raw_scores)
    maximum = max(raw_scores)
    if maximum <= minimum:
        return [int(round(max(0.0, minimum))) for _ in raw_scores]
    scaled = [(score - minimum) / (maximum - minimum) * 100.0 for score in raw_scores]
    return [int(round(value)) for value in scaled]


class JobRanker:
    """Rank job dicts for a user; safe to call without a trained model on disk."""

    def __init__(self, model_path: Path | None = None):
        self.model_path = model_path or default_model_path()
        self.model = load_ranker(self.model_path)

    @property
    def is_available(self) -> bool:
        return self.model is not None

    def rank_jobs(
        self,
        user_skills: Sequence[str],
        jobs: Sequence[dict[str, Any]],
        *,
        user_experience_level: str = "mid",
        preferred_country: str = "Egypt",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        skill_set = {str(item).strip() for item in user_skills if str(item).strip()}
        if not jobs:
            return []

        vectors = []
        overlap_scores = []
        job_required: list[set[str]] = []
        for job in jobs:
            required = {str(item).strip() for item in (job.get("required_skills") or []) if str(item).strip()}
            job_required.append(required)
            vectors.append(
                build_feature_vector(
                    skill_set,
                    job,
                    user_experience_level=user_experience_level,
                    preferred_country=preferred_country,
                )
            )
            overlap_scores.append(_overlap_score(skill_set, required))

        if self.model is not None:
            matrix = np.vstack(vectors)
            raw = self.model.predict(matrix)
            importances = None
            try:
                importances = self.model.feature_importance(importance_type="gain")
            except Exception:
                importances = None
            rank_scores = _normalize_scores([float(item) for item in raw])
        else:
            importances = None
            rank_scores = [int(round(score)) for score in overlap_scores]

        results = []
        for index, job in enumerate(jobs):
            required = job_required[index]
            user_norm = {s.lower(): s for s in skill_set}
            req_norm = {s.lower(): s for s in required}
            common = set(user_norm) & set(req_norm)
            matching = sorted(req_norm[key] for key in common)
            missing = sorted(req_norm[key] for key in req_norm if key not in common)
            explanation = explain_ranking(
                vectors[index],
                matching_skills=matching,
                missing_skills=missing,
                feature_importances=importances,
            )
            overlap_display = int(round(overlap_scores[index]))
            results.append(
                {
                    "job": job,
                    # Overlap % is shown in UI; ranker only changes order.
                    "match_score": overlap_display,
                    "rank_score": rank_scores[index],
                    "matching_skills": matching,
                    "missing_skills": missing,
                    "explanation": explanation,
                    "overlap_score": overlap_display,
                }
            )

        results.sort(key=lambda item: (item["rank_score"], item["overlap_score"]), reverse=True)
        return results[:limit]


def train_ranker_from_labeled_groups(
    feature_matrix: np.ndarray,
    labels: np.ndarray,
    group_sizes: list[int],
    *,
    output_path: Path | None = None,
) -> Path:
    """
    Train LGBMRanker on pseudo-labeled groups (one group per synthetic user).

    labels: relevance grades 0 (worst) .. N (best) per row within each group.
    """
    import lightgbm as lgb

    output = output_path or default_model_path()
    output.parent.mkdir(parents=True, exist_ok=True)

    train_set = lgb.Dataset(
        feature_matrix,
        label=labels,
        group=group_sizes,
        feature_name=list(FEATURE_NAMES),
    )
    params = {
        "objective": "lambdarank",
        "metric": "ndcg",
        "verbosity": -1,
        "learning_rate": 0.05,
        "num_leaves": 15,
        "min_data_in_leaf": 5,
    }
    model = lgb.train(params, train_set, num_boost_round=80)
    model.save_model(str(output))
    load_ranker(output)  # refresh cache
    return output
