"""LLM プロンプト出力品質の受け入れ検証スクリプト。

各 LLM アダプターを実インスタンス化し、定義済みシナリオでプロンプトを実行。
フォーマット準拠を自動チェックし、内容品質は生出力を表示して目視確認する。

Usage:
    cd backend
    uv run python scripts/verify_llm_prompts.py
"""
# ruff: noqa: T201, BLE001, PLR0915, RUF001, RUF003, I001

from __future__ import annotations

import json
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.llm.codex_transport import CodexLlmTransport


# ---------------------------------------------------------------------------
# Result tracking
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    scenario: str
    check: str
    passed: bool
    detail: str = ""


results: list[CheckResult] = []


def check(scenario: str, name: str, condition: bool, detail: str = "") -> bool:
    results.append(CheckResult(scenario=scenario, check=name, passed=condition, detail=detail))
    mark = "[PASS]" if condition else "[FAIL]"
    msg = f"  {mark} {name}"
    if detail and not condition:
        msg += f" — {detail}"
    print(msg)
    return condition


def print_raw(label: str, value: object) -> None:
    print(f"\n  raw {label}:")
    if isinstance(value, str):
        for line in value.split("\n"):
            print(f"    {line}")
    else:
        for line in json.dumps(value, ensure_ascii=False, indent=2).split("\n"):
            print(f"    {line}")


# ---------------------------------------------------------------------------
# S1: QuestionSetDesign
# ---------------------------------------------------------------------------

def verify_s1(transport: CodexLlmTransport) -> None:
    from quiz.infrastructure.codex_llm_adapters import CodexQuestionSetDesignLlm

    adapter = CodexQuestionSetDesignLlm(transport)

    # S1-1: detail, 実装寄り
    print("\n== S1-1: QuestionSetDesign — detail/実装寄り ==")
    try:
        result = adapter.generate_confirmation_points(
            "ジェネリクス",
            "TypeScriptのジェネリクスを使った型安全な関数・クラスの設計",
            "detail",
        )
        print_raw("出力", result)

        check("S1-1", "配列が返る", isinstance(result, list))
        check("S1-1", "要素数 3-5", 3 <= len(result) <= 5, f"実際: {len(result)}")

        ids = set()
        for i, cp in enumerate(result):
            check("S1-1", f"[{i}] id,content,format あり",
                  all(k in cp for k in ("id", "content", "format")))
            check("S1-1", f"[{i}] format valid",
                  cp.get("format") in ("knowledge", "knowledge_and_practice"),
                  f"実際: {cp.get('format')}")
            ids.add(cp.get("id"))

        check("S1-1", "id ユニーク", len(ids) == len(result))

    except Exception as exc:
        check("S1-1", "例外なし", False, str(exc))
        traceback.print_exc()

    # S1-2: major, 概念的
    print("\n== S1-2: QuestionSetDesign — major/概念的 ==")
    try:
        result = adapter.generate_confirmation_points(
            "プログラミングパラダイム",
            "オブジェクト指向・関数型・手続き型の比較と使い分け",
            "major",
        )
        print_raw("出力", result)

        check("S1-2", "要素数 3-5", 3 <= len(result) <= 5, f"実際: {len(result)}")

        knowledge_count = sum(1 for cp in result if cp.get("format") == "knowledge")
        check("S1-2", "knowledge が多数",
              knowledge_count >= len(result) // 2,
              f"knowledge: {knowledge_count}/{len(result)}")

    except Exception as exc:
        check("S1-2", "例外なし", False, str(exc))
        traceback.print_exc()


# ---------------------------------------------------------------------------
# S2: QuestionDelivery
# ---------------------------------------------------------------------------

