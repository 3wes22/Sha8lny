from __future__ import annotations

from apps.assessments.chains.base import BaseQuestionChain
from apps.assessments.chains.enums import QuestionType


class OpenEndedChain(BaseQuestionChain):
    question_type = QuestionType.OPEN_ENDED

    @property
    def helper(self) -> str | None:
        return (
            "Write 150-300 words. Include specific techniques and explicit tradeoffs."
        )

    def instruction_block(self) -> str:
        return (
            "Generate an open-ended question that requires depth of thinking, not recall. "
            "Every open-ended question must include: "
            "(1) a SPECIFIC component or system being designed (name concrete UI/system parts), "
            "(2) at least TWO NAMED TECHNICAL CONSTRAINTS, "
            "(3) an explicit instruction to COMPARE TWO APPROACHES and state tradeoffs. "
            "Follow this pattern: "
            "'You are building [SPECIFIC SYSTEM]. It requires [CONSTRAINT 1] and [CONSTRAINT 2]. "
            "Describe your strategy, comparing [TECHNIQUE A] vs [TECHNIQUE B] for [SUBPROBLEM], "
            "including at least one tradeoff and one approach you would rule out.' "
            "The question must be impossible to answer well with generic statements only. "
            "Do not inject debugging or diagnostic framing. "
            "The question text must stand alone without sub-instructions. "
            'question_type must be "open_ended". '
            "options must be []. "
            "answer_key must include expected_concepts and required_concept_count."
        )
