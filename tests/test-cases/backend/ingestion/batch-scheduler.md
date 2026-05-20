---
status: ready
---

# テストケース一覧

# 検証焦点

| テストの種類 | 検証焦点 |
|---|---|
| Phase 1（最小骨格） | `BatchRunSummary` 全フィールド、A2〜A5 非実行条件 |
| Phase 2（コアロジック） | 削除→新規→更新の順序、辞書順、成功カウント、ファイル単位継続 |
| Phase 3（エッジケース） | 構成エラー、更新ファイルの競合失敗 |
| Phase 4（外部連携） | 非分解失敗の `status="failed"`、例外送出契約、`structlog` イベント契約 |

## Phase 1: 最小骨格

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-01 | 差分ゼロ時は `skipped_no_diff` を返し、A2〜A5 を呼ばずに終了する | `target_path="/vault/study"`、`interval_seconds=300`、依存の呼び出し回数を検査できる | `run_once(trigger="startup")`。`diff_detector.detect("/vault/study")` は `{new_files: [], updated_files: [], deleted_files: [], new_count: 0, updated_count: 0, deleted_count: 0}` を返す | 戻り値は `{status: "skipped_no_diff", trigger: "startup", new_count: 0, updated_count: 0, deleted_count: 0, deleted_success_count: 0, ingest_target_count: 0, ingested_success_count: 0, failed_file_count: 0, failed_files: [], stored_chunk_count: 0}` と完全一致する。`markdown_loader.load`、`chunk_splitter.split`、`chunk_tagger.tag`、`embedder.embed`、`chunk_store.delete_by_source_path`、`chunk_store.upsert_chunks` はいずれもちょうど 0 回である | 仕様書 例1、受け入れ基準「差分件数がすべて 0」 |
| TC-02 | 削除成功 1 件・新規成功 1 件・更新失敗 1 件の複合差分を `completed_with_errors` として集約する | `target_path="/vault/study"`。`docker/compose.md` の A2〜A5 は成功し 2 チャンク保存される。`typescript/generics.md` は A4 で `EmbeddingModelCallError` を送出する | `run_once(trigger="interval")`。`diff_detector.detect("/vault/study")` は `{new_files: ["docker/compose.md"], updated_files: ["typescript/generics.md"], deleted_files: ["python/contextmanager.md"], new_count: 1, updated_count: 1, deleted_count: 1}` を返す。`chunk_store.delete_by_source_path("python/contextmanager.md")` は成功する | 戻り値は `{status: "completed_with_errors", trigger: "interval", new_count: 1, updated_count: 1, deleted_count: 1, deleted_success_count: 1, ingest_target_count: 2, ingested_success_count: 1, failed_file_count: 1, failed_files: [{source_path: "typescript/generics.md", action: "ingest_updated", step: "embed", error_type: "EmbeddingModelCallError"}], stored_chunk_count: 2}` と完全一致する。`typescript/generics.md` については旧チャンク削除と A5 upsert がいずれもちょうど 0 回である | 仕様書 例2 |

