"""Cross-flow tests for LangGraph trace naming and session grouping."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

import pytest

from competitive.application.competitive_graph import CompetitiveGraphRunner
from quiz.application.coding_graph import CodingGraphRunner
from quiz.application.graph import QuizGraphRunner
from shared.observability import NoOpObservability


class _FakeCompiledGraph:
    def __init__(self) -> None:
        self.invocations: list[tuple[object, dict[str, object]]] = []

    def invoke(self, payload: object, *, config: dict[str, object]) -> None:
        self.invocations.append((payload, config))


class _RecordingObservability(NoOpObservability):
    def __init__(self) -> None:
        self.scopes: list[tuple[str, str, str]] = []

    @contextmanager
    def graph_scope(
        self,
        *,
        flow: str,
        operation: str,
        session_id: str,
    ) -> Any:
        self.scopes.append((flow, operation, session_id))
        yield

    def graph_config(
        self,
        *,
        flow: str,
        operation: str,
        session_id: str,
    ) -> dict[str, object]:
        return {
            "callbacks": ["langfuse-callback"],
            "run_name": f"{flow}.{operation}",
            "metadata": {"langfuse_session_id": session_id},
        }


@pytest.mark.parametrize(
    ("runner_type", "flow"),
    [
        (QuizGraphRunner, "quiz"),
        (CodingGraphRunner, "coding"),
        (CompetitiveGraphRunner, "competitive"),
    ],
)
def test_start_graph_uses_stable_trace_name_and_thread_session(
    runner_type: Any,
    flow: str,
) -> None:
    graph = _FakeCompiledGraph()
    observer = _RecordingObservability()
    runner = runner_type(graph, observer)

    runner.start_graph({}, thread_id="thread-123")

    assert observer.scopes == [(flow, "start", "thread-123")]
    assert graph.invocations[0][1] == {
        "configurable": {"thread_id": "thread-123"},
        "callbacks": ["langfuse-callback"],
        "run_name": f"{flow}.start",
        "metadata": {"langfuse_session_id": "thread-123"},
    }