def verify_s2(transport: CodexLlmTransport) -> None:
    from quiz.infrastructure.codex_llm_adapters import CodexQuestionDeliveryLlm

    adapter = CodexQuestionDeliveryLlm(transport)

    # S2-1: knowledge
    print("\n== S2-1: QuestionDelivery — knowledge ==")
    try:
        result = adapter.generate_question(
            "TypeScript", "TypeScriptの型システムの基礎",
            "型推論の仕組みを説明できる", "knowledge", [],
        )
        print_raw("出力", {"question_text": result.question_text, "answer_type": result.answer_type})

        check("S2-1", "answer_type=textarea", result.answer_type == "textarea",
              f"実際: {result.answer_type}")
        check("S2-1", "question_text 非空", len(result.question_text.strip()) > 0)

    except Exception as exc:
        check("S2-1", "例外なし", False, str(exc))
        traceback.print_exc()

    # S2-2: knowledge_and_practice
    print("\n== S2-2: QuestionDelivery — knowledge_and_practice ==")
    try:
        result = adapter.generate_question(
            "TypeScript", "ジェネリクスの実践的な使い方",
            "ジェネリック関数を実装できる", "knowledge_and_practice", [],
        )
        print_raw("出力", {"question_text": result.question_text, "answer_type": result.answer_type})

        check("S2-2", "answer_type=code", result.answer_type == "code",
              f"実際: {result.answer_type}")

    except Exception as exc:
        check("S2-2", "例外なし", False, str(exc))
        traceback.print_exc()

    # S2-3: past_answers あり
    print("\n== S2-3: QuestionDelivery — 過去回答あり ==")
    try:
        past = [{
            "question_number": 1,
            "confirmation_point_id": "cp-001",
            "question_text": "TypeScriptの型推論とはどのような仕組みですか？",
            "answer_type": "textarea",
            "answer_text": "型を自動で決めてくれる機能",
            "score": 30,
            "feedback": "概要は合っていますが、具体的な推論ルールの説明が不足しています",
        }]
        result = adapter.generate_question(
            "TypeScript", "型推論",
            "型推論の仕組みを説明できる", "knowledge", past,
        )
        print_raw("出力", {"question_text": result.question_text, "answer_type": result.answer_type})

        check("S2-3", "前回と異なる問題文",
              result.question_text != past[0]["question_text"])

    except Exception as exc:
        check("S2-3", "例外なし", False, str(exc))
        traceback.print_exc()


# ---------------------------------------------------------------------------
# S3: InputClassification
# ---------------------------------------------------------------------------

def verify_s3(transport: CodexLlmTransport) -> None:
    from quiz.infrastructure.codex_llm_adapters import CodexInputClassificationLlm

    adapter = CodexInputClassificationLlm(transport)
    question = "TypeScriptの型推論とはどのような仕組みですか？"

    cases = [
        ("S3-1", "明確な回答",
         "コンパイラが変数の初期化値や関数の戻り値の型から、明示的な型アノテーションなしに型を推論する仕組みです。",
         "answer"),
        ("S3-2", "質問",
         "型推論って、JavaScriptにもあるんですか？それともTypeScript特有？",
         "question"),
        ("S3-3", "解説依頼",
         "型推論がよくわからないので、具体例を使って解説してほしいです",
         "explanation_request"),
        ("S3-4", "曖昧入力", "うーん", "answer"),
        ("S3-5", "1文字入力", "あ", "answer"),
    ]

    for sid, label, user_input, expected in cases:
        print(f"\n== {sid}: InputClassification — {label} ==")
        try:
            result = adapter.classify_input(question, user_input)
            print(f"  入力: {user_input}")
            print(f"  結果: {result}")
            check(sid, f"input_type={expected}", result == expected,
                  f"実際: {result}")
        except Exception as exc:
            check(sid, "例外なし", False, str(exc))
            traceback.print_exc()


# ---------------------------------------------------------------------------
# S4: ChatResponse
# ---------------------------------------------------------------------------

def verify_s4(transport: CodexLlmTransport) -> None:
    from quiz.infrastructure.codex_llm_adapters import CodexChatResponseLlm

    adapter = CodexChatResponseLlm(transport)

    print("\n== S4-1: ChatResponse — 基本質問 ==")
    try:
        result = adapter.generate_chat_response(
            "useEffectの第2引数の役割を説明してください",
            "useEffectって何ですか？基本的なところから教えてください",
        )
        print_raw("出力", result)

        check("S4-1", "文字列が返る", isinstance(result, str))
        check("S4-1", "空でない", len(result.strip()) > 0)

    except Exception as exc:
        check("S4-1", "例外なし", False, str(exc))
        traceback.print_exc()


# ---------------------------------------------------------------------------
# S5: AnswerEvaluation
# ---------------------------------------------------------------------------

