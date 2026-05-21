---
feature: logging
status: approved
reviewed_by: claude
approved_at: 2026-05-21
---

## 機能概要

structlogで構造化ログ（JSON形式）を出力する。取り込みバッチの実行状況、クイズセッションのイベント、エラー等をトレース可能にする。

## 振る舞い

### 基本動作

全てのログをJSON形式で出力する。各ログエントリにはタイムスタンプ、イベント名、関連するコンテキスト情報が含まれる。

### ログ出力の例

```json
{"timestamp": "2026-05-18T10:00:00", "event": "batch_started", "level": "info"}
{"timestamp": "2026-05-18T10:00:01", "event": "file_diff_detected", "level": "info", "new": 1, "changed": 2, "deleted": 0}
{"timestamp": "2026-05-18T10:00:05", "event": "chunk_created", "level": "info", "source_path": "study/ts/generics.md", "chunks": 3}
{"timestamp": "2026-05-18T10:00:10", "event": "tagging_completed", "level": "info", "source_path": "study/ts/generics.md", "tags": ["TypeScript"]}
{"timestamp": "2026-05-18T10:00:30", "event": "batch_completed", "level": "info", "duration_seconds": 30}
{"timestamp": "2026-05-18T10:15:00", "event": "quiz_session_started", "level": "info", "session_id": "...", "roadmap_item": "ジェネリクスの基本構文"}
{"timestamp": "2026-05-18T10:15:05", "event": "llm_call", "level": "info", "purpose": "answer_evaluation", "duration_ms": 1200}
{"timestamp": "2026-05-18T10:20:00", "event": "error", "level": "error", "error": "ChromaDB connection refused", "traceback": "..."}
```

### ログレベル

- **info**: 通常のイベント（バッチ開始/完了、セッション開始等）
- **warning**: 注意すべき状況（LLMレスポンスのパース失敗でリトライ等）
- **error**: エラー（DB接続失敗、LLM呼び出し失敗等）

## 技術判断

- structlogを採用する理由: 構造化ログ（JSON出力）が標準。コンテキスト付きログが簡単に書ける。開発計画書のJSONLイベントログ設計と相性が良い

## スコープ外

- ログの永続化（ファイル出力やログ管理サービスへの転送）
- ログのローテーション
- ログの検索・分析ダッシュボード

## 受け入れ基準

- [ ] ログがJSON形式で出力される
- [ ] 各ログにタイムスタンプとイベント名が含まれる
- [ ] コンテキスト情報（ファイルパス、セッションID等）がログに含まれる
- [ ] エラー時にトレースバックが含まれる
