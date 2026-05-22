from __future__ import annotations

import inspect
from typing import Literal, get_type_hints

from quiz.application.question_set_design import design_question_set
from quiz.application.question_set_design_types import (
    QuestionSetDesignError,
    QuestionSetDesignLlmClient,
)
from quiz.domain.session_state import ConfirmationPoint, SessionState


def test_tc_02_question_set_design_public_contract_uses_confirmation_point_dto() -> None:
    # Arrange / Act
    exception = QuestionSetDesignError(
        error_code="llm_request_failed",
        message="question set design llm request failed",
    )
    llm_signature = inspect.signature(
        QuestionSetDesignLlmClient.generate_confirmation_points,
    )
    llm_hints = get_type_hints(
        QuestionSetDesignLlmClient.generate_confirmation_points,
    )
    design_signature = inspect.signature(design_question_set)
    design_hints = get_type_hints(design_question_set)

    # Assert
    assert exception.error_code == "llm_request_failed"
    assert exception.message == "question set design llm request failed"
    assert exception.args == ("question set design llm request failed",)
    assert tuple(llm_signature.parameters) == ("self", "title", "description", "level")
    assert llm_hints == {
        "title": str,
        "description": str,
        "level": str,
        "return": list[ConfirmationPoint],
    }
    assert tuple(design_signature.parameters) == ("state", "llm")
    llm_parameter = design_signature.parameters["llm"]
    assert llm_parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert design_hints == {
        "state": SessionState,
        "llm": QuestionSetDesignLlmClient,
        "return": dict[str, object],
    }
    confirmation_point_hints = get_type_hints(ConfirmationPoint)
    assert confirmation_point_hints == {
        "id": str,
        "content": str,
        "format": Literal["knowledge", "knowledge_and_practice"],
    }