def verify_s5(transport: CodexLlmTransport) -> None:
    from quiz.infrastructure.codex_llm_adapters import CodexAnswerEvaluationLlm

    adapter = CodexAnswerEvaluationLlm(transport)

    base_q = "TypeScriptの型推論とはどのような仕組みですか？"
    base_cp = "型推論の仕組みを説明できる"

    # S5-1: 十分な回答
    print("\n== S5-1: AnswerEvaluation — 十分な回答 ==")
    try:
        result = adapter.evaluate_answer(
            base_q, base_cp,
            "TypeScriptの型推論は、コンパイラが変数の初期化値や関数の戻り値から型を自動的に推論する仕組みです。"
            "例えば let x = 5 と書くと x は number 型と推論されます。関数の戻り値も return 文から推論されます。",
            "textarea", [], 1,
        )
        print_raw("出力", {
            "next_action": result.next_action, "score": result.score,
            "feedback": result.feedback, "deepdive_points": result.deepdive_points,
        })

        check("S5-1", "score >= 70", result.score >= 70, f"実際: {result.score}")
        check("S5-1", "next_action=next or complete",
              result.next_action in ("next", "complete"), f"実際: {result.next_action}")
        check("S5-1", "deepdive_points 空", result.deepdive_points == [])

    except Exception as exc:
        check("S5-1", "例外なし", False, str(exc))
        traceback.print_exc()

    # S5-2: 不十分な回答
    print("\n== S5-2: AnswerEvaluation — 不十分な回答 ==")
    try:
        result = adapter.evaluate_answer(
            base_q, base_cp, "型を推論すること", "textarea", [], 1,
        )
        print_raw("出力", {
            "next_action": result.next_action, "score": result.score,
            "feedback": result.feedback, "deepdive_points": result.deepdive_points,
        })

        check("S5-2", "score <= 50", result.score <= 50, f"実際: {result.score}")
        if result.next_action == "deepdive":
            check("S5-2", "deepdive_points 1件以上",
                  len(result.deepdive_points) >= 1, f"実際: {len(result.deepdive_points)}")

    except Exception as exc:
        check("S5-2", "例外なし", False, str(exc))
        traceback.print_exc()

    # S5-3: 空回答
    print("\n== S5-3: AnswerEvaluation — 空回答 ==")
    try:
        result = adapter.evaluate_answer(
            base_q, base_cp, "", "textarea", [], 1,
        )
        print_raw("出力", {
            "next_action": result.next_action, "score": result.score,
            "feedback": result.feedback, "deepdive_points": result.deepdive_points,
        })

        check("S5-3", "score = 0", result.score == 0, f"実際: {result.score}")
        check("S5-3", "next_action=next", result.next_action == "next",
              f"実際: {result.next_action}")
        check("S5-3", "deepdive_points 空", result.deepdive_points == [])

    except Exception as exc:
        check("S5-3", "例外なし", False, str(exc))
        traceback.print_exc()

    # S5-4: 20問到達
    print("\n== S5-4: AnswerEvaluation — 20問到達 ==")
    try:
        result = adapter.evaluate_answer(
            "クロージャとは何ですか？", "クロージャの仕組みを説明できる",
            "関数が外側のスコープの変数を参照できる仕組み", "textarea", [], 20,
        )
        print_raw("出力", {
            "next_action": result.next_action, "score": result.score,
            "feedback": result.feedback,
        })

        check("S5-4", "next_action != deepdive", result.next_action != "deepdive",
              f"実際: {result.next_action}")

    except Exception as exc:
        check("S5-4", "例外なし", False, str(exc))
        traceback.print_exc()

    # S5-5: コード回答（構文エラー）
    print("\n== S5-5: AnswerEvaluation — 構文エラーあり ==")
    try:
        result = adapter.evaluate_answer(
            "配列の各要素を2倍にする関数を実装してください",
            "配列操作の基本的な実装ができる",
            "function double(arr: number[]) { return arr.map(x => x * 2 }",
            "code", [], 3,
        )
        print_raw("出力", {
            "next_action": result.next_action, "score": result.score,
            "feedback": result.feedback,
        })

        check("S5-5", "score > 0", result.score > 0, f"実際: {result.score}")

    except Exception as exc:
        check("S5-5", "例外なし", False, str(exc))
        traceback.print_exc()


# ---------------------------------------------------------------------------
# S6: Explanation
# ---------------------------------------------------------------------------

