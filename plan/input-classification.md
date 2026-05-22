---
type: impl
profile: backend
scope: quiz/input-classification
spec: docs/spec/backend/quiz/input-classification.md
test_cases: tests/test-cases/backend/quiz/input-classification.md
---

## 今回やること
input-classification ノードの classify_input 関数を TDD で実装する

## 対象テストケース
TC仕様書の全テストケース

## やらないこと
- input_source による後続ノード振り分けテスト（グラフ定義の責務）
- LangGraph ノード登録名の固定化
- InputClassificationLlmClient の concrete 実装

## 完了条件
- 対象テストケースが全て GREEN
- ruff + mypy がパス
- レビュー通過

## 設計判断
- classify_input(state, *, llm) -> dict はノード単体として分類のみ行う
- input_source による後続ノード振り分けはグラフ定義の責務
- テスト: quiz/application/test_input_classification.py
