from __future__ import annotations

from apps.assessments.chains.base import BaseQuestionChain
from apps.assessments.chains.enums import QuestionType


class MCQSingleChain(BaseQuestionChain):
    question_type = QuestionType.MCQ_SINGLE

    @property
    def helper(self) -> str | None:
        return None

    def instruction_block(self) -> str:
        skill = self.build_slot_context({}).get("skill_area", "")
        extra = ""
        if "composition" in skill:
            extra = (
                " The scenario must include a constraint that makes exactly one composition "
                "strategy correct (e.g. must support different content types, ship today, "
                "shared library used by multiple teams). Without such a constraint, the "
                "question is ambiguous."
            )
        if skill in {"html_accessibility", "interface_foundations"} or "html" in skill:
            extra += (
                " For HTML semantics: <article> scenarios describe self-contained distributable "
                "content; <section> describes thematic groupings; never use 'independent' for "
                "<section> questions; never use only 'thematic' language for <article>."
            )
        return (
            "You are generating a professional technical interview question. "
            "The question should test practical job-readiness, not trivia. "
            "One option must be unambiguously correct. "
            "The other three options must be plausible mistakes a working developer could make — "
            "not obviously wrong. "
            "Do not add any sub-instructions to the question text itself. "
            "If choosing between related correct techniques, the stem must specify the axis "
            "of comparison (prerequisite, performance, complexity, browser support, or specificity) — "
            "never ask 'which is best' without defining best."
            f"{extra} "
            "Write exactly 4 parallel options. "
            'question_type must be "single_choice". '
            "answer_key.correct_option_ids must contain exactly one option id."
        )

