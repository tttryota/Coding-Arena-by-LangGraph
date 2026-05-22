---
type: impl
profile: backend
scope: quiz/summary-test-record
spec: docs/spec/backend/quiz/summary-test-record.md
test_cases: tests/test-cases/backend/quiz/summary-test-record.md
---

## 今回やること
summary-test-record を TDD で実装する

## 対象テストケース
TC仕様書の全テストケース

## 完了条件
- 対象テストケースが全て GREEN
- ruff + mypy がパス
- レビュー通過

## 設計判断
- quiz/application/ に配置
- テスト: quiz/application/test_summary_test_record.py