## Phase 2: コアロジック

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-10 | 差分あり時は `deleted_files` → `new_files` → `updated_files` の順で、各一覧内は辞書順昇順で処理される | すべての対象ファイルで処理が成功し、各依存呼び出しの順序を検査できる | `run_once(trigger="interval")`。A1 は `{deleted_files: ["zeta/old.md", "alpha/old.md"], new_files: ["notes/z.md", "notes/a.md"], updated_files: ["topics/d.md", "topics/c.md"], new_count: 2, updated_count: 2, deleted_count: 2}` を返す | `chunk_store.delete_by_source_path` は `"alpha/old.md"`、`"zeta/old.md"` の順でちょうど各 1 回呼ばれる。その後に新規 `"notes/a.md"`、`"notes/z.md"` が処理され、その後に更新 `"topics/c.md"`、`"topics/d.md"` が処理される。戻り値は `status="completed"`、`deleted_success_count=2`、`ingest_target_count=4`、`ingested_success_count=4`、`failed_file_count=0` を含み、`failed_files=[]` である | 受け入れ基準「削除→新規→更新の順」 |
| TC-11 | 新規ファイルは `load -> split -> tag -> embed -> upsert` の順で処理される | `notes/a.md` と `notes/b.md` の処理が成功し、依存呼び出し順序を検査できる | `run_once(trigger="interval")`。A1 は `{new_files: ["notes/b.md", "notes/a.md"], updated_files: [], deleted_files: [], new_count: 2, updated_count: 0, deleted_count: 0}` を返す。各ファイルの分割結果は 1 チャンク以上である | 新規ファイルの実行順は `"notes/a.md"`、`"notes/b.md"` の辞書順である。各ファイルごとに `markdown_loader.load` → `chunk_splitter.split` → `chunk_tagger.tag` → `embedder.embed` → `chunk_store.upsert_chunks` の順でちょうど 1 回ずつ呼ばれる。`chunk_store.delete_by_source_path` は新規ファイルに対してちょうど 0 回である | 受け入れ基準「new_files の処理順」 |
| TC-12 | 更新ファイルは A4 成功後にのみ旧チャンク削除へ進み、その後に upsert する | `topics/refactor.md` の処理が成功し、依存呼び出し順序を検査できる | `run_once(trigger="interval")`。A1 は `{new_files: [], updated_files: ["topics/refactor.md"], deleted_files: [], new_count: 0, updated_count: 1, deleted_count: 0}` を返す。分割結果は 2 チャンクで、A2〜A5 は成功する | `topics/refactor.md` では `markdown_loader.load` → `chunk_splitter.split` → `chunk_tagger.tag` → `embedder.embed` → `chunk_store.delete_by_source_path("topics/refactor.md")` → `chunk_store.upsert_chunks(...)` の順でちょうど 1 回ずつ呼ばれる。`delete_by_source_path` は `embedder.embed` 成功前には呼ばれない。戻り値は `status="completed"`、`ingested_success_count=1`、`stored_chunk_count=2` を含む | 受け入れ基準「updated_files の処理順」 |
| TC-13 | 新規ファイルの split 結果が空なら保存なしで成功扱いになる | `notes/empty-new.md` の読み込みと split を検査できる | `run_once(trigger="interval")`。A1 は `{new_files: ["notes/empty-new.md"], updated_files: [], deleted_files: [], new_count: 1, updated_count: 0, deleted_count: 0}` を返す。`markdown_loader.load(...)` は `"---\ntitle: only meta\n---\n"` を返し、`chunk_splitter.split(...)` は `[]` を返す | `chunk_tagger.tag`、`embedder.embed`、`chunk_store.upsert_chunks`、`chunk_store.delete_by_source_path` は `notes/empty-new.md` に対してちょうど 0 回である。戻り値は `status="completed"`、`ingest_target_count=1`、`ingested_success_count=1`、`stored_chunk_count=0`、`failed_file_count=0` を含む | 境界条件「新規ファイルの分割結果が空」 |
| TC-14 | 更新ファイルの split 結果が空なら旧チャンク削除後に成功扱いになる | `notes/empty.md` の読み込みと split を検査できる | `run_once(trigger="interval")`。A1 は `{new_files: [], updated_files: ["notes/empty.md"], deleted_files: [], new_count: 0, updated_count: 1, deleted_count: 0}` を返す。`markdown_loader.load(...)` は `"---\ntitle: only meta\n---\n"` を返し、`chunk_splitter.split(...)` は `[]` を返す。`chunk_store.delete_by_source_path("notes/empty.md")` は成功する | `chunk_store.delete_by_source_path("notes/empty.md")` がちょうど 1 回呼ばれる。`chunk_tagger.tag`、`embedder.embed`、`chunk_store.upsert_chunks` はちょうど 0 回である。戻り値は `status="completed"`、`ingest_target_count=1`、`ingested_success_count=1`、`stored_chunk_count=0`、`failed_file_count=0` を含む | 仕様書 例4、受け入れ基準「空チャンク結果の更新ファイル」 |
| TC-15 | 単一ファイル失敗は `failed_files` に集約され、他ファイル処理は継続する | 各依存の成功・失敗をファイル単位で制御できる | `run_once(trigger="interval")`。A1 は `{deleted_files: ["removed/bad.md"], new_files: ["new/bad.md", "new/good.md"], updated_files: ["updated/good.md"], new_count: 2, updated_count: 1, deleted_count: 1}` を返す。`chunk_store.delete_by_source_path("removed/bad.md")` は `ChunkStoreWriteError` 失敗、`markdown_loader.load("new/bad.md")` は `FileNotFoundError` 失敗、`new/good.md` は 1 チャンク保存成功、`updated/good.md` は 2 チャンク保存成功 | 戻り値は `status="completed_with_errors"` を返す。`failed_file_count=2` であり、`failed_files` には `{source_path: "removed/bad.md", action: "delete", step: "delete_removed_file", error_type: "ChunkStoreWriteError"}` と `{source_path: "new/bad.md", action: "ingest_new", step: "load", error_type: "FileNotFoundError"}` が含まれる。`new/good.md` と `updated/good.md` は処理継続され、`ingested_success_count=2`、`deleted_success_count=0`、`stored_chunk_count=3` である。失敗した 2 ファイルは同一バッチ内で再試行されない | 受け入れ基準「1 ファイル失敗時の継続」 |
| TC-15b | split 失敗時に `step="split"` が記録され他ファイルは継続する | split 失敗をファイル単位で制御できる | `run_once(trigger="interval")`。A1 は `{new_files: ["bad/split.md", "good/file.md"], updated_files: [], deleted_files: [], new_count: 2, updated_count: 0, deleted_count: 0}` を返す。`chunk_splitter.split` は `bad/split.md` に対して `RuntimeError` を送出し、`good/file.md` は成功する | `failed_files` に `{source_path: "bad/split.md", action: "ingest_new", step: "split", error_type: "RuntimeError"}` がちょうど 1 件含まれる。`good/file.md` は処理継続される | TC-15 の split 分岐補完 |
| TC-15c | tag 失敗時に `step="tag"` が記録され他ファイルは継続する | tag 失敗をファイル単位で制御できる | `run_once(trigger="interval")`。A1 は `{new_files: ["bad/tag.md", "good/file.md"], updated_files: [], deleted_files: [], new_count: 2, updated_count: 0, deleted_count: 0}` を返す。`chunk_tagger.tag` は `bad/tag.md` に対して `RuntimeError` を送出し、`good/file.md` は成功する | `failed_files` に `{source_path: "bad/tag.md", action: "ingest_new", step: "tag", error_type: "RuntimeError"}` がちょうど 1 件含まれる。`good/file.md` は処理継続される | TC-15 の tag 分岐補完 |