def verify_s6(transport: CodexLlmTransport) -> None:
    from quiz.infrastructure.codex_llm_adapters import CodexExplanationLlm

    adapter = CodexExplanationLlm(transport)
    q = "TypeScriptの型推論とはどのような仕組みですか？"
    cp = "型推論の仕組みを説明できる"

    # S6-1: ノートあり
    print("\n== S6-1: Explanation — ノートチャンクあり ==")
    try:
        result = adapter.generate_explanation(q, cp, [
            "TypeScriptでは let x = 5 と書くと x は number 型と推論される。これは型推論と呼ばれる機能である。",
            "関数の戻り値も return 文の式から型が推論される。明示的な戻り値型アノテーションは省略可能。",
        ])
        print_raw("出力", result)

        check("S6-1", "文字列が返る", isinstance(result, str))
        check("S6-1", "空でない", len(result.strip()) > 0)

    except Exception as exc:
        check("S6-1", "例外なし", False, str(exc))
        traceback.print_exc()

    # S6-2: ノートなし
    print("\n== S6-2: Explanation — ノートチャンクなし ==")
    try:
        result = adapter.generate_explanation(q, cp, [])
        print_raw("出力", result)

        check("S6-2", "文字列が返る", isinstance(result, str))
        check("S6-2", "空でない", len(result.strip()) > 0)

    except Exception as exc:
        check("S6-2", "例外なし", False, str(exc))
        traceback.print_exc()


# ---------------------------------------------------------------------------
# S7: ProgressUpdate
# ---------------------------------------------------------------------------

def verify_s7(transport: CodexLlmTransport) -> None:
    from quiz.infrastructure.codex_llm_adapters import CodexProgressUpdateLlm

    adapter = CodexProgressUpdateLlm(transport)

    print("\n== S7-1: ProgressUpdate — 1問回答済み ==")
    try:
        answers = [{
            "question_number": 1, "confirmation_point_id": "cp-1",
            "question_text": "型推論とは何ですか", "answer_type": "textarea",
            "answer_text": "変数の初期値から型を自動判定する仕組み", "score": 70,
            "feedback": "基本は理解しているが具体例が不足",
        }]
        result = adapter.evaluate_session(
            "TypeScript 型システム", "TypeScriptの型に関する基礎知識",
            ["型推論の仕組み", "型アノテーションの使い方", "ユニオン型の理解"],
            answers,
        )
        print_raw("出力", {"score": result.score, "comment": result.comment})

        check("S7-1", "score 0-100", 0 <= result.score <= 100, f"実際: {result.score}")
        check("S7-1", "comment 非空", len(result.comment.strip()) > 0)

    except Exception as exc:
        check("S7-1", "例外なし", False, str(exc))
        traceback.print_exc()


# ---------------------------------------------------------------------------
# S8: SummaryTest
# ---------------------------------------------------------------------------

def verify_s8(transport: CodexLlmTransport) -> None:
    from quiz.infrastructure.codex_llm_adapters import CodexSummaryTestLlm

    adapter = CodexSummaryTestLlm(transport)

    print("\n== S8-1: SummaryTest — 複数問の中レベルテスト ==")
    try:
        answers = [
            {"question_number": 1, "confirmation_point_id": "cp-1",
             "question_text": "型推論とは", "answer_type": "textarea",
             "answer_text": "自動的に型を判定する仕組み", "score": 70,
             "feedback": "基本は理解"},
            {"question_number": 2, "confirmation_point_id": "cp-2",
             "question_text": "ジェネリック関数を実装してください",
             "answer_type": "code",
             "answer_text": "function id(x) { return x; }", "score": 30,
             "feedback": "型パラメータが使われていません"},
        ]
        result = adapter.analyze_session(
            "TypeScript", "TypeScript全般の理解度を確認する中レベルテスト", answers,
        )
        print_raw("出力", {"score": result.score, "analysis": result.analysis})

        check("S8-1", "score 0-100", 0 <= result.score <= 100, f"実際: {result.score}")
        check("S8-1", "analysis 非空", len(result.analysis.strip()) > 0)

    except Exception as exc:
        check("S8-1", "例外なし", False, str(exc))
        traceback.print_exc()


# ---------------------------------------------------------------------------
# S9: RoadmapGeneration
# ---------------------------------------------------------------------------

_expected_topic = ""


