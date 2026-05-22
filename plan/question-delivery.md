---
type: impl
profile: backend
scope: quiz/question-delivery
spec: docs/spec/backend/quiz/question-delivery.md
test_cases: tests/test-cases/backend/quiz/question-delivery.md
---

## 今回やること
question-delivery (C3 ノード) を TDD で実装する

## 対象テストケース
- TC-01: deliver_question の公開戻り値契約と LLM 呼び出しマッピング
- TC-02: total_questions_asked の初期化と加算
- TC-10: knowledge 形式の確認ポイントで textarea が返る
- TC-11: knowledge_and_practice 形式で code が返り過去問答が client に渡る
- TC-12: セッション再開時に current_point_index に従い続行
- TC-20: 全確認ポイント消化済みで LLM を呼ばず空更新を返す
- TC-21: 深掘りで追加された確認ポイントの出題
- TC-30: LLM リクエスト失敗由来の QuestionDeliveryError が伝播
- TC-31: LLM レスポンスパース失敗由来の QuestionDeliveryError が伝播

## やらないこと
- QuestionDeliveryLlmClient の concrete 実装
- chat_response / input_classification / explanation_generation
- 問題難易度調整
- テンプレート管理

## 完了条件
- 対象テストケースが全て GREEN
- ruff + mypy がパス
- レビュー通過

## 設計判断
- LangGraph ノード関数: deliver_question(state, *, llm) -> dict
- Protocol: QuestionDeliveryLlmClient (generate_question -> QuestionOutput)
- QuestionOutput: frozen dataclass (question_text, answer_type)
- 例外: QuestionDeliveryError (error_code + message + __cause__)
- ConfirmationPoint / QuizAnswerRecord は quiz/domain/session_state.py から import
- テスト: quiz/application/test_question_delivery.py