## Phase 3: エッジケース

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-20 | 構成不正は `BatchSchedulerConfigError` を送出し、バッチを開始しない | 依存呼び出し回数を検査できる | `target_path=""` で `run_once(trigger="startup")` を呼ぶ | `BatchSchedulerConfigError` を送出する。例外型のみを検証対象とし、message・cause chain・ログ有無は検証対象外とする。`diff_detector.detect` を含む A1〜A5 はちょうど 0 回である | 境界条件「target_path が空」 |
| TC-23 | `updated_files` に入っていた実ファイルが A2 前に消えた場合、`step="load"` 失敗として記録し継続する | 他ファイルの継続可否を検査できる | `run_once(trigger="interval")`。A1 は `{new_files: ["new/good.md"], updated_files: ["notes/moved.md"], deleted_files: [], new_count: 1, updated_count: 1, deleted_count: 0}` を返す。`markdown_loader.load("notes/moved.md")` は `FileNotFoundError` を送出し、`new/good.md` は成功する | 戻り値は `status="completed_with_errors"` を返す。`failed_files` には `{source_path: "notes/moved.md", action: "ingest_updated", step: "load", error_type: "FileNotFoundError"}` がちょうど 1 件含まれる。`notes/moved.md` に対して `chunk_splitter.split` 以降はちょうど 0 回であり、`new/good.md` は処理継続される | 境界条件「A1 検出後に実ファイルが削除・移動」 |
| TC-24 | 更新ファイルで旧チャンク削除に失敗した場合は `step="delete_old_chunks"` を記録し、upsert しない | `topics/topic.md` の A1〜A4 成功後に A5 削除だけ失敗させられる | `run_once(trigger="interval")`。A1 は `{new_files: [], updated_files: ["topics/topic.md"], deleted_files: [], new_count: 0, updated_count: 1, deleted_count: 0}` を返す。`markdown_loader.load`、`chunk_splitter.split`、`chunk_tagger.tag`、`embedder.embed` は成功し、`chunk_store.delete_by_source_path("topics/topic.md")` は `ChunkStoreWriteError` を送出する | 戻り値は `status="completed_with_errors"` を返す。`failed_files` には `{source_path: "topics/topic.md", action: "ingest_updated", step: "delete_old_chunks", error_type: "ChunkStoreWriteError"}` がちょうど 1 件含まれる。`topics/topic.md` に対する A5 upsert はちょうど 0 回である | 境界条件「delete_by_source_path(source_path) が失敗する」 |
| TC-25 | 更新ファイルで旧チャンク削除成功後の upsert 失敗は `step="upsert"` として記録し、ロールバックしない | `topics/topic.md` の A1〜A4 と旧チャンク削除は成功し、A5 upsert だけ失敗する | `run_once(trigger="interval")`。A1 は `{new_files: [], updated_files: ["topics/topic.md"], deleted_files: [], new_count: 0, updated_count: 1, deleted_count: 0}` を返す。`chunk_store.delete_by_source_path("topics/topic.md")` は成功し、`chunk_store.upsert_chunks(...)` は `ChunkStoreWriteError` を送出する | 戻り値は `status="completed_with_errors"` を返す。`failed_files` には `{source_path: "topics/topic.md", action: "ingest_updated", step: "upsert", error_type: "ChunkStoreWriteError"}` がちょうど 1 件含まれる。`stored_chunk_count` はこの失敗ファイル分を加算しない。失敗後に同一バッチ内のロールバックや再試行は行わない | 境界条件「delete 成功後に upsert が失敗する」 |

