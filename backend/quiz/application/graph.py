"""LangGraph グラフ定義と QuizGraphRunner。

quiz-overview.md のエッジ定義に従い、全ノードを接続する。
session_init (C1) はグラフ外で session_lifecycle.py が担当する。
グラフのエントリポイントは question_set_design (C2)。
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

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
    from langgraph.graph.state import CompiledStateGraph

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
    interrupt(value=state)
    return {}


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


def build_graph(deps: GraphDependencies) -> CompiledStateGraph:  # noqa: PLR0915
    """全ノードとエッジを登録して CompiledStateGraph を返す。"""
    graph: StateGraph[SessionState] = StateGraph(SessionState)

    # ノード登録: functools.partial で Protocol 依存を束縛
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

    # エントリポイント
    graph.set_entry_point(NODE_QUESTION_SET_DESIGN)

    # 線形エッジ
    graph.add_edge(NODE_QUESTION_SET_DESIGN, NODE_QUESTION_DELIVERY)
    graph.add_edge(NODE_QUESTION_DELIVERY, NODE_AWAIT_INPUT)
    graph.add_edge(NODE_CHAT_RESPONSE, NODE_AWAIT_INPUT)
    graph.add_edge(NODE_EXPLANATION_GENERATION, NODE_QUESTION_DELIVERY)
    graph.add_edge(NODE_SUMMARY_TEST_RECORD, END)

    # 条件付きエッジ
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

    return graph.compile()


# ---------------------------------------------------------------------------
# GraphRunner concrete implementation
# ---------------------------------------------------------------------------


class QuizGraphRunner:
    """GraphRunner Protocol の concrete 実装。"""

    def __init__(self, compiled_graph: CompiledStateGraph) -> None:
        self._graph = compiled_graph

    def start_graph(self, state: SessionState) -> None:
        """新規セッション用にグラフを開始する。"""
        self._graph.invoke(state)

    def resume_graph(self, state: SessionState) -> None:
        """再開セッション用にグラフを続行する。"""
        self._graph.invoke(state)


__all__ = [
    "QuizGraphRunner",
    "build_graph",
]
