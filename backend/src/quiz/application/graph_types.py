from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quiz.application.answer_evaluation_types import AnswerEvaluationLlmClient
    from quiz.application.chat_response_types import ChatResponseLlmClient
    from quiz.application.explanation_generation_types import ExplanationLlmClient
    from quiz.application.input_classification_types import (
        InputClassificationLlmClient,
    )
    from quiz.application.progress_update_types import (
        ProgressUpdateLlmClient,
        ProgressUpdateStore,
    )
    from quiz.application.question_delivery_types import QuestionDeliveryLlmClient
    from quiz.application.question_set_design_types import QuestionSetDesignLlmClient
    from quiz.application.summary_test_record_types import (
        SummaryTestLlmClient,
        SummaryTestStore,
    )


@dataclass(frozen=True)
class GraphDependencies:
    """LangGraph グラフ構築に必要な全 Protocol 依存を束ねる。"""

    question_set_design_llm: QuestionSetDesignLlmClient
    question_delivery_llm: QuestionDeliveryLlmClient
    input_classification_llm: InputClassificationLlmClient
    chat_response_llm: ChatResponseLlmClient
    answer_evaluation_llm: AnswerEvaluationLlmClient
    explanation_llm: ExplanationLlmClient
    progress_update_llm: ProgressUpdateLlmClient
    progress_update_store: ProgressUpdateStore
    summary_test_llm: SummaryTestLlmClient
    summary_test_store: SummaryTestStore


__all__ = ["GraphDependencies"]
