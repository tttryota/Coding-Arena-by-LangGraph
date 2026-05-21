---
feature: testing
status: approved
reviewed_by: claude
approved_at: 2026-05-21
---

## 機能概要

pytestによるテスト方針とディレクトリ配置を定義する。

## 振る舞い

### テストファイルの配置

コロケーション方式。テストファイルをソースファイルと同じディレクトリに配置する。

```
ingestion/domain/chunk_splitter.py
ingestion/domain/test_chunk_splitter.py    ← 同じディレクトリ

roadmap/roadmap_generation.py
roadmap/test_roadmap_generation.py
```

### ファイル命名規則

- テストファイル: `test_{対象モジュール名}.py`
- テスト関数: `test_{対象}_{条件}_{期待結果}`

### pytest設定

pyproject.tomlに設定:
```toml
[tool.pytest.ini_options]
testpaths = ["."]
```

### テストの種類

- **ユニットテスト**: 単一関数・クラスの振る舞いを検証。外部依存はモック
- **結合テスト**: 複数モジュールの連携を検証。DB・LLM等の外部依存はモック or テスト用インスタンス

## 技術判断

- コロケーション方式の理由: ソースとテストが同じ場所にあるため、何のテストかすぐわかる。ファイル移動時もテストが一緒に移動する
- testpathsを明示する理由: テスト収集の範囲が明確

## スコープ外

- E2Eテスト（フロントエンド〜バックエンド統合）
- パフォーマンステスト
- テストカバレッジの目標値設定

## 受け入れ基準

- [ ] pytestが全テストファイルを収集・実行できる
- [ ] テストファイルがソースと同じディレクトリに配置される
- [ ] テスト関数が命名規則に従っている
