---
feature: ingestion/batch-scheduler
status: ready
---

# 概要

- この機能が解決する課題:
  Obsidian Vault からの取り込みパイプライン A1〜A5 を 1 回実行し、差分がある Markdown だけを再取り込みできるようにする。1 ファイルの失敗でバッチ全体を停止させない。
- 利用者・呼び出し元・前提条件:
  呼び出し元はアプリケーション起動処理、または同等のライフサイクル管理コンポーネントを想定する。対象ディレクトリは Obsidian Vault 内の Markdown 取り込み対象ディレクトリであり、A1 `FileDiffDetector`、A2 `ChunkSplitter`、A3 `ChunkTagger`、A4 `Embedder`、A5 `ChunkStore` はいずれも Protocol ベースで DI されることを前提とする。構造化ログは `structlog` を用いる。

# 入出力

- 入力:
  `IngestionBatchScheduler` は以下の操作を提供する。
  - `run_once(trigger: BatchTrigger) -> BatchRunSummary`
    - `BatchTrigger` は `"startup"` または `"interval"`。
    - 実行に必要な注入依存は以下とする。
      - `target_path: str | Path`
      - `diff_detector: FileDiffDetector`
      - `markdown_loader: VaultMarkdownLoader`
      - `chunk_splitter: ChunkSplitter`
      - `chunk_tagger: ChunkTagger`
      - `embedder: Embedder`
      - `chunk_store: ChunkStore`
- 出力:
  - `BatchRunSummary`
    - `status: Literal["completed", "completed_with_errors", "skipped_no_diff", "failed"]`
    - `trigger: Literal["startup", "interval"]`
    - `new_count: int`
      A1 が返した `new_files` 件数。
    - `updated_count: int`
      A1 が返した `updated_files` 件数。
    - `deleted_count: int`
      A1 が返した `deleted_files` 件数。
    - `deleted_success_count: int`
      `deleted_files` のうち A5 削除が成功した件数。
    - `ingest_target_count: int`
      `new_files + updated_files` の合計件数。
    - `ingested_success_count: int`
      A2〜A5 まで完了した新規・更新ファイル件数。
    - `failed_file_count: int`
      ファイル単位で失敗した件数。`deleted_files` 側の削除失敗も含む。
    - `failed_files: list[FailedFileSummary]`
      - `source_path: str`
      - `action: Literal["delete", "ingest_new", "ingest_updated"]`
      - `step: Literal["load", "split", "tag", "embed", "delete_old_chunks", "delete_removed_file", "upsert"]`
      - `error_type: str`
    - `stored_chunk_count: int`
      A5 `upsert_chunks(...)` で保存成功したチャンク総数。
  - `run_once(...)` がファイル単位の失敗を検知した場合でも、その失敗は `failed_files` に集約し、処理可能な残りファイルの実行は継続する。
- エラー:
  送出する例外の型名と発生条件を定義する。
  例外型はテストで使用されるため、型名を具体的に指定すること。
  実装詳細ではなく、呼び出し元との契約として記述する。
  - `BatchSchedulerConfigError`: `target_path` が空であるなど、スケジューラ構成が不正な場合
  - `run_once(...)` の A1〜A5 実行失敗は例外として送出せず、ファイル単位失敗は `failed_files`、バッチ全体の継続不能な失敗は `status="failed"` として返す

# 具体例

代表的な入力と、それに対して期待される出力をデータ例で示す。
テストケース生成やレビューで曖昧さが出ないよう、入力・出力ともに具体値で書く。

## 例1

- 入力:
  - `run_once(trigger="startup")`
  - `diff_detector.detect("/vault/study")` の返却値:
    ```yaml
    new_files: []
    updated_files: []
    deleted_files: []
    new_count: 0
    updated_count: 0
    deleted_count: 0
    ```
- 期待される出力:
  ```yaml
  status: skipped_no_diff
  trigger: startup
  new_count: 0
  updated_count: 0
  deleted_count: 0
  deleted_success_count: 0
  ingest_target_count: 0
  ingested_success_count: 0
  failed_file_count: 0
  failed_files: []
  stored_chunk_count: 0
  ```

## 例2

- 入力:
  - `run_once(trigger="interval")`
  - `diff_detector.detect("/vault/study")` の返却値:
    ```yaml
    new_files:
      - "docker/compose.md"
    updated_files:
      - "typescript/generics.md"
    deleted_files:
      - "python/contextmanager.md"
    new_count: 1
    updated_count: 1
    deleted_count: 1
    ```
  - `chunk_store.delete_by_source_path("python/contextmanager.md")` は成功
  - `docker/compose.md` は A2〜A5 が成功し、2 チャンク保存される
  - `typescript/generics.md` は A2 と A3 は成功し、A4 `embed(...)` で `EmbeddingModelCallError` が発生する