def _check_roadmap(sid: str, data: dict) -> None:
    check(sid, "topic 完全一致", data.get("topic") == _expected_topic,
          f"実際: {data.get('topic')}")

    items = data.get("items", [])
    check(sid, "items 2件", len(items) == 2, f"実際: {len(items)}")

    if len(items) >= 1:
        check(sid, 'items[0].title="基礎"', items[0].get("title") == "基礎",
              f"実際: {items[0].get('title')}")
    if len(items) >= 2:
        check(sid, 'items[1].title="応用"', items[1].get("title") == "応用",
              f"実際: {items[1].get('title')}")

    valid_levels = {"major", "middle", "detail"}
    required = {"title", "description", "level", "children"}

    def _walk(node: dict, exp_level: str, path: str) -> None:
        check(sid, f"{path}: 必須フィールド", required.issubset(node.keys()),
              f"不足: {required - node.keys()}")
        check(sid, f"{path}: level={exp_level}", node.get("level") == exp_level,
              f"実際: {node.get('level')}")
        check(sid, f"{path}: level valid", node.get("level") in valid_levels)
        check(sid, f"{path}: description 非空",
              isinstance(node.get("description"), str) and len(node["description"].strip()) > 0)

        children = node.get("children", [])
        if exp_level == "detail":
            check(sid, f"{path}: detail children 空", children == [],
                  f"実際: {len(children)}件")
        else:
            nxt = "middle" if exp_level == "major" else "detail"
            for i, child in enumerate(children):
                _walk(child, nxt, f"{path}.children[{i}]")

    for i, item in enumerate(items):
        _walk(item, "major", f"items[{i}]")


def verify_s9(transport: CodexLlmTransport) -> None:
    global _expected_topic
    from roadmap.infrastructure.codex_roadmap_generation_llm import CodexRoadmapGenerationLlm

    adapter = CodexRoadmapGenerationLlm(transport)

    # S9-1: TypeScript
    print("\n== S9-1: RoadmapGeneration — TypeScript ==")
    _expected_topic = "TypeScript"
    raw = ""
    try:
        raw = adapter.generate_roadmap_json("TypeScript")
        data = json.loads(raw)
        print_raw("トップレベル", {
            "topic": data.get("topic"),
            "items_count": len(data.get("items", [])),
        })
        _check_roadmap("S9-1", data)
    except json.JSONDecodeError:
        check("S9-1", "JSON parse", False, "JSONDecodeError")
        print(f"  raw: {raw[:500]}")
    except Exception as exc:
        check("S9-1", "例外なし", False, str(exc))
        traceback.print_exc()

    # S9-2: 日本語トピック
    print("\n== S9-2: RoadmapGeneration — 関数型プログラミング ==")
    _expected_topic = "関数型プログラミング"
    raw = ""
    try:
        raw = adapter.generate_roadmap_json("関数型プログラミング")
        data = json.loads(raw)
        print_raw("トップレベル", {
            "topic": data.get("topic"),
            "items_count": len(data.get("items", [])),
        })
        _check_roadmap("S9-2", data)
    except json.JSONDecodeError:
        check("S9-2", "JSON parse", False, "JSONDecodeError")
        print(f"  raw: {raw[:500]}")
    except Exception as exc:
        check("S9-2", "例外なし", False, str(exc))
        traceback.print_exc()


# ---------------------------------------------------------------------------
# S10: TagClassifier
# ---------------------------------------------------------------------------

def verify_s10(transport: CodexLlmTransport) -> None:
    from ingestion.infrastructure.codex_llm_tag_classifier import CodexLlmTagClassifier

    classifier = CodexLlmTagClassifier(transport)

    print("\n== S10-1: TagClassifier — 明確な技術トピック ==")
    try:
        result = classifier.classify(
            "useEffectを使ってAPIからデータを取得し、stateを更新するパターンについてまとめた",
        )
        print_raw("出力", result)

        check("S10-1", "list が返る", isinstance(result, list))
        check("S10-1", "全要素 str", all(isinstance(t, str) for t in result))

    except Exception as exc:
        check("S10-1", "例外なし", False, str(exc))
        traceback.print_exc()

    print("\n== S10-2: TagClassifier — 複数技術 ==")
    try:
        result = classifier.classify(
            "TypeScriptでReactコンポーネントのPropsに型を付ける方法。interfaceとtypeの使い分け。",
        )
        print_raw("出力", result)

        check("S10-2", "list が返る", isinstance(result, list))
        check("S10-2", "2つ以上のタグ", len(result) >= 2, f"実際: {len(result)}")

    except Exception as exc:
        check("S10-2", "例外なし", False, str(exc))
        traceback.print_exc()


# ---------------------------------------------------------------------------
# S11: IngestionFeedback
# ---------------------------------------------------------------------------

