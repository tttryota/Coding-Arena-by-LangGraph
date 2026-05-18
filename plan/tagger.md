---
type: impl
profile: backend
scope: ingestion/tagger
spec: docs/spec/backend/ingestion/tagger.md
test_cases: tests/test-cases/backend/ingestion/tagger.md
---

## 今回やること
tagger を TDD で実装する

## 対象テストケース
TC-01 〜 TC-35（全テストケース）

## やらないこと
- LLM クライアント本体の実装（Protocol で定義）
- プロンプト戦略の具体実装（Protocol で定義）
- タグ一覧の永続化

## 完了条件
- 全テストケースが GREEN
- ruff + mypy がパス
- レビュー通過

## 設計判断
- TaggingPromptStrategy は Protocol で定義（DI）
- LlmTagClassifier は Protocol で定義（DI）
- 既存タグの正規化は tagger 本体が担当
- LLM 応答のフィルタリング（候補外タグ排除）は tagger 本体が担当