## Phase 4: 外部連携

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-30 | A1 自体の失敗は例外送出せず `status="failed"` として返す | A1 以外の依存呼び出し回数を検査できる | `run_once(trigger="interval")`。`diff_detector.detect("/vault/study")` が `RuntimeError("scan failed")` を送出する | 呼び出し元には例外を送出しない。戻り値は `{status: "failed", trigger: "interval", new_count: 0, updated_count: 0, deleted_count: 0, deleted_success_count: 0, ingest_target_count: 0, ingested_success_count: 0, failed_file_count: 0, failed_files: [], stored_chunk_count: 0}` と完全一致する。`markdown_loader.load`、`chunk_splitter.split`、`chunk_tagger.tag`、`embedder.embed`、`chunk_store.delete_by_source_path`、`chunk_store.upsert_chunks` はいずれも 0 回である | 受け入れ基準「ファイル単位へ分解できない失敗」 |
| TC-30b | A1 以外のオーケストレーション部分で予期しない例外が発生しても `status="failed"` として返す | オーケストレーション内部（summary 構築等）で例外を発生させられる | `run_once(trigger="interval")`。A1 は正常に差分を返すが、後続のオーケストレーション処理で `RuntimeError` が発生する | 呼び出し元には例外を送出しない。戻り値は `status="failed"` を含む | 受け入れ基準「ファイル単位へ分解できない失敗」の catch-all 経路 |
| TC-32 | 成功・失敗・完了の `structlog` イベント名と必須キーが固定である | `structlog` の出力イベント名・キー・件数を検査できる。混合差分で 1 削除成功、1 新規成功、1 更新成功、1 更新失敗を発生させる | `run_once(trigger="interval")`。A1 は `{new_files: ["docker/compose.md"], updated_files: ["react/hooks.md", "typescript/generics.md"], deleted_files: ["python/contextmanager.md"], new_count: 1, updated_count: 2, deleted_count: 1}` を返す。削除成功、新規成功 2 チャンク保存、更新 `react/hooks.md` 成功 3 チャンク保存、更新 `typescript/generics.md` は `EmbeddingModelCallError` 失敗とする | `event="ingestion_batch_started"` がちょうど 1 件あり、少なくとも `trigger="interval"`、`target_path="/vault/study"` を含む。`event="ingestion_batch_file_completed"` がちょうど 3 件あり、`("python/contextmanager.md","delete",0)` と `("docker/compose.md","ingest_new",2)` と `("react/hooks.md","ingest_updated",3)` の `source_path` / `action` / `stored_chunk_count` 組を含む。`event="ingestion_batch_file_failed"` がちょうど 1 件あり、少なくとも `source_path="typescript/generics.md"`、`action="ingest_updated"`、`step="embed"`、`error_type="EmbeddingModelCallError"` を含む。`event="ingestion_batch_completed"` がちょうど 1 件あり、少なくとも `status="completed_with_errors"`、`trigger="interval"`、`new_count=1`、`updated_count=2`、`deleted_count=1`、`deleted_success_count=1`、`ingested_success_count=2`、`failed_file_count=1`、`stored_chunk_count=5` を含む。追加キーは許容する | 受け入れ基準「structlog のイベント名と主要キー」 |
| TC-33 | 差分なしスキップの `structlog` イベント名と必須キーが固定である | `structlog` の出力イベント名・キー・件数を検査できる | 差分ゼロの `run_once(trigger="startup")` を実行する | `event="ingestion_batch_skipped_no_diff"` がちょうど 1 件あり、少なくとも `trigger="startup"`、`target_path="/vault/study"`、`new_count=0`、`updated_count=0`、`deleted_count=0` を含む。追加キーは許容する | 受け入れ基準「差分なしスキップ」の可観測性 |