def verify_s11(transport: CodexLlmTransport) -> None:
    from ingestion.domain.ingestion_feedback_types import (
        IngestionFeedbackLlmRequest,
        RoadmapCandidate,
    )
    from ingestion.infrastructure.codex_ingestion_feedback_llm import CodexIngestionFeedbackLlm

    adapter = CodexIngestionFeedbackLlm(transport)

    # S11-1: 候補なし
    print("\n== S11-1: IngestionFeedback — 候補なし ==")
    try:
        request = IngestionFeedbackLlmRequest(
            source_path="study/typescript-generics.md",
            chunk_texts=[
                "TypeScriptのジェネリクスは型パラメータを使って再利用可能な型を定義する仕組みです。"
                "例えば function identity<T>(arg: T): T { return arg; } のように使います。"
                "ジェネリクスを使うことで、any を使わずに型安全性を保ちながら汎用的なコードが書けます。",
            ],
            roadmap_candidates=[],
        )
        result = adapter.analyze(request)
        print_raw("出力", {
            "selected_roadmap_item_id": str(result.selected_roadmap_item_id),
            "accuracy_check": result.accuracy_check,
            "improvement_suggestions": result.improvement_suggestions,
        })

        check("S11-1", "selected_roadmap_item_id=null",
              result.selected_roadmap_item_id is None,
              f"実際: {result.selected_roadmap_item_id}")
        check("S11-1", "accuracy_check 非空",
              isinstance(result.accuracy_check, str) and len(result.accuracy_check.strip()) > 0)
        check("S11-1", "improvement_suggestions 1件以上",
              len(result.improvement_suggestions) >= 1,
              f"実際: {len(result.improvement_suggestions)}")

    except Exception as exc:
        check("S11-1", "例外なし", False, str(exc))
        traceback.print_exc()

    # S11-2: 候補あり
    print("\n== S11-2: IngestionFeedback — 候補あり ==")
    uuid_react = uuid4()
    uuid_ts = uuid4()
    try:
        request = IngestionFeedbackLlmRequest(
            source_path="study/react-hooks.md",
            chunk_texts=[
                "ReactのuseStateはコンポーネントに状態を持たせるためのHookです。"
                "const [count, setCount] = useState(0) のように使い、setCountで状態を更新します。",
            ],
            roadmap_candidates=[
                RoadmapCandidate(id=uuid_react, display_path="React > 基礎 > Hooks"),
                RoadmapCandidate(id=uuid_ts, display_path="TypeScript > 基礎 > 型システム"),
            ],
        )
        result = adapter.analyze(request)
        print_raw("出力", {
            "selected_roadmap_item_id": str(result.selected_roadmap_item_id),
            "accuracy_check": result.accuracy_check,
            "improvement_suggestions": result.improvement_suggestions,
        })

        check("S11-2", "React Hooks が選択された",
              result.selected_roadmap_item_id == uuid_react,
              f"実際: {result.selected_roadmap_item_id} (React={uuid_react}, TS={uuid_ts})")
        check("S11-2", "improvement_suggestions 1件以上",
              len(result.improvement_suggestions) >= 1)

    except Exception as exc:
        check("S11-2", "例外なし", False, str(exc))
        traceback.print_exc()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 70)
    print("LLM プロンプト出力品質 受け入れ検証")
    print("=" * 70)

    transport = CodexLlmTransport(timeout=180.0)

    # 接続テスト
    print("\n-- 接続テスト --")
    try:
        from infrastructure.llm.codex_transport import CodexMessage
        test_result = transport.call([
            CodexMessage(role="user", content="Say 'OK' if you can read this."),
        ])
        print(f"  接続成功: {test_result[:80]}...")
    except Exception as exc:
        print(f"  接続失敗: {exc}")
        print("  codex CLI がインストールされているか確認してください。")
        sys.exit(1)

    verify_s1(transport)
    verify_s2(transport)
    verify_s3(transport)
    verify_s4(transport)
    verify_s5(transport)
    verify_s6(transport)
    verify_s7(transport)
    verify_s8(transport)
    verify_s9(transport)
    verify_s10(transport)
    verify_s11(transport)

    # Cleanup
    transport.close()

    # サマリ
    print("\n" + "=" * 70)
    print("サマリ")
    print("=" * 70)

    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    total = len(results)
    print(f"\n  PASS: {passed}/{total}")
    print(f"  FAIL: {failed}/{total}")

    if failed > 0:
        print("\n  FAIL 一覧:")
        for r in results:
            if not r.passed:
                detail = f" — {r.detail}" if r.detail else ""
                print(f"    [{r.scenario}] {r.check}{detail}")

    print()
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
