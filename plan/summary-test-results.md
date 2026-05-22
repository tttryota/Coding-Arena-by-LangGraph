---
type: impl
profile: backend
scope: quiz/summary-test-results
spec: docs/spec/backend/quiz/summary-test-results.md
test_cases: tests/test-cases/backend/quiz/summary-test-results.md
---

## 今回やること
summary-test-results を TDD で実装する

## 対象テストケース
TC仕様書の全テストケース

## 完了条件
- 対象テストケースが全て GREEN
- ruff + mypy がパス
- レビュー通過

## 設計判断
- quiz/application/ に配置
- テスト: quiz/application/test_summary_test_results.py
