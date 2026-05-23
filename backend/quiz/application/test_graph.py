"""TDD tests for quiz/application/graph.py.

Category A: Routing function unit tests (pure functions)
Category B: Graph structure verification (nodes, linear edges, conditional edges)
Category C: QuizGraphRunner Protocol conformance

Design note: session_init (C1) is handled externally by session_lifecycle.py.
The graph entry point is question_set_design (C2). This is intentional -- see
session-lifecycle.md "C1 の責務" section.

The spec's `__interrupt__` is implemented as an `await_input` node that calls
LangGraph's `interrupt()`. This node acts as the user-input pause point.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from langgraph.graph import END

if TYPE_CHECKING:
    from quiz.domain.session_state import (
        InputSource,
        InputType,
        NextAction,
        RoadmapItemLevel,
        SessionState,
    )

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _routing_state(**fields: object) -> SessionState:
    """Build a minimal SessionState for routing function tests."""
    return fields  # type: ignore[return-value]


def _build_test_graph():
    """Build a compiled graph with stub dependencies for structure tests."""
    from quiz.application.graph import build_graph
    from quiz.application.graph_types import GraphDependencies

    class _NoopStub:
        """Stub that returns empty list/string/int for any Protocol method."""

        def __getattr__(self, name: str):
            def _noop(*_args: object, **_kw: object) -> object:
                return []

            return _noop

    stub = _NoopStub()
    return build_graph(GraphDependencies(
        question_set_design_llm=stub,  # type: ignore[arg-type]
        question_delivery_llm=stub,  # type: ignore[arg-type]
        input_classification_llm=stub,  # type: ignore[arg-type]
        chat_response_llm=stub,  # type: ignore[arg-type]
        answer_evaluation_llm=stub,  # type: ignore[arg-type]
        explanation_rag=stub,  # type: ignore[arg-type]
        explanation_llm=stub,  # type: ignore[arg-type]
        progress_update_llm=stub,  # type: ignore[arg-type]
        progress_update_store=stub,  # type: ignore[arg-type]
        summary_test_llm=stub,  # type: ignore[arg-type]
        summary_test_store=stub,  # type: ignore[arg-type]
    ))


@pytest.fixture(scope="module")
def compiled_graph():
    """Module-scoped fixture: compile the graph once for all structure tests."""
    return _build_test_graph()


def _graph_edge_targets(compiled_graph: object, source: str) -> set[str]:
    """Get all target node names for edges from a given source node."""
    draw = compiled_graph.get_graph()  # type: ignore[union-attr]
    return {e.target for e in draw.edges if e.source == source}


# ---------------------------------------------------------------------------
# Category A: Routing function unit tests
# ---------------------------------------------------------------------------


class TestRouteByInputSource:
    @pytest.mark.parametrize(
        ("input_source", "expected"),
        [
            ("form", "answer_evaluation"),
            ("chat", "input_classification"),
        ],
    )
    def test_routes_correctly(
        self, input_source: InputSource, expected: str,
    ) -> None:
        from quiz.application.graph import _route_by_input_source

        assert _route_by_input_source(_routing_state(input_source=input_source)) == expected


class TestRouteByInputType:
    @pytest.mark.parametrize(
        ("input_type", "expected"),
        [
            ("answer", "answer_evaluation"),
            ("question", "chat_response"),
            ("explanation_request", "explanation_generation"),
        ],
    )
    def test_routes_correctly(
        self, input_type: InputType, expected: str,
    ) -> None:
        from quiz.application.graph import _route_by_input_type

        assert _route_by_input_type(_routing_state(input_type=input_type)) == expected


class TestRouteByNextAction:
    @pytest.mark.parametrize(
        ("next_action", "expected"),
        [
            ("next", "question_delivery"),
            ("deepdive", "question_delivery"),
            ("complete", "progress_update"),
        ],
    )
    def test_routes_correctly(
        self, next_action: NextAction, expected: str,
    ) -> None:
        from quiz.application.graph import _route_by_next_action

        assert _route_by_next_action(_routing_state(next_action=next_action)) == expected


class TestRouteByRoadmapItemLevel:
    @pytest.mark.parametrize(
        ("level", "expected"),
        [
            ("detail", END),
            ("middle", "summary_test_record"),
            ("major", "summary_test_record"),
        ],
    )
    def test_routes_correctly(
        self, level: RoadmapItemLevel, expected: str,
    ) -> None:
        from quiz.application.graph import _route_by_roadmap_item_level

        assert _route_by_roadmap_item_level(_routing_state(roadmap_item_level=level)) == expected


# ---------------------------------------------------------------------------
# Category B: Graph structure verification
# ---------------------------------------------------------------------------

# session_init (C1) is NOT a graph node -- handled by session_lifecycle.py
_EXPECTED_NODES = frozenset({
    "question_set_design",
    "question_delivery",
    "await_input",  # implements spec's __interrupt__
    "input_classification",
    "chat_response",
    "answer_evaluation",
    "explanation_generation",
    "progress_update",
    "summary_test_record",
})


class TestGraphNodes:
    def test_all_required_nodes_are_registered(self, compiled_graph: object) -> None:
        node_names = set(compiled_graph.get_graph().nodes) - {"__start__", "__end__"}  # type: ignore[union-attr]
        assert node_names == _EXPECTED_NODES


class TestGraphLinearEdges:
    """Verify all unconditional (linear) edges from the spec."""

    @pytest.mark.parametrize(
        ("source", "target"),
        [
            ("question_set_design", "question_delivery"),
            ("question_delivery", "await_input"),
            ("chat_response", "await_input"),
            ("explanation_generation", "question_delivery"),
            ("summary_test_record", "__end__"),
        ],
    )
    def test_linear_edge_exists(
        self, compiled_graph: object, source: str, target: str,
    ) -> None:
        targets = _graph_edge_targets(compiled_graph, source)
        assert target in targets, f"Expected edge {source} -> {target}, got {targets}"


class TestGraphConditionalEdges:
    """Verify conditional edge attachment points and their possible targets."""

    def test_await_input_has_conditional_targets(self, compiled_graph: object) -> None:
        targets = _graph_edge_targets(compiled_graph, "await_input")
        assert "answer_evaluation" in targets
        assert "input_classification" in targets

    def test_input_classification_has_conditional_targets(self, compiled_graph: object) -> None:
        targets = _graph_edge_targets(compiled_graph, "input_classification")
        assert "answer_evaluation" in targets
        assert "chat_response" in targets
        assert "explanation_generation" in targets

    def test_answer_evaluation_has_conditional_targets(self, compiled_graph: object) -> None:
        targets = _graph_edge_targets(compiled_graph, "answer_evaluation")
        assert "question_delivery" in targets
        assert "progress_update" in targets

    def test_progress_update_has_conditional_targets(self, compiled_graph: object) -> None:
        targets = _graph_edge_targets(compiled_graph, "progress_update")
        assert "summary_test_record" in targets
        assert "__end__" in targets

    def test_entry_point_is_question_set_design(self, compiled_graph: object) -> None:
        targets = _graph_edge_targets(compiled_graph, "__start__")
        assert "question_set_design" in targets


# ---------------------------------------------------------------------------
# Category C: QuizGraphRunner Protocol conformance
# ---------------------------------------------------------------------------


class TestQuizGraphRunnerProtocol:
    def test_satisfies_graph_runner_protocol_via_assignment(self) -> None:
        from quiz.application.graph import QuizGraphRunner
        from quiz.application.session_lifecycle_types import GraphRunner  # noqa: TC001

        runner: GraphRunner = QuizGraphRunner(_build_test_graph())
        # Verify methods exist and are callable
        assert callable(runner.start_graph)
        assert callable(runner.resume_graph)