- 期待される出力:
  ```yaml
  status: completed_with_errors
  trigger: interval
  new_count: 1
  updated_count: 1
  deleted_count: 1
  deleted_success_count: 1
  ingest_target_count: 2
  ingested_success_count: 1
  failed_file_count: 1
  failed_files:
    - source_path: "typescript/generics.md"
      action: ingest_updated
      step: embed
      error_type: "EmbeddingModelCallError"
  stored_chunk_count: 2
  ```

## 例3

- 入力:
  - `run_once(trigger="interval")`
  - `diff_detector.detect("/vault/study")` の返却値:
    ```yaml
    new_files: []
    updated_files:
      - "notes/empty.md"
    deleted_files: []
    new_count: 0
    updated_count: 1
    deleted_count: 0
    ```
  - `markdown_loader.load(...)` は `"---\ntitle: only meta\n---\n"` を返す
  - `chunk_splitter.split(...)` は `[]` を返す
  - `chunk_store.delete_by_source_path("notes/empty.md")` は成功
- 期待される出力:
  ```yaml
  status: completed
  trigger: interval
  new_count: 0
  updated_count: 1
  deleted_count: 0
  deleted_success_count: 0
  ingest_target_count: 1
  ingested_success_count: 1
  failed_file_count: 0
  failed_files: []
  stored_chunk_count: 0
  ```

# 主要ルール

1. 差分なし時の短絡終了:
   - 条件:
     A1 `FileDiffDetector` の結果で `new_count == 0`、`updated_count == 0`、`deleted_count == 0` の場合。
   - 振る舞い:
     A2〜A5 は 1 回も呼び出さず、`status="skipped_no_diff"` を返す。
2. 削除ファイルの処理順序:
   - 条件:
     `deleted_files` が 1 件以上ある場合。
   - 振る舞い:
     `deleted_files` を辞書順昇順で処理し、各 `source_path` に対して A5 `chunk_store.delete_by_source_path(source_path)` を 1 回呼ぶ。1 件失敗しても残りの削除対象および新規・更新ファイル処理は継続する。
3. 新規ファイルの取り込み:
   - 条件:
     `new_files` に含まれるファイルを処理する場合。
   - 振る舞い:
     各 `source_path` を辞書順昇順で処理し、`markdown_loader.load` → A2 `chunk_splitter.split` → A3 `chunk_tagger.tag` → A4 `embedder.embed` → A5 `chunk_store.upsert_chunks` の順に実行する。A5 成功時点でそのファイルを取り込み成功 1 件として数える。
4. 更新ファイルの差し替え:
   - 条件:
     `updated_files` に含まれるファイルを処理する場合。
   - 振る舞い:
     各 `source_path` を辞書順昇順で処理し、まず `markdown_loader.load`、A2、A3、A4 を完了させる。A4 まで成功した後に `chunk_store.delete_by_source_path(source_path)` を呼び、成功した場合のみ A5 `upsert_chunks(...)` を呼ぶ。
5. 1 ファイル失敗時の継続:
   - 条件:
     削除・新規取り込み・更新差し替えのいずれかで、単一ファイルに対する `load`、`split`、`tag`、`embed`、`delete_old_chunks`、`delete_removed_file`、`upsert` のいずれかが失敗した場合。
   - 振る舞い:
     そのファイルを `failed_files` に記録し、バッチ全体は継続する。失敗したファイルを同一バッチ内で再試行しない。最終 `status` は他に成功ファイルがあっても `completed_with_errors` とする。
6. バッチ全体の継続不能失敗:
   - 条件:
     A1 `diff_detector.detect(...)` 自体が失敗した、または `BatchRunSummary` を構築できないなど、ファイル単位へ分解できない失敗が発生した場合。
   - 振る舞い:
     その `run_once(...)` は `status="failed"` を返す。A2〜A5 の未着手ファイルは処理しない。例外は呼び出し元へ送出しない。
7. 空チャンク結果の扱い:
   - 条件:
     A2 `chunk_splitter.split(...)` の結果が空リストである場合。
   - 振る舞い:
     新規ファイルでは A3・A4・A5 `upsert_chunks(...)` を呼ばず、そのファイルを成功として扱う。更新ファイルでは A5 `delete_by_source_path(source_path)` を実行し、旧チャンクを削除したうえで成功として扱う。
