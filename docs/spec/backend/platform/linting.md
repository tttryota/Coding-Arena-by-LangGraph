---
feature: linting
status: draft
reviewed_by:
approved_at:
---

## 機能概要

ruff（リント・フォーマット）とmypy（型チェック）でコード品質を保証する。設定はpyproject.tomlに定義済み。

## 振る舞い

### ruff

リントとフォーマットを1ツールで実行する。

- `ruff check .` — リントチェック
- `ruff format .` — コードフォーマット
- line-length: 88
- target-version: py312

### 有効なルールセット

pyproject.tomlで設定済み:

| カテゴリ | ルール | 目的 |
|---------|--------|------|
| E, W, F | pyflakes/pycodestyle | 基本的なエラー・警告 |
| I | isort | import順序 |
| UP | pyupgrade | Python 3.12向けの書き方に統一 |
| B | bugbear | バグになりやすいパターン検出 |
| S | bandit | セキュリティ |
| N | pep8-naming | 命名規則 |
| C901 | mccabe | 複雑度（max 10） |
| PLR0913 | pylint | 引数数制限（max 4） |
| PLR0915 | pylint | 文数制限（max 20） |
| PT | pytest-style | pytestの書き方 |
| BLE | blind-except | bare except禁止 |
| EM | error-messages | エラーメッセージ品質 |
| その他 | COM, PTH, A, RUF, FLY, RET, ARG, SIM, C4, ISC, PIE, TC | 各種コード品質 |

### テストファイルの除外

`**/tests/test_*.py` では以下を除外:
- S101（assert使用）
- N（命名規則）
- PLR0915（文数制限）
- ARG（不要な引数）

### mypy

- strict mode有効
- Python 3.12
- warn_return_any: true
- warn_unused_configs: true

## 技術判断

- ruffを採用する理由: flake8, isort, black等を1ツールに統合。高速。uvとの相性が良い
- strictモードの理由: 型アノテーション必須。個人プロジェクトでも型安全を担保し、LLMによるコード生成の品質チェックにも有効

## 受け入れ基準

- [ ] `ruff check .` がエラー0で通過する
- [ ] `ruff format --check .` がエラー0で通過する
- [ ] `mypy --strict .` がエラー0で通過する
