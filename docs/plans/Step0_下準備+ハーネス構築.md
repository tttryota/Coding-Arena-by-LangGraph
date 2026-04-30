# 実装計画: プロジェクト下準備 + ハーネス構築

## Context
obsidian-rag-langgraph リポジトリの下準備とハーネスのフル構築。開発計画書（docs/plans/開発計画書.md）の Step 0 に相当。ハーネスが動く状態にしてから Step 1（RAGパイプライン）に入る。docker-compose は不要と確定済み。

## 確定事項（議論で決定済み）
- Python 3.12
- ruff: line-length=88, select=[E,W,F,I,N,UP,B,A,S,T20,RUF,COM,PTH], ignore=[D,ANN,ERA,FIX,TD]
- mypy: strict=true
- ruff format で black/isort を代替
- フロントエンド: eslint + prettier（Phase 3で設定）

## 作成するファイル一覧

### Part A: ディレクトリ骨格 + 設定ファイル

#### A-1. ディレクトリ構造
```
obsidian-rag-langgraph/
├── backend/
│   ├── pyproject.toml
│   ├── __init__.py
│   ├── ingestion/
│   │   └── __init__.py
│   ├── agents/
│   │   └── __init__.py
│   ├── api/
│   │   └── __init__.py
│   └── db/
│       └── __init__.py
├── frontend/                    # (空、Phase 3 で初期化)
├── .harness/
│   ├── harness.py               # オーケストレーター本体
│   ├── lint_guard.py             # リンター強制ガード
│   ├── drift_guard.py            # 迷走検知ガード
│   ├── review_orchestrator.py    # レビュー制御（3ステップ）
│   ├── logger.py                 # 構造化ログ
│   ├── review-criteria-common.md
│   ├── review-criteria-backend.md
│   └── review-criteria-frontend.md
├── docs/
│   ├── overview/                # (既存)
│   ├── plans/                   # (既存)
│   └── spec/
│       ├── TEMPLATE.md
│       ├── ingestion/
│       ├── agents/
│       ├── api/
│       └── frontend/
├── tests/
│   ├── test-cases/
│   │   ├── TEMPLATE.md
│   │   ├── ingestion/
│   │   ├── agents/
│   │   ├── api/
│   │   └── frontend/
│   ├── backend/
│   └── frontend/
├── plan/                        # 実装計画ファイル置き場
├── logs/                        # (.gitignore済み)
├── CLAUDE.md
└── .gitignore
```

#### A-2. CLAUDE.md
開発計画書 3.2 の内容。docker-compose 記載は除外。

#### A-3. backend/pyproject.toml
```toml
[project]
name = "obsidian-rag-langgraph"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []

[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = [
    "E", "W", "F", "I", "N", "UP", "B", "A",
    "S", "T20", "RUF", "COM", "PTH",
]
ignore = ["D", "ANN", "ERA", "FIX", "TD"]

[tool.ruff.format]
quote-style = "double"

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
```

#### A-4. レビュー観点ファイル
- `.harness/review-criteria-common.md` — 開発計画書 6.1
- `.harness/review-criteria-backend.md` — 開発計画書 6.2
- `.harness/review-criteria-frontend.md` — 開発計画書 6.3（Phase 3で詳細化の注記付き）

#### A-5. テンプレート
- `docs/spec/TEMPLATE.md` — 仕様書テンプレート
- `tests/test-cases/TEMPLATE.md` — テストケーステンプレート

#### A-6. .gitignore 更新
logs/, .env, chroma_data/ 等が含まれていることを確認。

---

### Part B: ハーネス本体

#### B-1. .harness/logger.py — 構造化ログ
- HarnessLogger クラス
- logs/{timestamp}_{task_name}/ にJSONLでイベント記録
- 全コンポーネントがこのloggerを使用

