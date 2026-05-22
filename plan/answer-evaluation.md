---
type: impl
profile: backend
scope: quiz/answer-evaluation
spec: docs/spec/backend/quiz/answer-evaluation.md
test_cases: tests/test-cases/backend/quiz/answer-evaluation.md
---

## 今回やること
answer-evaluation (C4 ノード) を TDD で実装する

## 対象テストケース
- TC-01: evaluate_answer の公開戻り値契約と LLM 引数マッピング
- TC-02: answers への QuizAnswerRecord 追記（既存保持 + 1件追加）
- TC-10: next_action=next で current_point_index が +1
- TC-11: next_action=deepdive で confirmation_points 末尾追記 + index +1
- TC-12: next_action=complete で current_point_index が完了境界
- TC-13: input_type=answer が常に設定される（form 経路の正規化）
- TC-20: 20問収束シグナル（total_questions_asked >= 20）で LLM に渡す
- TC-30: LLM リクエスト失敗の AnswerEvaluationError 伝播
- TC-31: LLM レスポンスパース失敗の AnswerEvaluationError 伝播

## やらないこと
- AnswerEvaluationLlmClient の concrete 実装
- コード実行による正誤判定
- 回答比較評価・盗用検出

## 完了条件
- 対象テストケースが全て GREEN
- ruff + mypy がパス
- レビュー通過

## 設計判断
- LangGraph ノード関数: evaluate_answer(state, *, llm) -> dict
- Protocol: AnswerEvaluationLlmClient (evaluate_answer -> EvaluationOutput)
- EvaluationOutput: frozen dataclass (next_action, score, feedback, deepdive_points)
- 例外: AnswerEvaluationError (error_code + message + __cause__)
- テスト: quiz/application/test_answer_evaluation.py