# 網羅性チェック

仕様書の受け入れ基準の各項目に対応するテストケース ID を記載する。
全項目が少なくとも1つのテストケースでカバーされていることを確認する。

| 受け入れ基準 | 対応テストケース |
|---|---|
| 差分件数がすべて 0 のとき、A2〜A5 が呼ばれず `skipped_no_diff` になる | TC-01 |
| `deleted_files` はファイル単位で削除され、1 件失敗しても残りの削除対象と取り込み対象が継続される | TC-10, TC-15 |
| `new_files` は `load -> split -> tag -> embed -> upsert` の順で処理される | TC-11 |
| `updated_files` は `load -> split -> tag -> embed -> delete_by_source_path -> upsert` の順で処理される | TC-12 |
| 単一ファイルの失敗は `failed_files` に記録され、他ファイルの処理は継続する | TC-02, TC-15, TC-23, TC-24, TC-25 |
| ファイル単位へ分解できない失敗は `status="failed"` として返り、例外として外へ漏れない | TC-30, TC-30b |
| 空チャンク結果の更新ファイルは既存チャンク削除後に成功扱いとなる | TC-14 |
| `structlog` のイベント名と主要キーで、バッチ単位・ファイル単位の実行結果を機械集計できる | TC-32, TC-33 |

# 記述ルール

- 仕様書に明記された振る舞いだけを前提にする
- 仕様未記載の振る舞いを期待結果に置く場合は `[要仕様追記]` タグを付ける
- 正常系・境界系・異常系が重複なく網羅されていることを確認する
- 仕様書の受け入れ基準の各項目に対応するテストケースが最低1つあることを確認する
- 期待結果に「含まれる」「完全一致」「少なくとも1件」「ちょうど1件」などの検証粒度を明示する
- ログ検証を含む場合は、検証対象イベント名、必須キー、期待値、件数制約、追加キー許容の有無を明示する
- 例外検証を含む場合は、例外型、message、cause chain、ログ記録有無のうち何を確認するかを明示する
- テストが「存在確認」なのか「内容検証」なのかを期待結果で区別して書く
- テストケース文書に書いていない検証を impl レビューで追加要求しなくて済む粒度まで、期待結果を具体化する
