from __future__ import annotations

from apps.assessments.chains.enums import QuestionType
from apps.assessments.chains.mcq_single_chain import MCQSingleChain


class DebuggingSingleChain(MCQSingleChain):
    question_type = QuestionType.DEBUGGING_SINGLE

    @property
    def helper(self) -> str | None:
        return "Select the single best first action."

    def instruction_block(self) -> str:
        return (
            "This question tests systematic debugging thinking with a SINGLE best first action. "
            "The stem must ask for the SINGLE best or most important first action. "
            "Use phrasing like 'What is the most effective first step to...' or "
            "'What should the developer do first when...'. "
            "Exactly one option is correct. "
            "The other three options must be actions that seem reasonable but are premature, "
            "destructive, or skip the evidence-gathering phase. "
            'question_type must be "single_choice". '
            "answer_key.correct_option_ids must contain exactly one option id. "
            "Do not embed the sub-instruction in the stem."
        )
