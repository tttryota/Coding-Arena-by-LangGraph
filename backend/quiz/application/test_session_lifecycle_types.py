from __future__ import annotations

import inspect
from dataclasses import fields, is_dataclass
from typing import Any, cast, get_type_hints

from quiz.application import session_lifecycle as session_lifecycle_module
from quiz.application.session_lifecycle_types import (
    GraphRunner,
    QuizAnswerStore,
    QuizSessionStore,
    ResumeSessionInput,
    RoadmapItemReader,
    StartSessionInput,
    StartSessionResult,
)
from quiz.domain.session_state import InputSource


def _assert_frozen_dataclass(candidate: type[object]) -> None:
    assert is_dataclass(candidate)
    params = cast("Any", candidate).__dataclass_params__
    assert params.frozen is True


def test_resume_contract_stays_session_id_only_without_expiry_inputs() -> None:
    # Arrange / Act
    start_input_hints = get_type_hints(StartSessionInput)
    resume_input_hints = get_type_hints(ResumeSessionInput)
    result_hints = get_type_hints(StartSessionResult)
    resume_signature = inspect.signature(session_lifecycle_module.resume_session)

    # Assert
    _assert_frozen_dataclass(StartSessionInput)
    _assert_frozen_dataclass(ResumeSessionInput)
    _assert_frozen_dataclass(StartSessionResult)
    assert [field.name for field in fields(StartSessionInput)] == ["roadmap_item_id"]
    assert start_input_hints == {"roadmap_item_id": str}
    assert [field.name for field in fields(ResumeSessionInput)] == [
        "session_id",
        "user_input",
        "input_source",
    ]
    assert resume_input_hints == {
        "session_id": str,
        "user_input": str,
        "input_source": InputSource,
    }
    assert [field.name for field in fields(StartSessionResult)] == [
        "session_id",
        "resume_required",
        "resume_session_id",
    ]
    assert result_hints == {
        "session_id": str,
        "resume_required": bool,
        "resume_session_id": str | None,
    }
    assert tuple(resume_signature.parameters) == (
        "input",
        "session_store",
        "answer_store",
        "item_reader",
        "graph_runner",
    )


def test_protocol_surfaces_stay_minimal() -> None:
    # Arrange / Act
    session_store_methods = {
        name
        for name, value in QuizSessionStore.__dict__.items()
        if callable(value) and not name.startswith("_")
    }
    answer_store_methods = {
        name
        for name, value in QuizAnswerStore.__dict__.items()
        if callable(value) and not name.startswith("_")
    }
    item_reader_methods = {
        name
        for name, value in RoadmapItemReader.__dict__.items()
        if callable(value) and not name.startswith("_")
    }
    graph_runner_methods = {
        name
        for name, value in GraphRunner.__dict__.items()
        if callable(value) and not name.startswith("_")
    }

    # Assert
    assert session_store_methods == {
        "complete_session",
        "create_session",
        "discard_session",
        "find_in_progress_by_item",
        "find_session",
    }
    assert answer_store_methods == {"save_answer", "find_by_session"}
    assert item_reader_methods == {"find_item"}
    assert graph_runner_methods == {"start_graph", "resume_graph", "retry_graph"}
