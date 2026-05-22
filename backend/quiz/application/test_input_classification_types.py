from __future__ import annotations

import inspect
from typing import get_args, get_type_hints

import quiz.application.input_classification as input_classification_module
from quiz.application.input_classification_types import (
    InputClassificationError,
    InputClassificationLlmClient,
)
from quiz.domain.session_state import SessionState


def test_tc_00_input_classification_error_exposes_public_attributes() -> None:
    # Arrange / Act
    error = InputClassificationError(
        error_code="llm_request_failed",
        message="input classification llm request failed",
    )

    # Assert
    assert isinstance(error, Exception)
    assert error.error_code == "llm_request_failed"
    assert error.message == "input classification llm request failed"
    assert str(error) == "input classification llm request failed"


def test_tc_01_input_classification_public_contract_stays_stable() -> None:
    # Arrange / Act
    protocol_hints = get_type_hints(InputClassificationLlmClient.classify_input)
    function_hints = get_type_hints(input_classification_module.classify_input)
    function_signature = inspect.signature(input_classification_module.classify_input)
    protocol_methods = {
        name
        for name, value in InputClassificationLlmClient.__dict__.items()
        if callable(value) and not name.startswith("_")
    }

    # Assert
    assert protocol_methods == {"classify_input"}
    assert protocol_hints["question_text"] is str
    assert protocol_hints["user_input"] is str
    assert get_args(protocol_hints["return"]) == (
        "answer",
        "question",
        "explanation_request",
    )
    assert tuple(function_signature.parameters) == ("state", "llm")
    assert function_signature.parameters["llm"].kind is inspect.Parameter.KEYWORD_ONLY
    assert function_hints == {
        "state": SessionState,
        "llm": InputClassificationLlmClient,
        "return": dict[str, object],
    }
    assert function_signature.return_annotation == "dict[str, object]"
