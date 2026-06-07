from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from apps.assessments.chains.enums import QuestionType


# `helper` is the candidate-facing sub-instruction shown below the stem.
# It is type-scoped: set by the question's generating chain, never shared.
# Equivalent to what the architecture spec calls `candidate_instruction`.
# Do not rename — frontend is wired to this field name.


class BaseQuestionChain(ABC):
    """Isolated prompt template for one question type."""

    question_type: QuestionType
    template_version: str = "v1"

    @property
    @abstractmethod
    def helper(self) -> str | None:
        """Type-scoped candidate instruction; None means no sub-instruction."""

    @abstractmethod
    def instruction_block(self) -> str:
        """Type-specific generation rules (never shared across chains)."""

    def build_slot_context(self, slot: dict[str, Any]) -> dict[str, str]:
        return {
            "skill_area": str(slot.get("dimension_key") or slot.get("subskill_key") or ""),
            "seniority_level": self._seniority_from_difficulty(slot.get("difficulty")),
            "scenario_context": str(slot.get("scenario_hint") or ""),
            "competency": str(slot.get("competency") or ""),
            "learning_objective": str(slot.get("learning_objective_hint") or ""),
            "stage": str(slot.get("stage") or 1),
            "subskill_key": str(slot.get("subskill_key") or ""),
            "question_type": str(slot.get("question_type") or ""),
            "focus": str(slot.get("focus") or ""),
        }

    @staticmethod
    def _seniority_from_difficulty(difficulty: Any) -> str:
        try:
            level = int(difficulty)
        except (TypeError, ValueError):
            return "mid"
        if level <= 2:
            return "junior"
        if level >= 4:
            return "senior"
        return "mid"

    def build_fragment(self, slot: dict[str, Any]) -> str:
        """Render an isolated fragment for batched generation (one slot)."""
        ctx = self.build_slot_context(slot)
        return (
            f"For slot {slot.get('slot', '?')} ({self.question_type.value} / {ctx['subskill_key']}):\n"
            f"{self.instruction_block()}\n"
            f"Competency: {ctx['competency']}\n"
            f"Learning objective hint: {ctx['learning_objective']}\n"
            f"Seniority target: {ctx['seniority_level']}\n"
            f"Stage: {ctx['stage']}\n"
            f"Focus: {ctx['focus']}\n"
            f"Skill area (dimension): {ctx['skill_area']}\n"
            "Do not embed sub-instructions in the stem; stem must stand alone.\n"
        )

    def build_prompt(self, slot: dict[str, Any]) -> str:
        """Full prompt for per-question generation mode."""
        ctx = self.build_slot_context(slot)
        return (
            f"Generate one {self.question_type.value} assessment question.\n"
            f"{self.instruction_block()}\n"
            f"subskill_key: {ctx['subskill_key']}\n"
            f"competency: {ctx['competency']}\n"
            f"seniority_level: {ctx['seniority_level']}\n"
            f"stage: {ctx['stage']}\n"
            'Return a single question object inside a top-level JSON field "questions" with one item.\n'
        )
