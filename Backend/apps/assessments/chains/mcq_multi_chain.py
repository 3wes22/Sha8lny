from __future__ import annotations

from apps.assessments.chains.base import BaseQuestionChain
from apps.assessments.chains.enums import QuestionType


class MCQMultiChain(BaseQuestionChain):
    question_type = QuestionType.MCQ_MULTI

    @property
    def helper(self) -> str | None:
        return "Select all that apply."

    def instruction_block(self) -> str:
        return (
            "Generate 2 or 3 correct answers. "
            'The question stem must include "Select all that apply." '
            "Distractors should be things developers commonly do that are ineffective or harmful "
            "in this scenario. "
            "Write 5 options. "
            'question_type must be "multi_select". '
            "answer_key.correct_option_ids must contain 2 or 3 option ids."
        )
