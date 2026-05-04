from __future__ import annotations

from dataclasses import asdict
import re
from statistics import mean
from typing import Any

from apps.assessments.role_graph import RoleGraph, SubSkill
from apps.core.ai_contracts import GapProfile, SubSkillEvidence


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


class StageAllocator:
    """Pick the stage-one calibration targets from the role graph."""

    @staticmethod
    def allocate_stage_one(role_graph: RoleGraph, limit: int = 5) -> list[SubSkill]:
        selected: list[SubSkill] = []
        seen: set[str] = set()

        for dimension in role_graph.dimensions:
            for subskill in dimension.subskills:
                if subskill.key in seen:
                    continue
                selected.append(subskill)
                seen.add(subskill.key)
                break
            if len(selected) == limit:
                return selected

        ranked_dimensions = sorted(role_graph.dimensions, key=lambda dimension: dimension.weight, reverse=True)
        while len(selected) < limit:
            added_this_round = False
            for dimension in ranked_dimensions:
                for subskill in dimension.subskills:
                    if subskill.key in seen:
                        continue
                    selected.append(subskill)
                    seen.add(subskill.key)
                    added_this_round = True
                    break
                if len(selected) == limit:
                    return selected
            if not added_this_round:
                break

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

        if question_type == "open_ended" and answer_key.get("expected_concepts"):
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
            observed_level, confidence = AnswerScorer._score_answer(
                question,
                response_map.get(str(question.get("id"))),
            )
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
    def allocate_stage_two(role_graph: RoleGraph, gap_profile: GapProfile, limit: int = 5) -> list[SubSkill]:
        subskills = _subskill_lookup(role_graph)
        dimension_weights = _dimension_weight_map(role_graph)
        ordered_keys: list[str] = []

        def add(key: str) -> None:
            if key in subskills and key not in ordered_keys:
                ordered_keys.append(key)

        for key in gap_profile.high_priority_gaps:
            add(key)
        for key in gap_profile.uncertain_areas:
            add(key)
        for key in gap_profile.high_priority_gaps:
            for prerequisite in subskills[key].prerequisites:
                add(prerequisite)

        remaining = sorted(
            subskills.values(),
            key=lambda subskill: (
                dimension_weights.get(subskill.dimension, 0.0),
                subskill.target_proficiency,
            ),
            reverse=True,
        )
        for subskill in remaining:
            add(subskill.key)
            if len(ordered_keys) == limit:
                break

        return [subskills[key] for key in ordered_keys[:limit]]


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
