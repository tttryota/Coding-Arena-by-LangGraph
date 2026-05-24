"""LangGraph セッションフロー検証スクリプト。

実際の LLM を使って1セッション分（確認ポイント生成→出題→回答→評価→...→完了）を
通しで実行し、ノード間の状態遷移・責務分割・収束を検証する。

Usage:
    cd backend
    uv run python scripts/verify_session_flow.py
"""
# ruff: noqa: T201, BLE001, PLR0915, RUF002, I001, ARG002, SIM113

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.llm.codex_transport import CodexLlmTransport
from langgraph.checkpoint.memory import MemorySaver
from quiz.application.graph import QuizGraphRunner, build_graph
from quiz.application.graph_types import GraphDependencies
from quiz.infrastructure.codex_llm_adapters import (
    CodexAnswerEvaluationLlm,
    CodexChatResponseLlm,
    CodexExplanationLlm,
    CodexInputClassificationLlm,
    CodexProgressUpdateLlm,
    CodexQuestionDeliveryLlm,
    CodexQuestionSetDesignLlm,
    CodexSummaryTestLlm,
)


# ---------------------------------------------------------------------------
# Stub: RAG / Store (グラフ実行に必要だが検証対象外)
# ---------------------------------------------------------------------------

class StubRagClient:
    def search_related_chunks(self, query: str) -> list[str]:
        return ["(stub: ノートチャンクなし)"]


class StubProgressStore:
    def __init__(self) -> None:
        self.records: list[object] = []

    def update_roadmap_item_progress(self, item_id: str, score: int, last_quiz_at: object) -> None:
        self.records.append({"item_id": item_id, "score": score})
        print(f"    [Store] progress update: score={score}", flush=True)


class StubSummaryStore:
    def create(self, record: object) -> None:
        print("    [Store] summary test recorded", flush=True)


# ---------------------------------------------------------------------------
# 模擬回答: ユーザーの学習シナリオ
# ---------------------------------------------------------------------------

# 回答は確認ポイントの内容を見て動的に生成する
# ここでは質問内容に応じた回答パターンを定義
ANSWER_PATTERNS = [
    # 1問目: 概念質問に対して不十分な回答 → deepdive を誘発
    "よくわからないけど、型パラメータを使って汎用的にする仕組みだと思います",
    # 2問目以降: deepdive や次の確認ポイントに対してそこそこの回答
    "ジェネリクスは関数やクラスに型パラメータTを付けて、呼び出し時に具体的な型を決められる仕組みです。anyと違って型の整合性がコンパイル時にチェックされます。",
    # 3問目: コード実装問題への回答
    "function identity<T>(arg: T): T { return arg; }",
    # 4問目: 制約付きジェネリクス
    "extendsを使うとTに制約を付けられます。例えば<T extends { id: number }>とすると、idプロパティを持つ型だけを受け付けます。",
    # 5問目以降: 十分な回答
    "型パラメータTは呼び出し側で具体型に置き換わるため、関数本体では抽象的に扱いつつ、利用側では完全な型安全性が得られます。これがanyとの決定的な違いです。",
    # 以降繰り返し用
    "ジェネリック型を活用すると、配列操作やAPIレスポンスの型定義などで型安全性と再利用性を両立できます。",
    "Promise<T>やArray<T>のように、標準ライブラリもジェネリクスで設計されており、戻り値の型が推論されます。",
    "型パラメータに複数の制約を付ける場合はintersection型を使い、T extends A & Bとします。",
    "ジェネリクスの型推論は引数から自動的に行われるため、呼び出し側で明示する必要がない場面が多いです。",
    "まとめると、ジェネリクスは型の抽象化手段であり、コードの再利用性と型安全性を同時に実現する仕組みです。",
]


