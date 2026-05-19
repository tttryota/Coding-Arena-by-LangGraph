---
type: impl
profile: backend
scope: ingestion/file-diff-detector
spec: docs/spec/backend/ingestion/file-diff-detector.md
test_cases: tests/test-cases/backend/ingestion/file-diff-detector.md
---

## 今回やること
file-diff-detector を TDD で実装する

## 対象テストケース
TC-01 〜 TC-35（全テストケース）

## やらないこと
- state_store の具体実装（Protocol で定義）
- ファイルシステムの抽象化（os/pathlib を直接使用）

## 完了条件
- 全テストケースが GREEN
- ruff + mypy がパス
- レビュー通過

## 設計判断
- StateStore は Protocol で定義（DI）
- パスは pathlib.Path で扱う
- 相対パスは POSIX 形式で返す
