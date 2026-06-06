"""LangGraph グラフ定義と QuizGraphRunner。

quiz-overview.md のエッジ定義に従い、全ノードを接続する。
session_init (C1) はグラフ外で session_lifecycle.py が担当する。
グラフのエントリポイントは question_set_design (C2)。
"""

from __future__ import annotations

from collections.abc import Mapping
from functools import partial
from typing import TYPE_CHECKING, Any

from langgraph.graph import END, StateGraph
from langgraph.types import interrupt

from quiz.application.answer_evaluation import evaluate_answer
from quiz.application.chat_response import respond_to_chat
from quiz.application.explanation_generation import generate_explanation
from quiz.application.input_classification import classify_input
from quiz.application.progress_update import update_progress
from quiz.application.question_delivery import deliver_question
from quiz.application.question_set_design import design_question_set
from quiz.application.summary_test_record import record_summary_test
from quiz.application.summary_test_record_types import (  # noqa: TC001
    SummaryTestLlmClient,
    SummaryTestStore,
)
from quiz.domain.session_state import SessionState

if TYPE_CHECKING:
    from quiz.application.graph_types import GraphDependencies

# ---------------------------------------------------------------------------
# Node names (constants)
# ---------------------------------------------------------------------------

NODE_QUESTION_SET_DESIGN = "question_set_design"
NODE_QUESTION_DELIVERY = "question_delivery"
NODE_AWAIT_INPUT = "await_input"
NODE_INPUT_CLASSIFICATION = "input_classification"
NODE_CHAT_RESPONSE = "chat_response"
NODE_ANSWER_EVALUATION = "answer_evaluation"
NODE_EXPLANATION_GENERATION = "explanation_generation"
NODE_PROGRESS_UPDATE = "progress_update"
NODE_SUMMARY_TEST_RECORD = "summary_test_record"

# ---------------------------------------------------------------------------
# Internal node wrappers
# ---------------------------------------------------------------------------


def _await_input(state: SessionState) -> dict[str, object]:
    """spec の __interrupt__ を実装。グラフを一時停止してユーザー入力を待つ。"""
    user_input = interrupt(value=state)
    if not isinstance(user_input, dict):
        msg = f"Expected dict from interrupt resume, got {type(user_input).__name__}"
        raise ValueError(msg)
    return user_input


def _summary_test_record_node(
    state: SessionState,
    *,
    llm: SummaryTestLlmClient,
    store: SummaryTestStore,
) -> dict[str, object]:
    """record_summary_test は None を返すが LangGraph は dict を要求するためラッパー。"""
    record_summary_test(state, llm=llm, store=store)
    return {}


# ---------------------------------------------------------------------------
# Conditional edge routing functions
# ---------------------------------------------------------------------------


def _route_by_input_source(state: SessionState) -> str:
    """input_source に基づいて form → answer_evaluation, chat → input_classification。"""
    source = state["input_source"]
    if source == "form":
        return NODE_ANSWER_EVALUATION
    if source == "chat":
        return NODE_INPUT_CLASSIFICATION
    msg = f"Unexpected input_source: {source}"
    raise ValueError(msg)


def _route_by_input_type(state: SessionState) -> str:
    """input_type に基づいて answer/question/explanation_request をルーティング。"""
    input_type = state["input_type"]
    if input_type == "answer":
        return NODE_ANSWER_EVALUATION
    if input_type == "question":
        return NODE_CHAT_RESPONSE
    if input_type == "explanation_request":
        return NODE_EXPLANATION_GENERATION
    msg = f"Unexpected input_type: {input_type}"
    raise ValueError(msg)


def _route_by_next_action(state: SessionState) -> str:
    """next_action に基づいて next/deepdive → question_delivery, complete → progress_update。"""
    action = state["next_action"]
    if action == "complete":
        return NODE_PROGRESS_UPDATE
    if action in ("next", "deepdive"):
        return NODE_QUESTION_DELIVERY
    msg = f"Unexpected next_action: {action}"
    raise ValueError(msg)


def _route_by_roadmap_item_level(state: SessionState) -> str:
    """roadmap_item_level に基づいて detail → END, middle/major → summary_test_record。"""
    if state["roadmap_item_level"] in ("middle", "major"):
        return NODE_SUMMARY_TEST_RECORD
    return END


# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------


def build_graph(
    deps: GraphDependencies,
    checkpointer: Any = None,
) -> Any:
    """全ノードとエッジを登録して CompiledStateGraph を返す。"""
    graph: StateGraph[SessionState] = StateGraph(SessionState)
    _add_quiz_nodes(graph, deps)
    _add_quiz_edges(graph)

    return graph.compile(checkpointer=checkpointer)


def _add_quiz_nodes(
    graph: StateGraph[SessionState],
    deps: GraphDependencies,
) -> None:
    """graph に quiz の各 node を登録する。"""
    # node 登録を一か所に集めておくと、docs とコードの対応を追いやすい。
    graph.add_node(
        NODE_QUESTION_SET_DESIGN,
        partial(design_question_set, llm_client=deps.question_set_design_llm),
    )
    graph.add_node(
        NODE_QUESTION_DELIVERY,
        partial(deliver_question, llm=deps.question_delivery_llm),
    )
    graph.add_node(NODE_AWAIT_INPUT, _await_input)
    graph.add_node(
        NODE_INPUT_CLASSIFICATION,
        partial(classify_input, llm=deps.input_classification_llm),
    )
    graph.add_node(
        NODE_CHAT_RESPONSE,
        partial(respond_to_chat, llm=deps.chat_response_llm),
    )
    graph.add_node(
        NODE_ANSWER_EVALUATION,
        partial(evaluate_answer, llm=deps.answer_evaluation_llm),
    )
    graph.add_node(
        NODE_EXPLANATION_GENERATION,
        partial(
            generate_explanation,
            rag=deps.explanation_rag,
            llm=deps.explanation_llm,
        ),
    )
    graph.add_node(
        NODE_PROGRESS_UPDATE,
        partial(
            update_progress,
            llm=deps.progress_update_llm,
            store=deps.progress_update_store,
        ),
    )
    graph.add_node(
        NODE_SUMMARY_TEST_RECORD,
        partial(
            _summary_test_record_node,
            llm=deps.summary_test_llm,
            store=deps.summary_test_store,
        ),
    )


