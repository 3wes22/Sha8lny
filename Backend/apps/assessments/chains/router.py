from __future__ import annotations

import json
import logging
from typing import Any

from apps.assessments.chains.base import BaseQuestionChain
from apps.assessments.chains.debugging_multi_chain import DebuggingMultiChain
from apps.assessments.chains.debugging_single_chain import DebuggingSingleChain
from apps.assessments.chains.enums import QuestionType, question_type_to_semantic
from apps.assessments.chains.mcq_multi_chain import MCQMultiChain
from apps.assessments.chains.mcq_single_chain import MCQSingleChain
from apps.assessments.chains.open_ended_chain import OpenEndedChain
from apps.assessments.chains.stem_validator import resolve_chain_question_type
from apps.assessments.role_graph import RoleGraph, SubSkill
from apps.assessments.role_graph_taxonomy import is_debugging_dimension

logger = logging.getLogger(__name__)

BLEED_PHRASES = (
    "blast radius",
    "failing boundary",
    "narrows risk",
    "change set",
    "gather evidence",
    "diagnosis",
    "narrowing",
)


class QuestionTypeRouter:
    """Routes generation to isolated per-type chains."""

    def __init__(self) -> None:
        self._chains: dict[QuestionType, BaseQuestionChain] = {}

    def register(self, question_type: QuestionType, chain: BaseQuestionChain) -> None:
        self._chains[question_type] = chain

    def chain_for_slot(
        self,
        slot: dict[str, Any],
        *,
        subskill: SubSkill | None = None,
        role_graph: RoleGraph | None = None,
    ) -> BaseQuestionChain:
        dimension_key = str(
            slot.get("dimension_key")
            or (subskill.dimension if subskill else "")
            or ""
        )
        semantic = str(slot.get("question_type") or "single_choice")
        chain_type = resolve_chain_question_type(
            semantic_type=semantic,
            dimension_key=dimension_key,
            blueprint=slot,
        )
        if chain_type not in self._chains:
            chain_type = QuestionType.MCQ_SINGLE
        return self._chains[chain_type]

    def build_batch_prompt(
        self,
        *,
        role_label: str,
        stage: int,
        slots: list[dict[str, Any]],
        subskill_lookup: dict[str, SubSkill] | None = None,
    ) -> str:
        lookup = subskill_lookup or {}
        fragments: list[str] = []
        for slot in slots:
            subskill = lookup.get(str(slot.get("subskill_key") or ""))
            chain = self.chain_for_slot(slot, subskill=subskill)
            fragments.append(chain.build_fragment({**slot, "stage": stage}))

        return (
            f"Generate exactly {len(slots)} structured assessment questions for "
            f"{role_label} (stage {stage}).\n"
            'Return a top-level JSON object with a "questions" array containing exactly '
            f"{len(slots)} items in the same slot order.\n"
            "Each slot below has its own isolated instructions — follow only the block for that slot.\n"
            "Do not add sub-instructions to stems. Stems must stand alone.\n"
            "Do not use debugging or evidence-gathering framing unless the slot says debugging.\n\n"
            + "\n".join(fragments)
            + f"\n\nBlueprints:\n{json.dumps(slots, ensure_ascii=True)}\n"
        )

    def assign_helper(
        self,
        question: dict[str, Any],
        *,
        subskill: SubSkill | None = None,
        blueprint: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        slot = {
            "question_type": question.get("question_type"),
            "subskill_key": question.get("subskill_key"),
            "dimension_key": question.get("dimension_key"),
            "chain_question_type": (blueprint or {}).get("chain_question_type")
            or (question.get("generation_metadata") or {}).get("chain_question_type"),
        }
        chain = self.chain_for_slot(slot, subskill=subskill)
        helper = chain.helper
        if helper:
            question["helper"] = helper
        else:
            question.pop("helper", None)
        gen_meta = dict(question.get("generation_metadata") or {})
        gen_meta["chain_question_type"] = chain.question_type.value
        question["generation_metadata"] = gen_meta
        return question

    def is_debugging_chain_type(self, chain_type: QuestionType) -> bool:
        return chain_type in {QuestionType.DEBUGGING_SINGLE, QuestionType.DEBUGGING_MULTI}

    @staticmethod
    def contains_bleed_phrase(text: str) -> bool:
        lowered = (text or "").lower()
        return any(phrase in lowered for phrase in BLEED_PHRASES)


def build_default_router() -> QuestionTypeRouter:
    router = QuestionTypeRouter()
    router.register(QuestionType.MCQ_SINGLE, MCQSingleChain())
    router.register(QuestionType.MCQ_MULTI, MCQMultiChain())
    router.register(QuestionType.OPEN_ENDED, OpenEndedChain())
    router.register(QuestionType.DEBUGGING_SINGLE, DebuggingSingleChain())
    router.register(QuestionType.DEBUGGING_MULTI, DebuggingMultiChain())
    return router