#### B-2. .harness/lint_guard.py — リンター強制ガード
- 変更ファイルに対して ruff check + ruff format + mypy を実行
- エラー0 + 警告0を強制
- 差分かどうかに関わらずファイル全体をチェック
- 3回修正しても残る場合は DriftException

#### B-3. .harness/drift_guard.py — 迷走検知ガード
- 同一テストリトライ3回 → DriftException
- 同一エラー3回連続 → DriftException
- タスク経過15分 → DriftException
- ファイル巻き戻し2回 → DriftException
- diff行数がスコープの3倍超 → DriftException
- DriftException発生時のエスカレーション段階:
  - Level 1: Claude Code に別アプローチ指示
  - Level 2: Codex に相談（レート制限時スキップ）
  - Level 3: 人間にエスカレーション

#### B-4. .harness/review_orchestrator.py — レビュー制御

**Codex使用可能時（3ステップ）：**
```
Step 1: セルフレビュー（レビュー観点チェック）
  → 指摘あり → 修正 → リンター+テスト強制 → Step 1 再実行
  → 指摘なし ↓

Step 2: セルフレビュー（バグ・品質チェック）
  → 指摘あり → 修正 → リンター+テスト強制 → Step 2 再実行
  → 指摘なし ↓

Step 3: Codex レビュー
  → 指摘あり → 修正 → リンター+テスト強制 → Step 3 再実行
  → 指摘なし → 完了
```

**Codex使用不可時（2ステップ）：**
```
Step 1: セルフレビュー（レビュー観点チェック）
  → 指摘あり → 修正 → リンター+テスト強制 → Step 1 再実行
  → 指摘なし ↓

Step 2: セルフレビュー2体（バグ・品質チェック）+ 突合
  → 指摘あり → 修正 → リンター+テスト強制 → Step 2 再実行
  → 指摘なし → 完了
```

**各ステップ共通の修正後フロー：**
```
修正実施
  → ruff check + ruff format（ゼロ違反）
  → mypy --strict（ゼロエラー）
  → テスト全件パス
  → 同じステップの再レビュー
  → 3サイクルで収束しなければ迷走ガード発動
```

**2体突合ロジック（Codex不可時のStep 2）：**
- Agent A, B を並列実行（独立コンテキスト）
- 両方指摘 → 修正必須
- 片方のみ → 重大度判定 → 自律修正を試みる
  - 修正後テストGREEN → 完了
  - テスト壊れた or 仕様矛盾 → 人間判断

#### B-5. .harness/harness.py — オーケストレーター本体

**Design Flow:**
```
要件 → claude -p で仕様書生成 → レビュー → 承認
     → claude -p でテストケース生成 → レビュー → 承認
```

**Impl Flow:**
```
計画ファイル読み込み
  → ガード（仕様書+テストケースの存在・承認チェック）
  → TDDサイクル（テストケースを1つずつ）
    → レビュー観点注入済みpromptで claude -p 実行
    → リンター強制
    → RED確認 → 実装 → GREEN確認
  → Phase完了ごとにレビュー（B-4のフロー）
  → 全Phase完了 → 最終レビュー
```

---

## 作成しないもの
- docker-compose.yml（不要と確定）
- frontend/ 配下のpackage.json等（Phase 3 で初期化）

## 実装順序
1. Part A（ディレクトリ骨格 + 設定ファイル）
2. Part B-1（logger）— 他の全コンポーネントが依存
3. Part B-2（lint_guard）
4. Part B-3（drift_guard）
5. Part B-4（review_orchestrator）
6. Part B-5（harness.py）— 全部を統合

## 検証
- `ruff check backend/` がエラー0で通ること
- `mypy backend/` がエラー0で通ること
- ディレクトリ構造が開発計画書 2.2 と一致すること（docker-compose除く）
- CLAUDE.md が配置されていること
- ハーネスの各コンポーネントが単体で動作すること（簡易テスト）
- レビューフローが3ステップ/2ステップ両方で動作すること
