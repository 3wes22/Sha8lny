from __future__ import annotations

from apps.assessments.chains.enums import QuestionType
from apps.assessments.chains.mcq_multi_chain import MCQMultiChain


class DebuggingMultiChain(MCQMultiChain):
    question_type = QuestionType.DEBUGGING_MULTI

    @property
    def helper(self) -> str | None:
        return (
            "Select the action(s) that gather diagnostic evidence before making any changes."
        )

    def instruction_block(self) -> str:
        return (
            "This question tests systematic debugging with MULTIPLE valid evidence-gathering actions. "
            "The stem must ask which COMBINATION of actions the developer would take. "
            "Use phrasing like 'Which of the following steps would help diagnose...' or "
            "'Select all actions that would help identify the root cause of...'. "
            "Two or three options must be correct. "
            "Correct options should represent the evidence-gathering phase. "
            "Incorrect options should represent premature fixes or changes that destroy evidence. "
            'question_type must be "multi_select". '
            'The stem must include "Select all that apply." '
            "answer_key.correct_option_ids must contain 2 or 3 option ids."
        )
