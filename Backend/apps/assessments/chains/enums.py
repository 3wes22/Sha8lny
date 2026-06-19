from __future__ import annotations

from enum import Enum


class QuestionType(str, Enum):
    MCQ_SINGLE = "mcq_single"
    MCQ_MULTI = "mcq_multi"
    OPEN_ENDED = "open_ended"
    DEBUGGING_SINGLE = "debugging_single"
    DEBUGGING_MULTI = "debugging_multi"
    CODE_REVIEW = "code_review"
    ORDERING = "ordering"


SEMANTIC_TO_QUESTION_TYPE = {
    "single_choice": QuestionType.MCQ_SINGLE,
    "multi_select": QuestionType.MCQ_MULTI,
    "open_ended": QuestionType.OPEN_ENDED,
}

QUESTION_TYPE_TO_SEMANTIC = {
    QuestionType.MCQ_SINGLE: "single_choice",
    QuestionType.MCQ_MULTI: "multi_select",
    QuestionType.OPEN_ENDED: "open_ended",
    QuestionType.DEBUGGING_SINGLE: "single_choice",
    QuestionType.DEBUGGING_MULTI: "multi_select",
}


def semantic_type_to_question_type(semantic: str) -> QuestionType:
    return SEMANTIC_TO_QUESTION_TYPE.get(str(semantic or "").strip(), QuestionType.MCQ_SINGLE)


def question_type_to_semantic(question_type: QuestionType) -> str:
    return QUESTION_TYPE_TO_SEMANTIC.get(question_type, "single_choice")
