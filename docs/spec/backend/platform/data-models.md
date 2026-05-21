---
feature: data-models
status: approved
reviewed_by: claude
approved_at: 2026-05-21
---

## 機能概要

システム全体で使用するデータモデルの定義。各ドメインの具体仕様書がこのデータ構造を前提とする。

## エンティティ一覧

| エンティティ | ストレージ | 管理層 | 用途 |
|-------------|----------|--------|------|
| Chunk | ChromaDB | `core/vectordb/` | チャンク + Embedding + メタデータ |
| RoadmapItem | SQLite | `infrastructure/rdb/` | ロードマップ階層 + 進捗スコア |
| QuizSession | SQLite | `infrastructure/rdb/` | セッション状態管理（中断・再開対応） |
| QuizAnswer | SQLite | `infrastructure/rdb/` | 個別の問答記録 |
| IngestionFeedback | SQLite | `infrastructure/rdb/` | 取り込み時フィードバック |
| SummaryTestResult | SQLite | `infrastructure/rdb/` | まとめテストのLLM定性分析 |

## Chunk（ChromaDB）

ノートから分割されたテキストチャンク。ベクトル検索の対象。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| id | string | ナチュラルキー: `{source_path}_{chunk_index}` |
| content | string | チャンク本文（Markdownテキスト） |
| embedding | vector | multilingual-e5-largeによるベクトル |
| source_path | string | 元ファイルのパス（Vault相対） |
| chunk_index | int | ファイル内でのチャンク順序 |
| headers | string | 見出し階層（例: "TypeScript > 型システム > ジェネリクス"） |
| tags | list[string] | LLMが付与したタグ |
| created_at | datetime | 取り込み日時 |
| updated_at | datetime | 最終更新日時 |

- ファイル更新時は `source_path` でフィルタして全削除 → 再挿入

## RoadmapItem（SQLite）

ロードマップの項目。固定3段の階層をparent_id方式（隣接リスト）で表現する（ADR-002参照）。

| カラム | 型 | 説明 |
|--------|-----|------|
| id | UUID | 主キー |
| roadmap_id | UUID | どのロードマップに属するか（トピックごとに別） |
| parent_id | UUID / null | 親項目のID（大枠はnull） |
| level | string | "major" / "middle" / "detail" |
| title | string | 項目名 |
| description | string | LLM生成の説明文 |
| order | int | 同階層内での表示順 |
| score | int | 0〜100。ラベル変換はアプリケーション層で実施 |
| last_quiz_at | datetime / null | 最後にクイズを実施した日時 |
| created_at | datetime | 作成日時 |
| updated_at | datetime | 更新日時 |

### スコアのインターフェース

- QuizAnswer.score（個別回答: 0〜100）→ 集約 → RoadmapItem.score（0〜100）
- ラベル変換の閾値はpydantic-settingsで設定可能（デフォルト: 0〜25 not_started / 26〜50 insufficient / 51〜75 partial / 76〜100 sufficient）
- 集約ロジックの詳細は具体仕様書（progress-update.md）で定義
- 中枠・大枠のスコアは配下のdetail項目から算出（DBには保持しない）

## QuizSession（SQLite）

クイズセッションの状態管理。中断・再開を可能にする。

| カラム | 型 | 説明 |
|--------|-----|------|
| id | UUID | 主キー |
| roadmap_item_id | UUID | FK: RoadmapItem。出題対象 |
| status | string | "in_progress" / "completed" / "abandoned" |
| started_at | datetime | 開始日時 |
| completed_at | datetime / null | 終了日時 |

- セッションのタイプ（detail/まとめテスト）はRoadmapItemのlevelから判別
- サマリーや問題数は持たない（QuizAnswerから算出）

## QuizAnswer（SQLite）

個別の問答記録。

| カラム | 型 | 説明 |
|--------|-----|------|
| id | UUID | 主キー |
| session_id | UUID | FK: QuizSession |
| roadmap_item_id | UUID | FK: RoadmapItem |
| question_number | int | セッション内の問題番号 |
| question_text | text | 出題内容 |
| answer_type | string | "textarea" / "code" |
| answer_text | text | ユーザーの回答 |
| score | int | 0〜100（LLM Evaluatorが算出） |
| feedback | text | LLMからのフィードバック |
| answered_at | datetime | 回答日時 |

## IngestionFeedback（SQLite）

ノート取り込み時にLLMが生成するフィードバック。

| カラム | 型 | 説明 |
|--------|-----|------|
| id | UUID | 主キー |
| source_path | string | 関連ノートのパス |
| roadmap_item_id | UUID / null | 反映先のロードマップ項目 |
| title | string | フィードバックの見出し |
| body | text | 内容（正確性チェック・改善提案等） |
| is_read | bool | 確認済みか |
| created_at | datetime | 生成日時 |
| read_at | datetime / null | 確認日時 |

- バックエンドは汎用的な取得API（日付範囲・未確認フィルタ等）を提供
- フロントエンドで日付グルーピング等の表示が可能

## SummaryTestResult（SQLite）

中枠・大枠レベルのまとめテスト結果。LLMによる定性分析を保持する。

| カラム | 型 | 説明 |
|--------|-----|------|
| id | UUID | 主キー |
| session_id | UUID | FK: QuizSession |
| score | int | 0〜100（集計値） |
| analysis | text | LLMによる定性分析（弱点・傾向のコメント） |
| created_at | datetime | 実施日時 |

- まとめテスト完了時にLLMが問答全体を分析して生成
- 「型ガードの使い分けが弱い」のような具体的な示唆を提供

## 設計で不要と判断したもの

| 候補 | 不要の理由 |
|------|-----------|
| roadmap_proposal（改善提案の自動蓄積） | ユーザーが手動で再生成を依頼する形で十分 |
| repetition_reminder（反復リマインドの蓄積） | RoadmapItem.last_quiz_atからフロント側で算出可能 |
| is_deepdive / is_prerequisite（QuizAnswerのフラグ） | 活用場面がない |
| session_type（QuizSession） | RoadmapItemのlevelから判別可能 |
| result_summary（QuizSession） | 活用場面が不明。必要になれば後から追加 |