def main() -> None:
    print("=" * 70, flush=True)
    print("LangGraph セッションフロー検証", flush=True)
    print("=" * 70, flush=True)

    transport = CodexLlmTransport(timeout=180.0)

    deps = GraphDependencies(
        question_set_design_llm=CodexQuestionSetDesignLlm(transport),
        question_delivery_llm=CodexQuestionDeliveryLlm(transport),
        input_classification_llm=CodexInputClassificationLlm(transport),
        chat_response_llm=CodexChatResponseLlm(transport),
        answer_evaluation_llm=CodexAnswerEvaluationLlm(transport),
        explanation_rag=StubRagClient(),
        explanation_llm=CodexExplanationLlm(transport),
        progress_update_llm=CodexProgressUpdateLlm(transport),
        progress_update_store=StubProgressStore(),
        summary_test_llm=CodexSummaryTestLlm(transport),
        summary_test_store=StubSummaryStore(),
    )

    checkpointer = MemorySaver()
    compiled = build_graph(deps, checkpointer=checkpointer)
    runner = QuizGraphRunner(compiled)

    thread_id = str(uuid4())

    # 初期 state (C1 が設定する部分を手動で構築)
    initial_state = {
        "session_id": str(uuid4()),
        "roadmap_item_id": str(uuid4()),
        "roadmap_item_level": "detail",
        "roadmap_item_title": "ジェネリクス",
        "roadmap_item_description": "TypeScriptのジェネリクスを使った型安全な関数・クラスの設計",
        "is_resumed": False,
    }

    print(f"\nthread_id: {thread_id}", flush=True)
    print(f"topic: {initial_state['roadmap_item_title']}", flush=True)
    print(f"level: {initial_state['roadmap_item_level']}", flush=True)

    # --- Start graph ---
    print("\n" + "=" * 70, flush=True)
    print("Graph START (C2: question_set_design → C3: question_delivery → interrupt)", flush=True)
    print("=" * 70, flush=True)

    runner.start_graph(initial_state, thread_id=thread_id)

    # interrupt 後の state を取得
    snapshot = compiled.get_state({"configurable": {"thread_id": thread_id}})
    state = snapshot.values
    _print_state_summary(state, "start 後")

    # --- Resume loop ---
    answer_idx = 0
    max_turns = 25  # 安全弁

    for turn in range(1, max_turns + 1):
        # state から現在の問題を確認
        question = state.get("current_question_text", "")
        answer_type = state.get("current_answer_type", "")
        cp_idx = state.get("current_point_index", 0)
        total_cps = len(state.get("confirmation_points", []))
        total_q = state.get("total_questions_asked", 0)

        print(f"\n{'─' * 70}", flush=True)
        print(f"Turn {turn} | CP {cp_idx+1}/{total_cps} | 出題総数={total_q} | answer_type={answer_type}", flush=True)
        print(f"{'─' * 70}", flush=True)
        print(f"  Q: {question[:120]}", flush=True)

        # 回答を選択
        answer = ANSWER_PATTERNS[min(answer_idx, len(ANSWER_PATTERNS) - 1)]
        answer_idx += 1
        print(f"  A: {answer[:100]}", flush=True)

        # form 経路で回答
        user_input = {
            "user_input": answer,
            "input_source": "form",
        }

        try:
            runner.resume_graph(user_input, thread_id=thread_id)
        except Exception as exc:
            print(f"  ERROR during resume: {type(exc).__name__}: {exc}", flush=True)
            break

        # 更新後の state を取得
        snapshot = compiled.get_state({"configurable": {"thread_id": thread_id}})
        state = snapshot.values

        # グラフが完了したか確認
        if snapshot.next == ():
            print("\n  >>> Graph COMPLETED <<<", flush=True)
            _print_state_summary(state, "完了時")
            break

        _print_state_after_turn(state)

    else:
        print(f"\n  >>> {max_turns} turns reached without completion <<<", flush=True)
        _print_state_summary(state, f"{max_turns} turn 後")

    transport.close()
    print("\n" + "=" * 70, flush=True)
    print("セッションフロー検証完了", flush=True)
    print("=" * 70, flush=True)


def _print_state_summary(state: dict, label: str) -> None:
    cps = state.get("confirmation_points", [])
    answers = state.get("answers", [])
    print(f"\n  [{label}]", flush=True)
    print(f"    確認ポイント数: {len(cps)}", flush=True)
    for i, cp in enumerate(cps):
        print(f"      [{i}] {cp['content'][:50]}... (format={cp['format']})", flush=True)
    print(f"    回答数: {len(answers)}", flush=True)
    print(f"    current_point_index: {state.get('current_point_index', '?')}", flush=True)
    print(f"    total_questions_asked: {state.get('total_questions_asked', '?')}", flush=True)
    if answers:
        print(f"    スコア推移: {[a['score'] for a in answers]}", flush=True)
        print(f"    action推移: {[state.get('next_action', '?')]}", flush=True)


def _print_state_after_turn(state: dict) -> None:
    answers = state.get("answers", [])
    last = answers[-1] if answers else None
    action = state.get("next_action", "?")
    cps = state.get("confirmation_points", [])
    cp_idx = state.get("current_point_index", 0)

    if last:
        print(f"  → score={last['score']}, action={action}, feedback={last['feedback'][:80]}", flush=True)

    if action == "deepdive":
        # 新しく追加された deepdive ポイントを表示
        for cp in cps[cp_idx:]:
            if not cp["id"].startswith("cp-"):
                print(f"    +deepdive: [{cp['id']}] {cp['content'][:60]}", flush=True)

    print(f"  → CP {cp_idx+1}/{len(cps)} | 残り {len(cps) - cp_idx} ポイント", flush=True)


if __name__ == "__main__":
    main()