8. structlog による構造化ログ:
   - 条件:
     バッチ開始、差分なしスキップ、ファイル成功、ファイル失敗、バッチ完了の各タイミング。
   - 振る舞い:
     `structlog` でイベント名を固定して出力する。少なくとも以下を含める。
     - バッチ開始: `event="ingestion_batch_started"`, `trigger`, `target_path`
     - 差分なし: `event="ingestion_batch_skipped_no_diff"`, `trigger`, `target_path`, `new_count`, `updated_count`, `deleted_count`
     - ファイル成功: `event="ingestion_batch_file_completed"`, `source_path`, `action`, `stored_chunk_count`
     - ファイル失敗: `event="ingestion_batch_file_failed"`, `source_path`, `action`, `step`, `error_type`
     - バッチ完了: `event="ingestion_batch_completed"`, `status`, `trigger`, `new_count`, `updated_count`, `deleted_count`, `deleted_success_count`, `ingested_success_count`, `failed_file_count`, `stored_chunk_count`

# 境界条件

- ケース:
  - A1 では `updated_files` に含まれていたが、A2 実行前に実ファイルが削除または移動され、`markdown_loader.load(...)` が失敗する。
  - 振る舞い:
    そのファイルを `step="load"` の失敗として `failed_files` に記録し、残りファイル処理を継続する。
  - 理由:
    Obsidian の保存・移動タイミングとバッチ検出タイミングの競合を吸収するため。
- ケース:
  - 更新ファイルで A4 までは成功したが、`delete_by_source_path(source_path)` が失敗する。
  - 振る舞い:
    `step="delete_old_chunks"` の失敗として記録し、A5 `upsert_chunks(...)` は呼ばない。
  - 理由:
    旧チャンクが残ったまま新チャンクだけを保存すると、同一 `source_path` 配下でチャンク整合性が壊れるため。
- ケース:
  - 更新ファイルで `delete_by_source_path(source_path)` 成功後に A5 `upsert_chunks(...)` が失敗する。
  - 振る舞い:
    `step="upsert"` の失敗として記録し、そのファイルは当該バッチ終了時点でチャンク未保存状態のままでよい。
  - 理由:
    A5 の公開契約が `source_path` 単位の削除と upsert だけであり、同一バッチ内での原子的ロールバックは保証しないため。
- ケース:
  - 新規ファイルまたは更新ファイルの分割結果が空である。
  - 振る舞い:
    新規ファイルは保存なしで成功、更新ファイルは既存チャンク削除後に保存なしで成功とする。
  - 理由:
    フロントマターのみ、または実質空ファイルへ変化したケースを自然に表現するため。
- ルール間の相互作用:
  まず A1 を実行し、`差分なし時の短絡終了` を評価する。差分ありの場合は `削除ファイルの処理順序` を先に適用し、その後 `新規ファイルの取り込み`、`更新ファイルの差し替え` を順に適用する。各ファイル内では `1 ファイル失敗時の継続` が優先され、ファイル単位へ分解できない失敗に限って `バッチ全体の継続不能失敗` を適用する。

# 非機能・制約

- 性能:
  - 差分なしの場合、A1 以外の高コスト処理を呼ばずに終了すること。
  - 処理順は決定的であり、`deleted_files`、`new_files`、`updated_files` はそれぞれ辞書順昇順で実行すること。
- 可観測性:
  - `structlog` のイベント名と主要キーが固定され、機械集計可能であること。
  - 少なくともバッチ単位の成功・失敗・スキップ件数と、ファイル単位の失敗箇所がログから追跡できること。
- 外部依存:
  - A1 `FileDiffDetector`
  - A2 `ChunkSplitter`
  - A3 `ChunkTagger`
  - A4 `Embedder`
  - A5 `ChunkStore`
  - Markdown 実ファイル本文の読み込みを行う `VaultMarkdownLoader`
  - `structlog`

# モジュール構成

design 時に、各モジュールが概ね 200-300 行に収まるかを責務単位で概算し、実装の切り方を先に決める。
厳密な計算式は不要だが、例外型・データ構造・主要ルール・バリデーション・ログなどの構成要素を踏まえて判断する。
単一ファイルで十分な場合も、その判断を明記する。

- 構成方針:
  - `複数モジュールに分割する`
- 概算メモ:
  - 例外型、`BatchRunSummary`、`FailedFileSummary`、依存 Protocol 定義だけで 100 行前後を使う。
  - `run_once(...)` の分岐は、差分なし短絡、削除処理、新規処理、更新処理、ファイル失敗集約、構造化ログ出力を含むため 200 行を超えやすい。