def _add_quiz_edges(graph: StateGraph[SessionState]) -> None:
    """graph の entry point と edge を登録する。"""
    graph.set_entry_point(NODE_QUESTION_SET_DESIGN)

    graph.add_edge(NODE_QUESTION_SET_DESIGN, NODE_QUESTION_DELIVERY)
    graph.add_edge(NODE_QUESTION_DELIVERY, NODE_AWAIT_INPUT)
    graph.add_edge(NODE_CHAT_RESPONSE, NODE_AWAIT_INPUT)
    graph.add_edge(NODE_EXPLANATION_GENERATION, NODE_QUESTION_DELIVERY)
    graph.add_edge(NODE_SUMMARY_TEST_RECORD, END)

    graph.add_conditional_edges(
        NODE_AWAIT_INPUT,
        _route_by_input_source,
        {
            NODE_ANSWER_EVALUATION: NODE_ANSWER_EVALUATION,
            NODE_INPUT_CLASSIFICATION: NODE_INPUT_CLASSIFICATION,
        },
    )
    graph.add_conditional_edges(
        NODE_INPUT_CLASSIFICATION,
        _route_by_input_type,
        {
            NODE_ANSWER_EVALUATION: NODE_ANSWER_EVALUATION,
            NODE_CHAT_RESPONSE: NODE_CHAT_RESPONSE,
            NODE_EXPLANATION_GENERATION: NODE_EXPLANATION_GENERATION,
        },
    )
    graph.add_conditional_edges(
        NODE_ANSWER_EVALUATION,
        _route_by_next_action,
        {
            NODE_QUESTION_DELIVERY: NODE_QUESTION_DELIVERY,
            NODE_PROGRESS_UPDATE: NODE_PROGRESS_UPDATE,
        },
    )
    graph.add_conditional_edges(
        NODE_PROGRESS_UPDATE,
        _route_by_roadmap_item_level,
        {
            NODE_SUMMARY_TEST_RECORD: NODE_SUMMARY_TEST_RECORD,
            END: END,
        },
    )


# ---------------------------------------------------------------------------
# Transient LLM error detection
# ---------------------------------------------------------------------------


class TransientLlmNodeError(Exception):
    """一過性 LLM エラー。グラフは checkpointer に状態が残っており再試行可能。"""

    def __init__(self, *, node_error: Exception, thread_id: str) -> None:
        self.node_error = node_error
        self.thread_id = thread_id
        super().__init__(f"Transient LLM error (thread={thread_id}): {node_error}")


def _is_transient_llm_error(exc: Exception) -> bool:
    """error_code 属性が "llm_request_failed" なら一過性エラーと判定する。"""
    error_code = getattr(exc, "error_code", None)
    return error_code == "llm_request_failed"


# ---------------------------------------------------------------------------
# GraphRunner concrete implementation
# ---------------------------------------------------------------------------


class QuizGraphRunner:
    """GraphRunner Protocol の concrete 実装。"""

    def __init__(self, compiled_graph: Any) -> None:
        self._graph = compiled_graph

    @staticmethod
    def _build_thread_config(thread_id: str) -> dict[str, dict[str, str]]:
        return {"configurable": {"thread_id": thread_id}}

    def _invoke_or_raise(self, payload: object, *, thread_id: str) -> None:
        """graph 実行時の一過性 LLM エラー変換を共通化する。"""
        try:
            self._graph.invoke(payload, config=self._build_thread_config(thread_id))
        except Exception as exc:
            if _is_transient_llm_error(exc):
                raise TransientLlmNodeError(
                    node_error=exc, thread_id=thread_id,
                ) from exc
            raise

    def start_graph(self, state: SessionState, *, thread_id: str) -> None:
        """新規セッション用にグラフを開始する。

        invoke() は interrupt() でグラフが一時停止した場合、例外を送出せず
        interrupt 時点の state を返す。返り値は不要 (checkpointer が state を保持する)。
        """
        self._invoke_or_raise(state, thread_id=thread_id)

    def resume_graph(self, user_input: dict[str, object], *, thread_id: str) -> None:
        """再開セッション用にグラフを続行する。Command(resume=...) で入力を渡す。"""
        from langgraph.types import Command

        self._invoke_or_raise(Command(resume=user_input), thread_id=thread_id)

    def retry_graph(self, *, thread_id: str) -> None:
        """前回失敗したノードから再実行する。

        LangGraph の checkpointer に失敗前の state が残っているため、
        invoke(None) で失敗ノードから再実行できる。
        """
        self._invoke_or_raise(None, thread_id=thread_id)

    def get_state(self, *, thread_id: str) -> SessionState:
        """checkpointer から thread_id に対応するグラフの最新 state を取得する。"""
        if not thread_id:
            msg = "thread_id must not be empty"
            raise ValueError(msg)
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
    "QuizGraphRunner",
    "TransientLlmNodeError",
    "build_graph",
]
