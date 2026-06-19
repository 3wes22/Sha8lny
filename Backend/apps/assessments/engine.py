from __future__ import annotations

from dataclasses import asdict
import logging
import re
from statistics import mean
from typing import Any

from apps.assessments.role_graph import CoreDimension, RoleGraph, SubSkill
from apps.core.ai_contracts import GapProfile, SubSkillEvidence


logger = logging.getLogger(__name__)


def _dimension_weight_map(role_graph: RoleGraph) -> dict[str, float]:
    return {dimension.key: dimension.weight for dimension in role_graph.dimensions}


def _subskill_lookup(role_graph: RoleGraph) -> dict[str, SubSkill]:
    lookup: dict[str, SubSkill] = {}
    for dimension in role_graph.dimensions:
        for subskill in dimension.subskills:
            lookup[subskill.key] = subskill
    return lookup


def _coerce_evidence(value: SubSkillEvidence | dict[str, Any]) -> SubSkillEvidence:
    if isinstance(value, SubSkillEvidence):
        return value
    return SubSkillEvidence(**value)


def _assessment_weight(dimension: CoreDimension) -> float:
    return float(dimension.assessment_weight or dimension.weight)


def _dimension_counts_from_questions(questions: list[dict[str, Any]] | None) -> dict[str, int]:
    counts: dict[str, int] = {}
    for question in questions or []:
        if not isinstance(question, dict):
            continue
        dimension_key = str(question.get("dimension_key") or "").strip()
        if dimension_key:
            counts[dimension_key] = counts.get(dimension_key, 0) + 1
    return counts


def _pick_subskill(
    role_graph: RoleGraph,
    dimension_key: str,
    *,
    exclude_subskill_keys: set[str],
) -> SubSkill | None:
    for dimension in role_graph.dimensions:
        if dimension.key != dimension_key:
            continue
        for subskill in sorted(dimension.subskills, key=lambda item: item.target_proficiency, reverse=True):
            if subskill.key not in exclude_subskill_keys:
                return subskill
    return None


