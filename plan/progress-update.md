---
type: impl
profile: backend
scope: quiz/progress-update
spec: docs/spec/backend/quiz/progress-update.md
test_cases: tests/test-cases/backend/quiz/progress-update.md
---

## 今回やること
progress-update を TDD で実装する

## 対象テストケース
TC仕様書の全テストケース

## 完了条件
- 対象テストケースが全て GREEN
- ruff + mypy がパス
- レビュー通過

## 設計判断
- quiz/application/ に配置
- テスト: quiz/application/test_progress_update.py
