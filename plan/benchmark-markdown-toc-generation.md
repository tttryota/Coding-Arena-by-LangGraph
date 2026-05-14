---
profile: backend
benchmark: generation
scope: benchmark/markdown-toc
spec: docs/spec/benchmark/markdown-toc.md
test_cases: tests/test-cases/benchmark/markdown-toc.md
---

## 今回やること
markdown-toc を generation benchmark として実行する。
開始時点で ALREADY_GREEN なら失格とし、既存実装の review-only benchmark と混在させない。

## 対象テストケース
1. `plan/benchmark-markdown-toc.md` と同じ 23 ケース

## やらないこと
- 既存実装あり benchmark の品質比較

## 完了条件
- generation benchmark が RED スタート前提でのみ実行される
- ALREADY_GREEN の場合は失格として終了する