- モジュール一覧:
  - `backend/ingestion/infrastructure/batch_scheduler_types.py`
    - 責務:
      実行結果データ構造、例外型、依存 Protocol 定義を集約する。
    - 含める要素:
      `BatchRunSummary`、`FailedFileSummary`、`BatchSchedulerConfigError`、依存 Protocol（`DiffDetector`、`MarkdownLoader`、`Splitter`、`Tagger`、`Embedder`、`ChunkStoreWriter`）
  - `backend/ingestion/infrastructure/batch_executor.py`
    - 責務:
      `run_once(...)` の純粋な実行順序と、ファイル単位の成功・失敗集約ルールを実装する。
    - 含める要素:
      A1〜A5 呼び出し順、差分なし判定、更新ファイルの delete-before-upsert 制御、`structlog` 呼び出し

# 技術判断

品質に直結する技術選定や実装方針がある場合は、その判断と理由を書く。

- 判断:
  - 更新ファイルは A4 完了後に旧チャンク削除を行う。
  - 理由:
    読み込み・分割・タグ付与・Embedding で失敗しただけで既存チャンクを失う事態を避け、データ欠損の窓を最小化するため。
- 判断:
  - `run_once(...)` は運用上の失敗を例外送出ではなく `BatchRunSummary.status` に集約する。
  - 理由:
    バックグラウンドスケジューラは継続運転が前提であり、呼び出し元が毎回 try/except で回復させるより、結果集約と構造化ログで監視できる方が扱いやすいため。

# スコープ外

この機能では扱わないこと、別 issue / 別機能で扱うことを明示する。

- 対応しないこと:
  - 複数プロセス・複数ホスト間での分散ロック
  - 失敗ファイルの同一バッチ内リトライ
  - ファイル単位の並列取り込み
  - A6 以降のロードマップマッピングやフィードバック生成
  - バッチ途中の強制キャンセルとロールバック

# 受け入れ基準

検証可能な条件をチェックリスト形式で書く。実装手段ではなく、満たされるべき事実を書く。

- [ ] 差分件数がすべて 0 のとき、A2〜A5 が呼ばれず `skipped_no_diff` になる
- [ ] `deleted_files` はファイル単位で削除され、1 件失敗しても残りの削除対象と取り込み対象が継続される
- [ ] `new_files` は `load -> split -> tag -> embed -> upsert` の順で処理される
- [ ] `updated_files` は `load -> split -> tag -> embed -> delete_by_source_path -> upsert` の順で処理される
- [ ] 単一ファイルの失敗は `failed_files` に記録され、他ファイルの処理は継続する
- [ ] ファイル単位へ分解できない失敗は `status="failed"` として返り、例外として外へ漏れない
- [ ] 空チャンク結果の更新ファイルは既存チャンク削除後に成功扱いとなる
- [ ] `structlog` のイベント名と主要キーで、バッチ単位・ファイル単位の実行結果を機械集計できる

# テスト観点メモ

各主要ルールに対して最低1つ、各境界条件に対して最低1つの観点を列挙する。
受け入れ基準の各項目が少なくとも1つの観点でカバーされていることを確認する。

- 正常系:
  - `deleted_files=1, new_files=1, updated_files=1` の複合差分で、削除→新規→更新の順に処理されること
  - 新規ファイルが複数あるとき、辞書順昇順で `load -> split -> tag -> embed -> upsert` が行われること
  - 更新ファイルで A4 後に `delete_by_source_path`、その後 `upsert` が呼ばれること
  - 空チャンク結果の新規ファイルが保存なしで成功扱いになること
- 境界系:
  - 差分ゼロで `skipped_no_diff` になり、A2〜A5 が 1 回も呼ばれないこと
  - 更新ファイルで split 結果が空のとき、`delete_by_source_path` のみ呼ばれて成功扱いになること
- 異常系:
  - A1 `diff_detector.detect(...)` 失敗時に `status="failed"` が返り、A2〜A5 が未実行であること
  - 削除対象ファイルの `delete_by_source_path` 失敗時に、その 1 件だけが `failed_files` に入り残り処理が継続すること
  - 新規ファイルの `markdown_loader.load(...)` 失敗時に、次のファイルへ継続すること
  - 更新ファイルの `embed(...)` 失敗時に、`delete_by_source_path` と `upsert` が呼ばれないこと
  - 更新ファイルの `upsert(...)` 失敗時に、`failed_files.step="upsert"` が記録され `completed_with_errors` になること
