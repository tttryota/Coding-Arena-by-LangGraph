---
type: impl
profile: backend
scope: quiz/explanation-generation
spec: docs/spec/backend/quiz/explanation-generation.md
test_cases: tests/test-cases/backend/quiz/explanation-generation.md
---

## 今回やること
explanation-generation を TDD で実装する

## 対象テストケース
TC仕様書の全テストケース

## 完了条件
- 対象テストケースが全て GREEN
- ruff + mypy がパス
- レビュー通過

## 設計判断
- quiz/application/ に配置
- テスト: quiz/application/test_explanation_generation.py