class StageAllocator:
    """Select stage targets using assessment weights and cross-stage coverage."""

    @staticmethod
    def allocate_stage_one(role_graph: RoleGraph, limit: int = 5) -> list[SubSkill]:
        return StageAllocator.get_stage_targets(role_graph, stage=1, limit=limit)

    @staticmethod
    def get_stage_targets(
        role_graph: RoleGraph,
        *,
        stage: int,
        limit: int = 5,
        prior_questions: list[dict[str, Any]] | None = None,
        stage_one_dimension_keys: set[str] | None = None,
    ) -> list[SubSkill]:
        global_counts = _dimension_counts_from_questions(prior_questions)
        used_dimensions: set[str] = set()
        used_subskills: set[str] = set()
        selected: list[SubSkill] = []

        def coverage_gap(dimension: CoreDimension) -> int:
            minimum = max(1, int(dimension.min_questions_per_stage))
            return minimum - global_counts.get(dimension.key, 0)

        def dimension_allowed(dimension: CoreDimension) -> bool:
            if dimension.key in used_dimensions:
                return False
            if stage == 2 and stage_one_dimension_keys and dimension.key in stage_one_dimension_keys:
                return False
            return True

        ranked = sorted(role_graph.dimensions, key=_assessment_weight, reverse=True)
        top_half_count = max(1, len(ranked) // 2)
        top_half_keys = {dimension.key for dimension in ranked[:top_half_count]}

        mandatory = [
            dimension
            for dimension in ranked
            if coverage_gap(dimension) > 0 and dimension_allowed(dimension)
        ]
        mandatory.sort(key=lambda dimension: (coverage_gap(dimension), _assessment_weight(dimension)), reverse=True)

        def try_add_dimension(dimension: CoreDimension) -> bool:
            if not dimension_allowed(dimension):
                return False
            if stage == 1 and role_graph.role_key != "fullstack" and dimension.key not in top_half_keys:
                if not mandatory or dimension not in mandatory[:limit]:
                    if coverage_gap(dimension) <= 0:
                        return False
            subskill = _pick_subskill(role_graph, dimension.key, exclude_subskill_keys=used_subskills)
            if subskill is None:
                return False
            selected.append(subskill)
            used_dimensions.add(dimension.key)
            used_subskills.add(subskill.key)
            return True

        for dimension in mandatory:
            if len(selected) >= limit:
                break
            try_add_dimension(dimension)

        if role_graph.role_key == "fullstack" and stage == 1:
            origins_needed = {"frontend": 2, "backend": 2}
            for origin, needed in origins_needed.items():
                have = sum(
                    1
                    for subskill in selected
                    for dimension in role_graph.dimensions
                    if dimension.key == subskill.dimension and (dimension.origin or "") == origin
                )
                while have < needed and len(selected) < limit:
                    candidate = next(
                        (
                            dimension
                            for dimension in ranked
                            if (dimension.origin or "") == origin
                            and dimension_allowed(dimension)
                        ),
                        None,
                    )
                    if candidate is None:
                        break
                    if try_add_dimension(candidate):
                        have += 1
                    else:
                        break

        for dimension in ranked:
            if len(selected) >= limit:
                break
            if coverage_gap(dimension) > 0 or stage == 2:
                try_add_dimension(dimension)

        for dimension in ranked:
            if len(selected) >= limit:
                break
            try_add_dimension(dimension)

        if role_graph.role_key == "fullstack":
            selected = StageAllocator._balance_fullstack_origins(
                role_graph,
                selected,
                limit=limit,
                ranked=ranked,
                used_subskills=used_subskills,
                stage_one_dimension_keys=stage_one_dimension_keys,
            )

        return selected[:limit]

    @staticmethod
    def _balance_fullstack_origins(
        role_graph: RoleGraph,
        selected: list[SubSkill],
        *,
        limit: int,
        ranked: list[CoreDimension],
        used_subskills: set[str],
        stage_one_dimension_keys: set[str] | None,
    ) -> list[SubSkill]:
        def origin_for(subskill: SubSkill) -> str:
            for dimension in role_graph.dimensions:
                if dimension.key == subskill.dimension:
                    return dimension.origin or ""
            return ""

        def count_origin(origin: str) -> int:
            return sum(1 for subskill in selected if origin_for(subskill) == origin)

        for origin in ("frontend", "backend"):
            while count_origin(origin) < 2 and len(selected) < limit:
                replacement = next(
                    (
                        dimension
                        for dimension in ranked
                        if (dimension.origin or "") == origin
                        and dimension.key not in {item.dimension for item in selected}
                        and (not stage_one_dimension_keys or dimension.key not in stage_one_dimension_keys)
                    ),
                    None,
                )
                if replacement is None:
                    break
                subskill = _pick_subskill(role_graph, replacement.key, exclude_subskill_keys=used_subskills)
                if subskill is None:
                    break
                if selected:
                    selected[-1] = subskill
                else:
                    selected.append(subskill)
                used_subskills.add(subskill.key)
        return selected


class AnswerScorer:
    """Convert stage responses into deterministic subskill evidence."""

    @staticmethod
    def _normalize_text(value: Any) -> str:
        return re.sub(r"\s+", " ", str(value or "").strip().lower())

    @classmethod
    def _selected_option_ids(cls, answer: Any, options: list[dict[str, Any]]) -> list[str]:
        option_lookup: dict[str, str] = {}
        for option in options:
            option_id = str(option.get("id") or option.get("value") or "").strip()
            if not option_id:
                continue
            option_lookup[cls._normalize_text(option_id)] = option_id
            option_lookup[cls._normalize_text(option.get("value"))] = option_id
            option_lookup[cls._normalize_text(option.get("label"))] = option_id

        if isinstance(answer, list):
            candidates = answer
        elif answer in (None, ""):
            candidates = []
        else:
            candidates = [answer]

        selected: list[str] = []
        for candidate in candidates:
            option_id = option_lookup.get(cls._normalize_text(candidate))
            if option_id and option_id not in selected:
                selected.append(option_id)
        return selected

    @classmethod
    def _legacy_score_answer(cls, question: dict[str, Any], answer: Any) -> tuple[float, float]:
        options = question.get("options") or []
        if isinstance(answer, str):
            stripped = answer.strip()
            for option in options:
                if stripped in {str(option.get("value", "")), str(option.get("label", ""))}:
                    return float(option.get("score", 3)), 0.85
            if stripped.isdigit():
                return max(0.0, min(5.0, float(stripped))), 0.78
            if len(stripped) >= 80:
                return 4.0, 0.68
            if len(stripped) >= 30:
                return 3.0, 0.6
            if len(stripped) >= 10:
                return 2.0, 0.52
            return 1.0, 0.45

        if isinstance(answer, (int, float)):
            return max(0.0, min(5.0, float(answer))), 0.78

        return 0.0, 0.35

    @classmethod
    def _score_answer(cls, question: dict[str, Any], answer: Any) -> tuple[float, float]:
        question_type = str(question.get("question_type") or "").strip()
        answer_key = question.get("answer_key") if isinstance(question.get("answer_key"), dict) else {}
        options = question.get("options") if isinstance(question.get("options"), list) else []

        if question_type == "single_choice" and answer_key.get("correct_option_ids"):
            selected = cls._selected_option_ids(answer, options)
            if not selected:
                return 0.0, 0.45
            return (5.0, 0.9) if selected[0] in set(answer_key["correct_option_ids"]) else (1.0, 0.85)

        if question_type == "multi_select" and answer_key.get("correct_option_ids"):
            selected = set(cls._selected_option_ids(answer, options))
            if not selected:
                return 0.0, 0.45
            correct = set(answer_key["correct_option_ids"])
            true_positive = len(selected & correct)
            precision = true_positive / len(selected)
            recall = true_positive / len(correct) if correct else 0.0
            f1_score = 0.0
            if precision + recall > 0:
                f1_score = (2 * precision * recall) / (precision + recall)
            return round(1.0 + (4.0 * f1_score), 2), 0.84

        if question_type == "open_ended":
            score, confidence, _method = cls.score_open_ended(question, answer)
            return score, confidence

        return cls._legacy_score_answer(question, answer)

    @classmethod
    def score_answer_with_method(
        cls, question: dict[str, Any], answer: Any
    ) -> tuple[float, float, str]:
        """Score an answer and report the scoring method used.

        Open-ended answers route through :meth:`score_open_ended` (LLM rubric
        when enabled, else keyword coverage); closed items are deterministic.
        """
        if str(question.get("question_type") or "").strip() == "open_ended":
            return cls.score_open_ended(question, answer)
        score, confidence = cls._score_answer(question, answer)
        return score, confidence, "deterministic"

    @classmethod
    def score_open_ended(
        cls, question: dict[str, Any], answer: Any
    ) -> tuple[float, float, str]:
        """Score an open-ended answer, preferring an LLM rubric when available.

        When ``ASSESSMENT_RUBRIC_LLM_ENABLED`` is set and the item carries
        ``expected_concepts``, Gemini grades the answer 1-5 against a rubric
        prompt. Any failure (disabled flag, missing key, API/parse error) falls
        back to the deterministic keyword-coverage scorer — the demo never
        breaks on a dead ``GEMINI_API_KEY``. Returns ``(score, confidence,
        scoring_method)`` where ``scoring_method`` is ``"llm_rubric"`` or
        ``"keyword_coverage"``.
        """
        from apps.core import ai_settings

        answer_key = question.get("answer_key") if isinstance(question.get("answer_key"), dict) else {}
        normalized_answer = cls._normalize_text(answer)

        if (
            normalized_answer
            and ai_settings.ASSESSMENT_RUBRIC_LLM_ENABLED
            and answer_key.get("expected_concepts")
        ):
            try:
                score, confidence = cls._score_open_ended_llm_rubric(question, answer)
                return score, confidence, "llm_rubric"
            except Exception as error:  # pragma: no cover - exercised via mocked failure
                logger.warning("LLM rubric scoring failed, using keyword fallback: %s", error)

        score, confidence = cls._score_open_ended_keyword(question, answer)
        return score, confidence, "keyword_coverage"

    @classmethod
    def _score_open_ended_llm_rubric(
        cls, question: dict[str, Any], answer: Any
    ) -> tuple[float, float]:
        """Grade an open-ended answer 1-5 with Gemini against expected concepts."""
        from apps.core.gemma_client import GemmaClient

        answer_key = question.get("answer_key") if isinstance(question.get("answer_key"), dict) else {}
        expected = [str(c).strip() for c in answer_key.get("expected_concepts", []) if str(c).strip()]
        forbidden = [str(c).strip() for c in answer_key.get("forbidden_concepts", []) if str(c).strip()]
        stem = str(question.get("stem") or question.get("question_text") or question.get("question") or "").strip()

        prompt = (
            "Grade the candidate's answer to a technical assessment question on a 1-5 scale.\n"
            "5 = covers all key concepts correctly; 3 = partial coverage; 1 = off-topic or wrong.\n\n"
            f"Question: {stem}\n"
            f"Expected concepts: {', '.join(expected) or 'n/a'}\n"
            f"Concepts that indicate a misconception: {', '.join(forbidden) or 'none'}\n\n"
            f"Candidate answer: {str(answer).strip()}\n\n"
            'Return JSON: {"score": <int 1-5>, "reasoning": "<one sentence>"}.'
        )

        result = GemmaClient(task_type="career_matching", max_output_tokens=200).generate_structured(
            prompt=prompt,
            system="You are a strict but fair technical grader. Output only the requested JSON.",
            required_keys=("score",),
        )
        payload = result.payload if isinstance(result.payload, dict) else {}
        raw_score = payload.get("score")
        score = max(1.0, min(5.0, float(raw_score)))
        return round(score, 2), 0.85

    @classmethod
    def _score_open_ended_keyword(
        cls, question: dict[str, Any], answer: Any
    ) -> tuple[float, float]:
        """Deterministic open-ended scoring: rubric dimensions or concept coverage."""
        answer_key = question.get("answer_key") if isinstance(question.get("answer_key"), dict) else {}
        rubric = question.get("rubric")
        if isinstance(rubric, dict) and rubric.get("scoring_dimensions"):
            return cls._score_open_ended_with_rubric(question, answer, rubric)

        if answer_key.get("expected_concepts"):
            normalized_answer = cls._normalize_text(answer)
            if not normalized_answer:
                return 0.0, 0.45

            expected_concepts = [
                cls._normalize_text(concept)
                for concept in answer_key.get("expected_concepts", [])
                if cls._normalize_text(concept)
            ]
            hits = sum(1 for concept in expected_concepts if concept in normalized_answer)
            coverage = hits / len(expected_concepts) if expected_concepts else 0.0
            forbidden_hits = sum(
                1
                for concept in answer_key.get("forbidden_concepts", [])
                if cls._normalize_text(concept) in normalized_answer
            )
            coverage = max(0.0, coverage - (0.2 * forbidden_hits))
            confidence = 0.72 if len(normalized_answer) >= 40 else 0.64
            return round(1.0 + (4.0 * coverage), 2), confidence

        return cls._legacy_score_answer(question, answer)

    @classmethod
    def _score_open_ended_with_rubric(
        cls,
        question: dict[str, Any],
        answer: Any,
        rubric: dict[str, Any],
    ) -> tuple[float, float]:
        normalized_answer = cls._normalize_text(answer)
        if not normalized_answer:
            return 0.0, 0.45

        for fail_phrase in rubric.get("auto_fail_if") or []:
            if cls._normalize_text(fail_phrase) in normalized_answer:
                return 1.0, 0.9

        required = [
            cls._normalize_text(concept)
            for concept in rubric.get("required_concepts") or []
            if cls._normalize_text(concept)
        ]
        if required:
            required_hits = sum(1 for concept in required if concept in normalized_answer)
            if required_hits < len(required):
                partial = required_hits / len(required)
                return round(1.0 + (2.0 * partial), 2), 0.7

        dimensions = rubric.get("scoring_dimensions") or []
        concept_pool = [
            cls._normalize_text(concept)
            for concept in (rubric.get("required_concepts") or [])
            + (rubric.get("bonus_concepts") or [])
            + (question.get("answer_key") or {}).get("expected_concepts", [])
            if cls._normalize_text(concept)
        ]
        if concept_pool:
            concept_hits = sum(1 for concept in concept_pool if concept in normalized_answer)
            coverage = concept_hits / len(concept_pool)
        else:
            weighted_score = 0.0
            total_weight = 0.0
            for dimension in dimensions:
                if not isinstance(dimension, dict):
                    continue
                weight = float(dimension.get("weight") or 0)
                label = cls._normalize_text(dimension.get("dimension") or "")
                if not weight or not label:
                    continue
                total_weight += weight
                if label in normalized_answer:
                    weighted_score += weight
                else:
                    tokens = [token for token in label.split() if len(token) > 4]
                    if tokens and any(token in normalized_answer for token in tokens):
                        weighted_score += weight * 0.6
            coverage = weighted_score / total_weight if total_weight > 0 else 0.5

        bonus = rubric.get("bonus_concepts") or []
        bonus_hits = sum(
            1
            for concept in bonus
            if cls._normalize_text(concept) in normalized_answer
        )
        if bonus_hits:
            coverage = min(1.0, coverage + (0.05 * bonus_hits))

        confidence = 0.78 if len(normalized_answer) >= 80 else 0.7
        return round(1.0 + (4.0 * coverage), 2), confidence

    @staticmethod
    def score_stage(
        role_graph: RoleGraph,
        questions: list[dict[str, Any]],
        responses: list[dict[str, Any]],
    ) -> list[SubSkillEvidence]:
        response_map = {
            str(response.get("question_id")): response.get("answer")
            for response in responses
        }
        subskills = _subskill_lookup(role_graph)
        scored: list[SubSkillEvidence] = []

        for question in questions:
            subskill = subskills[question["subskill_key"]]
            observed_level, confidence, scoring_method = AnswerScorer.score_answer_with_method(
                question,
                response_map.get(str(question.get("id"))),
            )
            # Record how open-ended answers were graded (llm_rubric vs
            # keyword_coverage) on the question's persisted metadata.
            if str(question.get("question_type") or "").strip() == "open_ended":
                generation_metadata = question.get("generation_metadata")
                if not isinstance(generation_metadata, dict):
                    generation_metadata = {}
                    question["generation_metadata"] = generation_metadata
                generation_metadata["scoring_method"] = scoring_method
            stage = int(question.get("stage") or 1)
            if stage == 2:
                confidence = min(0.95, confidence + 0.08)

            evidence_strength = "strong"
            if confidence < 0.75:
                evidence_strength = "moderate"
            if confidence < 0.6:
                evidence_strength = "weak"

            scored.append(
                SubSkillEvidence(
                    subskill_key=subskill.key,
                    dimension_key=subskill.dimension,
                    observed_level=round(observed_level, 2),
                    target_level=subskill.target_proficiency,
                    gap=round(max(0.0, subskill.target_proficiency - observed_level), 2),
                    confidence=round(confidence, 2),
                    evidence_strength=evidence_strength,
                )
            )

        return scored


class GapProfileBuilder:
    """Build the stage-one gap profile used to drive stage two."""

    @staticmethod
    def build(
        role_graph: RoleGraph,
        evidence: list[SubSkillEvidence | dict[str, Any]],
    ) -> GapProfile:
        normalized = [_coerce_evidence(item) for item in evidence]
        dimension_weights = _dimension_weight_map(role_graph)
        ranked = sorted(
            normalized,
            key=lambda item: (item.gap * dimension_weights.get(item.dimension_key, 0.0), -item.confidence),
            reverse=True,
        )
        observed_ratio = [
            min(1.0, (item.observed_level / item.target_level) if item.target_level else 0.0)
            for item in normalized
        ]

        return GapProfile(
            role_key=role_graph.role_key,
            subskill_evidence=normalized,
            high_priority_gaps=[item.subskill_key for item in ranked[:5]],
            uncertain_areas=[
                item.subskill_key
                for item in normalized
                if item.confidence < 0.65 or item.evidence_strength == "weak"
            ],
            overall_calibration=round(mean(observed_ratio) * 100, 2) if observed_ratio else 0.0,
        )


class Stage2Allocator:
    """Choose the targeted follow-up areas for stage two."""

    @staticmethod
    def allocate_stage_two(
        role_graph: RoleGraph,
        gap_profile: GapProfile,
        limit: int = 5,
        *,
        stage_one_questions: list[dict[str, Any]] | None = None,
    ) -> list[SubSkill]:
        stage_one_dimension_keys = {
            str(question.get("dimension_key") or "").strip()
            for question in stage_one_questions or []
            if isinstance(question, dict) and question.get("dimension_key")
        }
        subskills = _subskill_lookup(role_graph)
        priority_keys: list[str] = []

        def add(key: str) -> None:
            if key in subskills and key not in priority_keys:
                priority_keys.append(key)

        for key in gap_profile.high_priority_gaps:
            add(key)
        for key in gap_profile.uncertain_areas:
            add(key)

        coverage_targets = StageAllocator.get_stage_targets(
            role_graph,
            stage=2,
            limit=limit,
            prior_questions=stage_one_questions,
            stage_one_dimension_keys=stage_one_dimension_keys,
        )
        ordered_keys = [target.key for target in coverage_targets]
        for key in priority_keys:
            if key not in ordered_keys:
                ordered_keys.append(key)
        return [subskills[key] for key in ordered_keys[:limit] if key in subskills]


def merge_evidence(
    role_graph: RoleGraph,
    stage_one_evidence: list[SubSkillEvidence | dict[str, Any]],
    stage_two_evidence: list[SubSkillEvidence | dict[str, Any]],
) -> list[SubSkillEvidence]:
    merged: dict[str, SubSkillEvidence] = {
        item.subskill_key: item
        for item in [_coerce_evidence(evidence) for evidence in stage_one_evidence]
    }
    for evidence in [_coerce_evidence(item) for item in stage_two_evidence]:
        previous = merged.get(evidence.subskill_key)
        if not previous:
            merged[evidence.subskill_key] = evidence
            continue

        observed_level = round((previous.observed_level + evidence.observed_level) / 2, 2)
        confidence = round(max(previous.confidence, evidence.confidence), 2)
        evidence_strength = evidence.evidence_strength if confidence >= previous.confidence else previous.evidence_strength
        merged[evidence.subskill_key] = SubSkillEvidence(
            subskill_key=evidence.subskill_key,
            dimension_key=evidence.dimension_key,
            observed_level=observed_level,
            target_level=evidence.target_level,
            gap=round(max(0.0, evidence.target_level - observed_level), 2),
            confidence=confidence,
            evidence_strength=evidence_strength,
        )

    dimension_weights = _dimension_weight_map(role_graph)
    return sorted(
        merged.values(),
        key=lambda item: (item.gap * dimension_weights.get(item.dimension_key, 0.0), -item.confidence),
        reverse=True,
    )


def evidence_to_dicts(evidence: list[SubSkillEvidence]) -> list[dict[str, Any]]:
    return [asdict(item) for item in evidence]
