---
type: impl
profile: backend
scope: ingestion/chunk-splitter
spec: docs/spec/backend/ingestion/chunk-splitter.md
test_cases: tests/test-cases/backend/ingestion/chunk-splitter.md
---

## 今回やること
chunk-splitter を TDD で実装する

## 対象テストケース
TC-01 〜 TC-34（全テストケース）

## やらないこと
- トークナイザ本体の実装（外部依存としてインターフェースのみ定義）
- 他の ingestion モジュール（tagger, embedder 等）

## 完了条件
- 全テストケースが GREEN
- ruff + mypy がパス
- レビュー通過

## 設計判断
- トークナイザは DI で注入（Protocol で定義）
- 行単位のステートマシンで1パス走査
