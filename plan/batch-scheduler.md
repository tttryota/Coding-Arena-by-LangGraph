---
type: impl
profile: backend
scope: ingestion/batch-scheduler
spec: docs/spec/backend/ingestion/batch-scheduler.md
test_cases: tests/test-cases/backend/ingestion/batch-scheduler.md
---

## 今回やること
batch-scheduler を TDD で実装する

## 対象テストケース
- TC-01: 差分ゼロ時は skipped_no_diff を返しA2〜A5を呼ばない
- TC-02: 削除1件・新規1件・更新失敗1件を completed_with_errors として集約
- TC-03: start()は待機なしで trigger=startup の初回実行を1回開始
- TC-10: deleted→new→updatedの順で各一覧内は辞書順昇順
- TC-11: 新規ファイルは load→split→tag→embed→upsert の順
- TC-12: 更新ファイルはA4後に旧チャンク削除してからupsert
- TC-13: 新規ファイルのsplit結果が空なら保存なしで成功
- TC-14: 更新ファイルのsplit結果が空なら旧チャンク削除後に成功
- TC-15: 単一ファイル失敗はfailed_filesに集約し他ファイル継続
- TC-16: 実行中の追加run_once要求はskipped_already_running
- TC-20: 構成不正はBatchSchedulerConfigErrorを送出
- TC-21: startup長引きでもtick側はskipped_already_running
- TC-22: stop()後は新しいinterval実行を開始しない
- TC-23: updated_filesのファイルがload時に消えていた場合step=load失敗
- TC-24: 更新ファイルの旧チャンク削除失敗はstep=delete_old_chunks
- TC-25: 更新ファイルの旧チャンク削除成功後upsert失敗はstep=upsert
- TC-30: A1自体の失敗はstatus=failedで返し例外送出しない
- TC-31: stop()なしでstart()2回はBatchSchedulerAlreadyStartedError
- TC-32: 成功・失敗・完了のstructlogイベント名と必須キー
- TC-33: スキップ系のstructlogイベント名と必須キー

## やらないこと
- A6以降のロードマップマッピング・フィードバック生成
- 複数プロセス・複数ホスト間の分散ロック
- 失敗ファイルの同一バッチ内リトライ
- ファイル単位の並列取り込み

## 完了条件
- 対象テストケースが全て GREEN
- ruff + mypy がパス
- レビュー通過

## 設計判断
- 依存モジュールはProtocol DIで注入（DiffDetector, MarkdownLoader, Splitter, Tagger, Embedder, ChunkStoreWriter）
- 全ファイルを infrastructure/ に配置（harness sourceLayout準拠）
- 3モジュール構成: batch_scheduler_types.py, batch_executor.py, periodic_batch_scheduler.py
- run_once()は運用失敗をBatchRunSummary.statusに集約し例外送出しない
- 更新ファイルはA4完了後に旧チャンク削除（データ欠損窓の最小化）
