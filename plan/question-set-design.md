---
type: impl
profile: backend
scope: quiz/question-set-design
spec: docs/spec/backend/quiz/question-set-design.md
test_cases: tests/test-cases/backend/quiz/question-set-design.md
---

## 今回やること
question-set-design (C2 ノード) を TDD で実装する

## 対象テストケース
- TC-01: design_question_set が SessionState から必要情報を読み戻り値の基本形を返す
- TC-02: 確認ポイントリストが生成され各ポイントが ConfirmationPoint DTO で返る
- TC-10: 通常の詳細項目では確認ポイント数が3-5件に収まる
- TC-11: format の公開契約として knowledge_and_practice と knowledge をそのまま返せる
- TC-12: まとめテストでも入力スコープ契約どおりに ConfirmationPoint を返す
- TC-20: description が空でも title のみから確認ポイントを設計できる
- TC-21: 概念的な項目では全確認ポイントが format=knowledge になる
- TC-22: LLM が3-5件を外しても警告して継続する
- TC-30: LLM リクエスト失敗由来の QuestionSetDesignError が伝播する
- TC-31: JSON パース由来の QuestionSetDesignError が伝播する
- TC-32: スキーマ不整合由来の QuestionSetDesignError が伝播する

## やらないこと
- QuestionSetDesignLlmClient の concrete 実装
- 確認ポイントの手動編集
- 問題テンプレート管理
- 難易度段階設定

## 完了条件
- 対象テストケースが全て GREEN
- ruff + mypy がパス
- レビュー通過

## 設計判断
- LangGraph ノード関数: design_question_set(state, *, llm) -> dict
- Protocol: QuestionSetDesignLlmClient (generate_confirmation_points)
- 例外: QuestionSetDesignError (error_code + message + __cause__)
- ConfirmationPoint は quiz/domain/session_state.py から import
- ログは structlog
- テスト: quiz/application/test_question_set_design.py
