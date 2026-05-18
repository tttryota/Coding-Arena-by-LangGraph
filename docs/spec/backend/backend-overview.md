---
feature: backend-overview
status: draft
reviewed_by:
approved_at:
---

## サービス概要

様々なソース（動画・書籍・記事等）で学んだことをObsidianに文書化し、LLMが体系的に整理・理解度チェック・学習支援してくれる個人用学習支援ツール。

### ユーザーができること

**A. 知識ベースの構築（受動的）**

Vault内の設定されたパス配下にノートを書くだけで、システムが定期的に自動取り込みする。取り込み時にLLMがフィードバック（反映先の通知・正確性チェック・改善提案）を生成し、ユーザーは好きなタイミングで確認できる。

**B. ロードマップ生成（ユーザー起点）**

取り込まれたノート群からシステムがトピック候補を提案し、ユーザーが選択するとLLMが学習ロードマップ（大枠→中枠→具体）を生成する。ノートでカバー済みの項目と未着手の項目を可視化し、学習の全体像とゴールを示す。

**C. クイズセッション（メイン体験）**

ロードマップの項目を選んでクイズを開始する。文章またはコードで回答し、LLMが理解度を評価する。深掘り・解説・前提知識の遡りを経て、項目の理解度が判定される。結果はロードマップの進捗に反映される。

**D. 学習状況の把握（参照系）**

ロードマップの進捗、弱点分析、反復学習リマインド、フィードバック一覧を確認できる。

## ユーザー体験の全体フロー

```
ユーザーの日常学習（動画・書籍・記事）
  │
  ▼
Obsidianにノート書く（対象パス配下）
  │
  ▼ 定期バッチ（10〜30分間隔）
A. 知識ベース構築
  取り込み → チャンク分割 → タグ付け → Embedding → DB格納
  → フィードバック生成（蓄積）
  │
  │ ノート群が溜まる
  ▼
B. ロードマップ生成
  トピック候補提案 → 選択 → ロードマップ全生成
  ノートのカバー状況を反映
  │
  │ ロードマップの項目を選ぶ
  ▼
C. クイズセッション
  出題 → 回答(文章/コード) → 評価
  深掘り・解説・前提知識の遡り
  │
  │ 結果が反映される
  ▼
D. 学習状況の把握
  ロードマップ進捗 / 弱点分析 / リマインド / FB一覧
  │
  └──→ C に戻って弱点を復習（循環）
```

## パッケージ構成

DDDアーキテクチャで構成し、汎用基盤と学習支援固有ロジックを分離する。

```
backend/
├── core/                      # 汎用基盤（別リポジトリに切り出し可能）
│   ├── ingestion/             #   取り込みパイプライン
│   ├── llm/                   #   LLMクライアント
│   ├── embedding/             #   Embeddingクライアント
│   ├── vectordb/              #   ベクトルDB操作
│   └── rag/                   #   RAG検索
│
├── domain/                    # 学習支援固有ドメイン
│   ├── roadmap/               #   ロードマップ管理
│   └── quiz/                  #   クイズセッション
│
├── application/               # ユースケース層
│   ├── roadmap/
│   └── quiz/
│
├── infrastructure/            # インフラ層
│   └── rdb/                   #   SQLite
│
└── presentation/              # プレゼンテーション層
    └── api/                   #   FastAPIエンドポイント
```

### 依存方向

```
presentation → application → domain → core
                                ↓
                          infrastructure
```

- `core/` は学習支援に一切依存しない。Obsidianノートの取り込み・分析基盤として他用途（進捗管理・企画等）にも再利用可能
- `domain/` が `core/` を利用する。逆方向の依存は禁止
- タグ付与のプロンプトやチャンク分割戦略は設定/ストラテジーパターンで `core/` に注入する

## 技術スタック

### ランタイム

| レイヤー | 技術 |
|:---|:---|
| 言語 | Python 3.12 |
| API Framework | FastAPI |
| LLM | Codex（app-server経由） |
| Embedding | multilingual-e5-large（ローカル） |
| VectorDB | ChromaDB（ローカル永続化） |
| RDB | SQLite |
| DB ORM | SQLAlchemy + Alembic |
| バリデーション | Pydantic |
| Agent Workflow | LangGraph |
| 設定管理 | pydantic-settings（.env + 環境変数） |
| ログ管理 | structlog（構造化JSON出力） |
| ファイル取り込み | 定期バッチ（10〜30分間隔） |

### 開発ツール

| ツール | 用途 |
|:---|:---|
| uv | 依存管理 |
| ruff | リント / フォーマット |
| mypy | 型チェック（strict） |
| pytest | テスト |

### コンテナ構成

```yaml
services:
  backend:    # FastAPIアプリ（Dockerfile）
  frontend:   # React/Viteアプリ（Dockerfile）
  chromadb:   # 公式イメージ（chromadb/chroma）
```

- SQLite: ファイルベース、ボリュームマウントで永続化（`./data/app.db`）
- ChromaDB: ボリュームマウントで永続化（`./data/chromadb/`）
- Embeddingモデルキャッシュ: ボリュームマウントで永続化（`./data/huggingface/`）
- Obsidian Vault: ホスト側パスを読み取り専用マウント

## ストレージの使い分け

| ストレージ | 用途 | 管理層 |
|:---|:---|:---|
| ChromaDB | チャンク + Embedding（ベクトル検索用） | `core/vectordb/` |
| SQLite | ロードマップ・フィードバック・クイズ結果等の構造化データ | `infrastructure/rdb/` |

## プラットフォーム仕様書へのポインタ

- [data-models](platform/data-models.md) — データモデル定義（Chunk, RoadmapItem, QuizSession, QuizAnswer, IngestionFeedback, SummaryTestResult）
- [docker-compose](platform/docker-compose.md) — コンテナ構成（backend, frontend, chromadb）
- [configuration](platform/configuration.md) — pydantic-settings、環境変数、.env
- [database-migration](platform/database-migration.md) — Alembicマイグレーション
- [linting](platform/linting.md) — ruff + mypy 設定
- [logging](platform/logging.md) — structlog構造化ログ
- [testing](platform/testing.md) — pytest方針・コロケーション配置

## 中枠仕様書へのポインタ

- [ingestion-overview](ingestion/ingestion-overview.md) — 取り込みパイプライン + フィードバック（`core/`、汎用基盤）
- [roadmap-overview](roadmap/roadmap-overview.md) — ロードマップ管理 + 弱点分析（`domain/roadmap/`）
- [quiz-overview](quiz/quiz-overview.md) — クイズセッション + まとめテスト結果（`domain/quiz/`）

※ analyticsグループは廃止。各機能をingestion/roadmap/quizに再配置:
- フィードバック一覧 → ingestion
- 弱点分析 → roadmapの進捗集約に包含
- まとめテスト結果 → quiz
- 反復学習リマインド → フロント側でlast_quiz_atから算出（バックエンド不要）
- 進捗集計 → roadmap-retrievalに包含
