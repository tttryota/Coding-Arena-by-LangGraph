"""コーディングセッションの LangGraph グラフ定義と CodingGraphRunner。

グラフフロー:
lecture_generation -> await_lecture_input -> (chat: lecture_chat_response -> await_lecture_input)
                                         -> (practice_start: coding_problem_set_design)
coding_problem_set_design -> coding_problem_delivery -> await_coding_input
                                                     -> (chat: coding_chat_response -> await_coding_input)
                                                     -> (form: code_evaluation)
code_evaluation -> (next_step/retry: coding_problem_delivery)
               -> (next_cp: coding_problem_delivery)
               -> (complete: END)
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Any

from langgraph.graph import END, StateGraph
from langgraph.types import interrupt

from quiz.application.code_evaluation import evaluate_code
from quiz.application.coding_chat_response import respond_to_coding_chat
from quiz.application.coding_problem_delivery import deliver_coding_problem
from quiz.application.coding_problem_set_design import design_coding_problem_set
from quiz.application.lecture_chat_response import respond_to_lecture_chat
from quiz.application.lecture_generation import generate_lecture
from quiz.domain.coding_session_state import CodingSessionState
from shared.observability import NoOpObservability, Observability

if TYPE_CHECKING:
    from quiz.application.code_evaluation_types import CodeEvaluationLlmClient
    from quiz.application.coding_chat_response_types import (
        CodingChatResponseLlmClient,
    )
    from quiz.application.coding_problem_delivery_types import (
        CodingProblemDeliveryLlmClient,
    )
    from quiz.application.coding_problem_set_design_types import (
        CodingProblemSetDesignLlmClient,
    )
    from quiz.application.lecture_chat_response_types import (
        LectureChatResponseLlmClient,
    )
    from quiz.application.lecture_generation_types import (
        LectureGenerationLlmClient,
    )

# ---------------------------------------------------------------------------
# Node names
# ---------------------------------------------------------------------------

NODE_LECTURE_GENERATION = "lecture_generation"
NODE_AWAIT_LECTURE_INPUT = "await_lecture_input"
NODE_LECTURE_CHAT_RESPONSE = "lecture_chat_response"
NODE_CODING_PROBLEM_SET_DESIGN = "coding_problem_set_design"
NODE_CODING_PROBLEM_DELIVERY = "coding_problem_delivery"
NODE_AWAIT_CODING_INPUT = "await_coding_input"
NODE_CODING_CHAT_RESPONSE = "coding_chat_response"
NODE_CODE_EVALUATION = "code_evaluation"
NODE_PROGRESS_UPDATE = "progress_update"

# ---------------------------------------------------------------------------
# Interrupt nodes
# ---------------------------------------------------------------------------


_ALLOWED_LECTURE_RESUME_KEYS = frozenset({
    "user_input", "input_source", "lecture_phase_active",
})


def _await_lecture_input(state: CodingSessionState) -> dict[str, object]:
    """座学フェーズの interrupt。ユーザー入力を待つ。"""
    user_input = interrupt(value=state)
    if not isinstance(user_input, dict):
        msg = f"Expected dict from interrupt resume, got {type(user_input).__name__}"
        raise ValueError(msg)
    extra = set(user_input.keys()) - _ALLOWED_LECTURE_RESUME_KEYS
    if extra:
        msg = f"Resume payload contains disallowed keys: {extra}"
        raise ValueError(msg)
    # 座学フェーズでは chat 入力に加えて practice 開始フラグだけを通す。
    return user_input


_ALLOWED_CODING_RESUME_KEYS = frozenset({"user_input", "input_source"})


def _await_coding_input(state: CodingSessionState) -> dict[str, object]:
    """コーディングフェーズの interrupt。ユーザー入力を待つ。"""
    user_input = interrupt(value=state)
    if not isinstance(user_input, dict):
        msg = f"Expected dict from interrupt resume, got {type(user_input).__name__}"
        raise ValueError(msg)
    extra = set(user_input.keys()) - _ALLOWED_CODING_RESUME_KEYS
    if extra:
        msg = f"Resume payload contains disallowed keys: {extra}"
        raise ValueError(msg)
    if "user_input" not in user_input:
        msg = "Resume payload must contain 'user_input'"
        raise ValueError(msg)
    source = user_input.get("input_source", "form")
    if source not in ("form", "chat"):
        msg = f"Invalid input_source: {source}"
        raise ValueError(msg)
    return user_input


# ---------------------------------------------------------------------------
# Routing functions
# ---------------------------------------------------------------------------


def _coding_progress_update(
    state: CodingSessionState,  # noqa: ARG001
) -> dict[str, object]:
    """コーディングセッションの完了処理。current_score/feedbackは最終評価を維持する。"""
    return {}


def _route_lecture_input(state: CodingSessionState) -> str:
    """座学 input のルーティング。chat → lecture_chat, practice_start → CP設計。"""
    if state.get("lecture_phase_active") is False:
        return NODE_CODING_PROBLEM_SET_DESIGN
    return NODE_LECTURE_CHAT_RESPONSE


def _route_coding_input(state: CodingSessionState) -> str:
    """コーディング input のルーティング。form → 評価、chat → チャット。"""
    source = state.get("input_source", "form")
    if source == "chat":
        return NODE_CODING_CHAT_RESPONSE
    return NODE_CODE_EVALUATION


def _route_evaluation(state: CodingSessionState) -> str:
    """評価後のルーティング。"""
    action = state.get("next_action", "complete")
    if action in ("next_step", "retry", "next_cp"):
        return NODE_CODING_PROBLEM_DELIVERY
    return NODE_PROGRESS_UPDATE


# ---------------------------------------------------------------------------
# Graph dependencies
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CodingGraphDependencies:
    """コーディンググラフの依存一覧。"""

    lecture_generation_llm: LectureGenerationLlmClient
    lecture_chat_response_llm: LectureChatResponseLlmClient
    coding_problem_set_design_llm: CodingProblemSetDesignLlmClient
    coding_problem_delivery_llm: CodingProblemDeliveryLlmClient
    coding_chat_response_llm: CodingChatResponseLlmClient
    code_evaluation_llm: CodeEvaluationLlmClient


# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------


def build_coding_graph(
    deps: CodingGraphDependencies,
    checkpointer: Any,
) -> Any:
    """全ノードとエッジを登録して CompiledStateGraph を返す。"""
    graph: StateGraph[CodingSessionState] = StateGraph(CodingSessionState)
    _add_coding_nodes(graph, deps)
    _add_coding_edges(graph)

    return graph.compile(checkpointer=checkpointer)


def _add_coding_nodes(
    graph: StateGraph[CodingSessionState],
    deps: CodingGraphDependencies,
) -> None:
    """graph にコーディングセッション用 node を登録する。"""
    graph.add_node(
        NODE_LECTURE_GENERATION,
        partial(generate_lecture, llm=deps.lecture_generation_llm),
    )
    graph.add_node(NODE_AWAIT_LECTURE_INPUT, _await_lecture_input)
    graph.add_node(
        NODE_LECTURE_CHAT_RESPONSE,
        partial(respond_to_lecture_chat, llm=deps.lecture_chat_response_llm),
    )
    graph.add_node(
        NODE_CODING_PROBLEM_SET_DESIGN,
        partial(
            design_coding_problem_set,
            llm=deps.coding_problem_set_design_llm,
        ),
    )
    graph.add_node(
        NODE_CODING_PROBLEM_DELIVERY,
        partial(
            deliver_coding_problem,
            llm=deps.coding_problem_delivery_llm,
        ),
    )
    graph.add_node(NODE_AWAIT_CODING_INPUT, _await_coding_input)
    graph.add_node(
        NODE_CODING_CHAT_RESPONSE,
        partial(respond_to_coding_chat, llm=deps.coding_chat_response_llm),
    )
    graph.add_node(
        NODE_CODE_EVALUATION,
        partial(evaluate_code, llm=deps.code_evaluation_llm),
    )
    graph.add_node(NODE_PROGRESS_UPDATE, _coding_progress_update)


def _add_coding_edges(graph: StateGraph[CodingSessionState]) -> None:
    """entry point と edge を登録する。"""
    graph.set_entry_point(NODE_LECTURE_GENERATION)

    graph.add_edge(NODE_LECTURE_GENERATION, NODE_AWAIT_LECTURE_INPUT)
    graph.add_edge(NODE_LECTURE_CHAT_RESPONSE, NODE_AWAIT_LECTURE_INPUT)
    graph.add_edge(
        NODE_CODING_PROBLEM_SET_DESIGN, NODE_CODING_PROBLEM_DELIVERY,
    )
    graph.add_edge(NODE_CODING_PROBLEM_DELIVERY, NODE_AWAIT_CODING_INPUT)
    graph.add_edge(NODE_CODING_CHAT_RESPONSE, NODE_AWAIT_CODING_INPUT)
    graph.add_edge(NODE_PROGRESS_UPDATE, END)

    graph.add_conditional_edges(
        NODE_AWAIT_LECTURE_INPUT,
        _route_lecture_input,
        {
            NODE_CODING_PROBLEM_SET_DESIGN: NODE_CODING_PROBLEM_SET_DESIGN,
            NODE_LECTURE_CHAT_RESPONSE: NODE_LECTURE_CHAT_RESPONSE,
        },
    )
    graph.add_conditional_edges(
        NODE_AWAIT_CODING_INPUT,
        _route_coding_input,
        {
            NODE_CODE_EVALUATION: NODE_CODE_EVALUATION,
            NODE_CODING_CHAT_RESPONSE: NODE_CODING_CHAT_RESPONSE,
        },
    )
    graph.add_conditional_edges(
        NODE_CODE_EVALUATION,
        _route_evaluation,
        {
            NODE_CODING_PROBLEM_DELIVERY: NODE_CODING_PROBLEM_DELIVERY,
            NODE_PROGRESS_UPDATE: NODE_PROGRESS_UPDATE,
        },
    )


# ---------------------------------------------------------------------------
# Transient LLM error
# ---------------------------------------------------------------------------


class TransientLlmNodeError(Exception):
    """一過性 LLM エラー。checkpointer に状態が残っており再試行可能。"""

    def __init__(self, *, node_error: Exception, thread_id: str) -> None:
        self.node_error = node_error
        self.thread_id = thread_id
        super().__init__(
            f"Transient LLM error (thread={thread_id}): {node_error}",
        )


def _is_transient_llm_error(exc: Exception) -> bool:
    """LLM 呼び出しの一時失敗だけを再試行対象として判定する。"""
    return getattr(exc, "error_code", None) == "llm_request_failed"


# ---------------------------------------------------------------------------
# CodingGraphRunner
# ---------------------------------------------------------------------------


class CodingGraphRunner:
    """コーディンググラフの実行を管理する。"""

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
                flow="coding",
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
                flow="coding",
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
        self, state: CodingSessionState, *, thread_id: str,
    ) -> None:
        """新規コーディングセッションを開始する。"""
        self._validate_thread_id(thread_id)
        self._invoke_or_raise(state, thread_id=thread_id, operation="start")

    def resume_graph(
        self, user_input: dict[str, object], *, thread_id: str,
    ) -> None:
        """一時停止中のコーディングセッションを再開する。"""
        self._validate_thread_id(thread_id)
        from langgraph.types import Command

        self._invoke_or_raise(
            Command(resume=user_input),
            thread_id=thread_id,
            operation="resume",
        )

    def get_state(self, *, thread_id: str) -> CodingSessionState:
        """checkpointer から最新のコーディング状態を取得する。"""
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
    "CodingGraphDependencies",
    "CodingGraphRunner",
    "TransientLlmNodeError",
    "build_coding_graph",
]
