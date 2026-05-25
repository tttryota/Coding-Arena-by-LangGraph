# TODO — プロジェクト完成像からの逆算

## 完成像

ユーザーが一気通貫で体験できる状態:

1. Vault にノートを書く → 自動取り込み → フィードバック確認
2. トピック選択 → ロードマップ生成 → 項目調整
3. ロードマップ項目を選んでクイズ開始 → 対話的問答 → 進捗反映
4. 進捗・弱点・フィードバックをダッシュボードで確認

---

## Phase 0: 仕様精査（Quiz 実装前に必須）

| タスク | 理由 |
|---|---|
| SessionState の TypedDict 定義 | quiz-overview.md に追記。CLAUDE.md に「SessionState を基本」とあるが仕様書に定義がない |
| LangGraph グラフ構造の定義 | ノード一覧、conditional edge（next/deepdive/complete）、入力分類ノードの振る舞い |
| 仕様書の不整合解消 | session-lifecycle の status 2値 vs data-models の 3値。CLAUDE.md の LLM 記述を Codex app-server に更新 |
| quiz 仕様書 8 本を ready に | session-lifecycle, question-set-design, question-delivery, answer-evaluation, explanation-generation, progress-update, summary-test-record, summary-test-results |

## Phase 0.5: ディレクトリ構成リファクタ（DDD 層分離）

```
backend/
├── infrastructure/          # 横断基盤（config, logging, rdb）— 変更なし
├── ingestion/
│   ├── domain/              # chunk_splitter — 変更なし
│   ├── application/         # NEW: batch pipeline orchestration
│   └── infrastructure/      # concrete adapters
├── roadmap/
│   ├── domain/              # NEW: 純粋ロジック（バリデーション、ツリー操作等）
│   ├── application/         # NEW: generation flow
│   └── infrastructure/      # concrete adapters
├── quiz/
│   ├── domain/              # NEW: SessionState, 各ノードのビジネスロジック
│   ├── application/         # NEW: LangGraph グラフ定義
│   └── infrastructure/      # NEW: concrete adapters（LLM, RDB Store, RAG）
└── shared/                  # テスト共有ヘルパー — 変更なし
```

方針:
- `{機能}/infrastructure/` の Protocol + ドメインロジック → `domain/` に移動
- `{機能}/infrastructure/` の concrete 実装 → `infrastructure/` に残留
- `application/` は各機能のオーケストレーション
- テストはコロケーション維持
- CLAUDE.md のディレクトリ規約を更新

## Phase 1: Quiz 層 全 8 モジュール + LangGraph グラフ

各モジュールは最初から LangGraph ノードとして設計。SessionState を共有する密結合のため、グラフ定義と並行して進める。

| # | タスク | 概要 |
|---|---|---|
| 1-1 | LangGraph グラフ骨格 + SessionState | quiz/application/graph.py にグラフ定義 |
| 1-2 | session-lifecycle | セッション開始・進行・再開・完了管理 |
| 1-3 | question-set-design | 確認ポイントリスト設計 |
| 1-4 | question-delivery | 過去問答文脈を踏まえた問題文生成 |
| 1-5 | answer-evaluation | 理解度判定 + conditional edge (next/deepdive/complete) |
| 1-6 | explanation-generation | RAG ノート参照 + 解説生成 |
| 1-7 | 入力分類ノード | ユーザー入力が回答/質問/解説依頼かを判断 |
| 1-8 | progress-update | セッション完了時の総合評価 → score 更新 |
| 1-9 | summary-test-record | 中枠・大枠テスト結果の定性分析保存 |
| 1-10 | summary-test-results | まとめテスト結果取得 API |

## Phase 2: Concrete 接続 + Presentation 層

| # | タスク | 概要 |
|---|---|---|
| 2-1 | LLM Concrete | Codex app-server ラッパー |
| 2-2 | RAG Concrete | ChromaDB ベクトル検索 |
| 2-3 | RDB Store Concrete 群 | SQLAlchemy Protocol 実装 |
| 2-4 | FastAPI 基盤 + 全エンドポイント | Quiz / Roadmap / Ingestion の API |
| 2-5 | Embedder Concrete | multilingual-e5-large ラッパー |
| 2-6 | ChunkStore Concrete | ChromaDB クライアント |
| 2-7 | ジョブスケジューラ Concrete | roadmap-generation の非同期実行基盤 |
| 2-8 | Ingestion feedback 統合 | ingestion_feedback を batch_executor に組み込み |

## Phase 3: Frontend

| タスク | 概要 |
|---|---|
| プロジェクト初期化 | Vite + React + TypeScript + shadcn/ui + TanStack Query + Zustand |
| ロードマップ画面 | ツリー表示、進捗バー、項目 CRUD |
| クイズ画面 | 問題表示、回答入力（文章/コード）、チャット UI |
| ダッシュボード | 進捗一覧、フィードバック確認 |

## Phase 4: 結合テスト + 運用整備

| タスク | 概要 |
|---|---|
| E2E テスト | 取り込み → ロードマップ → クイズ → 進捗反映の一気通貫 |
| LLM プロンプトチューニング | 出題品質、評価精度の調整 |

---

## 完了済み

| 層 | モジュール | 状態 |
|---|---|---|
| ingestion | chunk-splitter, tagger, file-diff-detector, embedder, chroma-chunk-store, batch-scheduler, ingestion-feedback, feedback-listing | develop |
| roadmap | roadmap-persistence, roadmap-retrieval | develop |
| roadmap | topic-listing | PR #4 |
| roadmap | roadmap-item-crud | PR #5 |
| roadmap | roadmap-generation | PR #6 |
| platform | config, logging, rdb (models + migration), docker-compose | develop |
| quiz 仕様 | Phase 0 仕様精査完了（SessionState定義、グラフ構造定義、不整合解消、8仕様書ready化） | develop |
| quiz リファクタ | Phase 0.5 ディレクトリ構成リファクタ（DDD 3層分離） | develop |
| quiz | Phase 1 全10モジュール実装（session-state, session-lifecycle, question-set-design, question-delivery, answer-evaluation, input-classification, explanation-generation, progress-update, summary-test-record, summary-test-results） | develop |

## 不要と判断済み

| 項目 | 理由 |
|---|---|
| A6 ロードマップマッピング | RAG で都度検索で代替 |
| B6 改善提案蓄積 | ユーザー手動 CRUD で代替 |
| CI/CD | 個人ツールのため不要 |

## 設計上の重要判断（Phase 0 で確定要）

1. LangGraph グラフは `quiz/application/` に置く
2. 各モジュールは最初から LangGraph ノードとして設計する
3. SessionState を先に定義して全ノードの入出力契約を固める
4. CLAUDE.md の LLM 記述を Codex app-server に更新する
