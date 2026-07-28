"""競プロクイズの LangGraph グラフ定義と CompetitiveGraphRunner。

グラフ: theme_selection -> problem_generation -> await_submission -> solution_evaluation -> END
4 nodes, 1 interrupt, no loops.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Any

from langgraph.graph import END, StateGraph
from langgraph.types import interrupt

from competitive.application.problem_generation import generate_problem
from competitive.application.solution_evaluation import evaluate_solution
from competitive.application.theme_selection import select_theme
from competitive.domain.competitive_types import CompetitiveSessionState
from shared.observability import NoOpObservability, Observability

if TYPE_CHECKING:
    from competitive.application.problem_generation_types import (
        ProblemGenerationLlmClient,
    )
    from competitive.application.solution_evaluation_types import (
        SolutionEvaluationLlmClient,
    )
    from competitive.application.theme_selection_types import ThemeReaderClient

# ---------------------------------------------------------------------------
# Node names
# ---------------------------------------------------------------------------

NODE_THEME_SELECTION = "theme_selection"
NODE_PROBLEM_GENERATION = "problem_generation"
NODE_AWAIT_SUBMISSION = "await_submission"
NODE_SOLUTION_EVALUATION = "solution_evaluation"

# ---------------------------------------------------------------------------
# Internal node wrappers
# ---------------------------------------------------------------------------


_ALLOWED_RESUME_KEYS = frozenset({"user_code"})


def _await_submission(state: CompetitiveSessionState) -> dict[str, object]:
    """interrupt でグラフを一時停止し、ユーザーのコード提出を待つ。

    resume payload は user_code のみ許可する。
    grading_rubric や reference_solution の上書きを防ぐ。
    """
    public_state = {
        k: v for k, v in state.items()
        if k not in ("reference_solution", "grading_rubric")
    }
    user_input = interrupt(value=public_state)
    if not isinstance(user_input, dict):
        msg = f"Expected dict from interrupt resume, got {type(user_input).__name__}"
        raise ValueError(msg)
    extra_keys = set(user_input.keys()) - _ALLOWED_RESUME_KEYS
    if extra_keys:
        msg = f"Resume payload contains disallowed keys: {extra_keys}"
        raise ValueError(msg)
    if "user_code" not in user_input:
        msg = "Resume payload must contain 'user_code'"
        raise ValueError(msg)
    return user_input


# ---------------------------------------------------------------------------
# Graph dependencies
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompetitiveGraphDependencies:
    """競プログラフの依存一覧。"""

    theme_reader: ThemeReaderClient
    problem_generation_llm: ProblemGenerationLlmClient
    solution_evaluation_llm: SolutionEvaluationLlmClient


# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------


def build_competitive_graph(
    deps: CompetitiveGraphDependencies,
    checkpointer: Any,
) -> Any:
    """全ノードとエッジを登録して CompiledStateGraph を返す。"""
    graph: StateGraph[CompetitiveSessionState] = StateGraph(
        CompetitiveSessionState,
    )
    _add_competitive_nodes(graph, deps)
    _add_competitive_edges(graph)

    return graph.compile(checkpointer=checkpointer)


def _add_competitive_nodes(
    graph: StateGraph[CompetitiveSessionState],
    deps: CompetitiveGraphDependencies,
) -> None:
    """graph に競プロセッションの各 node を登録する。"""
    graph.add_node(
        NODE_THEME_SELECTION,
        partial(select_theme, reader=deps.theme_reader),
    )
    graph.add_node(
        NODE_PROBLEM_GENERATION,
        partial(generate_problem, llm=deps.problem_generation_llm),
    )
    graph.add_node(NODE_AWAIT_SUBMISSION, _await_submission)
    graph.add_node(
        NODE_SOLUTION_EVALUATION,
        partial(evaluate_solution, llm=deps.solution_evaluation_llm),
    )


def _add_competitive_edges(graph: StateGraph[CompetitiveSessionState]) -> None:
    """entry point と edge を登録する。"""
    graph.set_entry_point(NODE_THEME_SELECTION)
    graph.add_edge(NODE_THEME_SELECTION, NODE_PROBLEM_GENERATION)
    graph.add_edge(NODE_PROBLEM_GENERATION, NODE_AWAIT_SUBMISSION)
    graph.add_edge(NODE_AWAIT_SUBMISSION, NODE_SOLUTION_EVALUATION)
    graph.add_edge(NODE_SOLUTION_EVALUATION, END)


# ---------------------------------------------------------------------------
# Transient LLM error detection
# ---------------------------------------------------------------------------


class TransientLlmNodeError(Exception):
    """一過性 LLM エラー。checkpointer に状態が残っており再試行可能。"""

    def __init__(self, *, node_error: Exception, thread_id: str) -> None:
        self.node_error = node_error
        self.thread_id = thread_id
        super().__init__(f"Transient LLM error (thread={thread_id}): {node_error}")


def _is_transient_llm_error(exc: Exception) -> bool:
    """LLM 呼び出しの一時失敗だけを再試行対象として判定する。"""
    error_code = getattr(exc, "error_code", None)
    return error_code == "llm_request_failed"


# ---------------------------------------------------------------------------
# CompetitiveGraphRunner
# ---------------------------------------------------------------------------


class CompetitiveGraphRunner:
    """競プログラフの実行を管理する。"""

    def __init__(
        self,
        compiled_graph: Any,
        observability: Observability | None = None,
    ) -> None:
        self._graph = compiled_graph
        self._observability = observability or NoOpObservability()

    @staticmethod
    def _validate_thread_id(thread_id: str) -> None:
        """checkpointer のキーになる thread_id の空文字を防ぐ。"""
        if not thread_id:
            msg = "thread_id must not be empty"
            raise ValueError(msg)

    def _build_thread_config(
        self,
        thread_id: str,
        operation: str = "state",
    ) -> dict[str, Any]:
        config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
        config.update(
            self._observability.graph_config(
                flow="competitive",
                operation=operation,
                session_id=thread_id,
            ),
        )
        return config

    def _invoke_or_raise(
        self,
        payload: object,
        *,
        thread_id: str,
        operation: str,
    ) -> None:
        """graph 実行時の一過性 LLM エラー変換を共通化する。"""
        try:
            with self._observability.graph_scope(
                flow="competitive",
                operation=operation,
                session_id=thread_id,
            ):
                self._graph.invoke(
                    payload,
                    config=self._build_thread_config(thread_id, operation),
                )
        except Exception as exc:
            if _is_transient_llm_error(exc):
                raise TransientLlmNodeError(
                    node_error=exc, thread_id=thread_id,
                ) from exc
            raise

    def start_graph(
        self, state: CompetitiveSessionState, *, thread_id: str,
    ) -> None:
        """セッション開始。interrupt で一時停止する。"""
        self._validate_thread_id(thread_id)
        self._invoke_or_raise(state, thread_id=thread_id, operation="start")

    def resume_graph(
        self, user_input: dict[str, object], *, thread_id: str,
    ) -> None:
        """ユーザーのコード提出でグラフを再開する。"""
        self._validate_thread_id(thread_id)
        from langgraph.types import Command

        self._invoke_or_raise(
            Command(resume=user_input),
            thread_id=thread_id,
            operation="resume",
        )

    def get_state(self, *, thread_id: str) -> CompetitiveSessionState:
        """checkpointer から最新 state を取得する。"""
        self._validate_thread_id(thread_id)
        try:
            snapshot = self._graph.get_state(self._build_thread_config(thread_id))
        except Exception as exc:
            msg = f"Failed to read checkpoint for thread_id={thread_id!r}"
            raise RuntimeError(msg) from exc
        if snapshot.created_at is None:
            msg = f"No checkpoint found for thread_id={thread_id!r}"
            raise LookupError(msg)
        values = snapshot.values
        if not isinstance(values, Mapping):
            msg = f"Checkpoint state is not a mapping for thread_id={thread_id!r}"
            raise RuntimeError(msg)
        return values  # type: ignore[return-value]


__all__ = [
    "CompetitiveGraphDependencies",
    "CompetitiveGraphRunner",
    "TransientLlmNodeError",
    "build_competitive_graph",
]
