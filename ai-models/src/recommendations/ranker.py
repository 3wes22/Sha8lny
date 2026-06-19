"""
LightGBM job ranker — loads committed model or falls back to overlap sort.
"""

from __future__ import annotations

import math
import tempfile
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


# ---------------------------------------------------------------------------
# Ranking-quality evaluation (held-out group split, baselines)
# ---------------------------------------------------------------------------
# Relevance grades here are weak/pseudo-labels (see scripts/train_job_ranker.py),
# not human ground truth. The harness still gives a defensible, reproducible
# read on whether the learned ranker beats trivial baselines.

# A pair counts as "relevant" for MAP at grade >= 2 (graded labels are 0..3,
# where 2 = solid skill overlap and 3 = overlap + role-title match).
DEFAULT_RELEVANT_GRADE = 2.0


def _dcg(relevances: Sequence[float], k: int) -> float:
    return sum(rel / math.log2(index + 2) for index, rel in enumerate(list(relevances)[:k]))


def ndcg_at_k(ordered_relevances: Sequence[float], k: int) -> float:
    """Normalized DCG@k for relevance grades ordered by predicted rank (best first)."""
    ideal = sorted(ordered_relevances, reverse=True)
    idcg = _dcg(ideal, k)
    if idcg <= 0:
        return 0.0
    return _dcg(ordered_relevances, k) / idcg


def average_precision(
    ordered_relevances: Sequence[float],
    *,
    relevant_grade: float = DEFAULT_RELEVANT_GRADE,
) -> float:
    """Average precision for a single ranked list (grades >= relevant_grade are hits)."""
    n_relevant = sum(1 for rel in ordered_relevances if rel >= relevant_grade)
    if n_relevant == 0:
        return 0.0
    hits = 0
    running = 0.0
    for index, rel in enumerate(ordered_relevances):
        if rel >= relevant_grade:
            hits += 1
            running += hits / (index + 1)
    return running / n_relevant


def _order_relevances_by_scores(
    relevances: Sequence[float],
    scores: Sequence[float],
) -> list[float]:
    """Return true relevance grades ordered by descending predicted score (stable)."""
    order = np.argsort(-np.asarray(scores, dtype=float), kind="stable")
    return [float(relevances[index]) for index in order]


def train_and_evaluate(
    feature_matrix: np.ndarray,
    labels: np.ndarray,
    group_sizes: list[int],
    *,
    seed: int = 42,
    ks: Sequence[int] = (5, 10),
) -> dict[str, Any]:
    """Leave-one-group-out evaluation reporting NDCG@k / MAP vs. baselines.

    Each group (one synthetic user) is held out *whole* in turn; the model trains
    on the remaining groups and is scored on the held-out one. With only a handful
    of groups this uses the data far better than a single split and gives stable
    metrics. No user leaks across train/test, and these throwaway models (written
    to temp files) never overwrite the committed production model.
    """
    labels = np.asarray(labels, dtype=float)
    n_groups = len(group_sizes)
    if n_groups < 2:
        raise ValueError("Need at least 2 groups for leave-one-group-out evaluation")

    bounds = np.cumsum([0, *group_sizes])

    def group_slice(group_index: int) -> slice:
        return slice(int(bounds[group_index]), int(bounds[group_index + 1]))

    import lightgbm as lgb

    overlap_index = FEATURE_NAMES.index("required_skill_overlap_ratio")
    score_rng = np.random.default_rng(seed + 1)

    rankers = ("lightgbm", "overlap_baseline", "random_baseline")
    ndcg_acc: dict[str, dict[int, list[float]]] = {r: {k: [] for k in ks} for r in rankers}
    map_acc: dict[str, list[float]] = {r: [] for r in rankers}

    for test_group in range(n_groups):
        train_groups = [g for g in range(n_groups) if g != test_group]
        train_rows = np.vstack([feature_matrix[group_slice(g)] for g in train_groups])
        train_labels = np.concatenate([labels[group_slice(g)] for g in train_groups])
        train_group_sizes = [group_sizes[g] for g in train_groups]

        with tempfile.NamedTemporaryFile(suffix=".lgb", delete=False) as handle:
            tmp_path = Path(handle.name)
        try:
            train_ranker_from_labeled_groups(
                train_rows, train_labels, train_group_sizes, output_path=tmp_path
            )
            booster = lgb.Booster(model_file=str(tmp_path))
        finally:
            tmp_path.unlink(missing_ok=True)

        group_features = feature_matrix[group_slice(test_group)]
        group_labels = labels[group_slice(test_group)]
        score_sets = {
            "lightgbm": booster.predict(group_features),
            "overlap_baseline": group_features[:, overlap_index],
            "random_baseline": score_rng.random(len(group_labels)),
        }
        for ranker_name, scores in score_sets.items():
            ordered = _order_relevances_by_scores(group_labels, scores)
            for k in ks:
                ndcg_acc[ranker_name][k].append(ndcg_at_k(ordered, k))
            map_acc[ranker_name].append(average_precision(ordered))

    def _mean(values: list[float]) -> float:
        return round(float(np.mean(values)), 4) if values else 0.0

    metrics: dict[str, dict[str, float]] = {}
    for k in ks:
        metrics[f"ndcg@{k}"] = {r: _mean(ndcg_acc[r][k]) for r in rankers}
    metrics["map"] = {r: _mean(map_acc[r]) for r in rankers}

    # Restore the committed production model in the in-process cache (the loop
    # left it pointing at the last throwaway fold).
    load_ranker(default_model_path())

    return {
        "evaluation": "leave-one-group-out",
        "n_groups": n_groups,
        "n_folds": n_groups,
        "seed": seed,
        "features": list(FEATURE_NAMES),
        "relevant_grade_for_map": DEFAULT_RELEVANT_GRADE,
        "label_provenance": "weak-supervision (pseudo-label), not ground truth",
        "metrics": metrics,
    }
