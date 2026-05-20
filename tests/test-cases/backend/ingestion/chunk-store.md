---
status: ready
---

# テストケース一覧

# 検証焦点

| テストの種類 | 検証焦点 |
|---|---|
| Phase 1（最小骨格） | `stored_ids` / `StoredChunk` / `deleted_count` の基本返却形、自然キー、成功ログ |
| Phase 2（コアロジック） | 空バッチ短絡、重複拒否、`source_path` 完全一致、優先順位付き fail-fast |
| Phase 3（エッジケース） | 入力契約違反、空 `source_path`、取得レコード不整合 |
| Phase 4（外部連携） | `ChunkCollection` 障害のラップ、cause chain、失敗ログ |

## Phase 1: 最小骨格

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-01 | 正常な 2 チャンクを 1 回で保存し、自然キー ID・metadata・成功ログを返す | `ChunkCollection` Protocol を満たすテストダブルを注入し、`upsert(ids, documents, embeddings, metadatas)` 呼び出し内容と `structlog` 出力を検査できる | `upsert_chunks(...)` に `source_path = "study/typescript/generics.md"`、`chunks = [{chunk_index: 0, text: "TypeScriptのジェネリクスは型引数で再利用性を高める。", embedding: [0.12, -0.03, 0.44, 0.08], headers: "TypeScript入門 > ジェネリクス", tags: ["TypeScript"], created_at: "2026-05-17T10:00:00+09:00", updated_at: "2026-05-17T10:00:00+09:00"}, {chunk_index: 1, text: "extends で型制約を付与できる。", embedding: [0.09, 0.11, -0.05, 0.27], headers: "TypeScript入門 > ジェネリクス", tags: ["TypeScript"], created_at: "2026-05-17T10:00:00+09:00", updated_at: "2026-05-17T10:00:00+09:00"}]` を渡す | 戻り値は `{source_path: "study/typescript/generics.md", stored_count: 2, stored_ids: ["study/typescript/generics.md_0", "study/typescript/generics.md_1"]}` と完全一致する。backend `upsert(...)` はちょうど 1 回だけ呼ばれ、`ids` は上記 2 件、`documents` は入力本文順、`embeddings` は入力ベクトル順、`metadatas` は各要素が `source_path` / `chunk_index` / `headers` / `tags` / `created_at` / `updated_at` を入力値そのままで含む。`event = "chunk_store_upsert_completed"` のログがちょうど 1 件出力され、少なくとも `source_path = "study/typescript/generics.md"`、`chunk_count = 2`、`stored_count = 2`、`vector_dimension = 4` を含む（追加キーがあってもよい） | 仕様書 例1、Protocol 注入の最小正常系 |
| TC-02 | 取得結果を `chunk_index` 昇順へ正規化し、完全な `StoredChunk` 一覧と成功ログを返す | backend `get(where={"source_path": "study/typescript/generics.md"})` が `chunk_index=1` のレコードを先、`chunk_index=0` のレコードを後で返す。ログ収集を有効化する | `get_by_source_path("study/typescript/generics.md")` | 戻り値は 2 件の `StoredChunk` 配列で、1 件目が `id = "study/typescript/generics.md_0"`、2 件目が `id = "study/typescript/generics.md_1"` となり、各 `text` / `embedding` / `metadata.source_path` / `metadata.chunk_index` / `metadata.headers` / `metadata.tags` / `metadata.created_at` / `metadata.updated_at` は仕様書 例2 と完全一致する。backend `get(...)` は `where = {"source_path": "study/typescript/generics.md"}` でちょうど 1 回呼ばれる。`event = "chunk_store_get_completed"` のログがちょうど 1 件出力され、少なくとも `source_path = "study/typescript/generics.md"`、`returned_count = 2` を含む（`vector_dimension` を含む場合は `4`、追加キーは許容する） | 仕様書 例2 |
| TC-03 | 同一 `source_path` の既存 2 件を全削除し、削除件数と成功ログを返す | 事前状態として `study/typescript/generics.md_0` と `study/typescript/generics.md_1` が保存済みで、backend 呼び出し内容とログを検査できる | `delete_by_source_path("study/typescript/generics.md")` | 戻り値は `{source_path: "study/typescript/generics.md", deleted_count: 2}` と完全一致する。削除条件は `where = {"source_path": "study/typescript/generics.md"}` の完全一致で扱われる。`event = "chunk_store_delete_completed"` のログがちょうど 1 件出力され、少なくとも `source_path = "study/typescript/generics.md"`、`deleted_count = 2` を含む（追加キーがあってもよい） | 仕様書 例3 |

## Phase 2: コアロジック

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-10 | 空バッチ保存は短絡成功し、backend を呼ばず、空バッチ成功ログを出す | backend `upsert` 呼び出し有無を検査でき、ログ収集を有効化する | `upsert_chunks({source_path: "study/empty.md", chunks: []})` | 戻り値は `{source_path: "study/empty.md", stored_count: 0, stored_ids: []}` と完全一致する。backend `upsert(...)` は 1 回も呼ばれない。`event = "chunk_store_upsert_completed"` のログがちょうど 1 件出力され、少なくとも `source_path = "study/empty.md"`、`chunk_count = 0`、`stored_count = 0`、`vector_dimension = null` を含む（追加キーがあってもよい） | 空バッチ境界 |
| TC-11 | 同一 `upsert_chunks(...)` 内の重複 `chunk_index` は backend 呼び出し前に拒否する | backend `upsert` 呼び出し有無を検査できる | `upsert_chunks(...)` に `source_path = "study/invalid.md"`、`chunks = [{chunk_index: 0, text: "本文A", embedding: [0.1, 0.2], headers: "", tags: [], created_at: "2026-05-17T10:00:00+09:00", updated_at: "2026-05-17T10:00:00+09:00"}, {chunk_index: 0, text: "本文B", embedding: [0.3, 0.4], headers: "", tags: [], created_at: "2026-05-17T10:00:00+09:00", updated_at: "2026-05-17T10:00:00+09:00"}]` を渡す | `ChunkStoreDuplicateChunkIndexError` を送出する。backend `upsert(...)` は 1 回も呼ばれない。部分保存は行われない | 仕様書 例4 |
| TC-12 | 取得は `source_path` 完全一致で行い、近接パス `.bak` を混同せず、該当なしは空リストを返す | backend には `id = "study/typescript/generics.md.bak_0"`、`metadata.source_path = "study/typescript/generics.md.bak"` のみが存在し、backend `get` の受け取り `where` を検査できる。ログ収集を有効化する | `get_by_source_path("study/typescript/generics.md")` | 戻り値は `[]` と完全一致する。backend `get(...)` は `where = {"source_path": "study/typescript/generics.md"}` でちょうど 1 回呼ばれ、prefix 条件や部分一致条件は使われない。`event = "chunk_store_get_completed"` のログがちょうど 1 件出力され、少なくとも `source_path = "study/typescript/generics.md"`、`returned_count = 0` を含む（追加キーがあってもよい） | `.md` と `.md.bak` の非混同、該当なし取得 |
| TC-13 | 削除は `source_path` 完全一致で行い、近接パス `.bak` を削除せず、該当なしは `deleted_count=0` を返す | backend には `study/typescript/generics.md.bak` 由来のレコードのみが存在し、backend 呼び出し `where` と削除有無を検査できる。ログ収集を有効化する | `delete_by_source_path("study/typescript/generics.md")` | 戻り値は `{source_path: "study/typescript/generics.md", deleted_count: 0}` と完全一致する。backend への削除条件は `where = {"source_path": "study/typescript/generics.md"}` の完全一致であり、`.bak` 側は削除対象に含まれない。`event = "chunk_store_delete_completed"` のログがちょうど 1 件出力され、少なくとも `source_path = "study/typescript/generics.md"`、`deleted_count = 0` を含む（追加キーがあってもよい） | `.md` と `.md.bak` の非混同、0 件削除 |
| TC-14 | `upsert_chunks(...)` は全件バリデーションを重複判定より先に行い、不正入力があれば `Duplicate` ではなく `InputError` を優先する | backend `upsert` 呼び出し有無を検査できる | `upsert_chunks(...)` に `source_path = "study/invalid.md"`、`chunks = [{chunk_index: 0, text: "   ", embedding: [0.1, 0.2], headers: "", tags: [], created_at: "2026-05-17T10:00:00+09:00", updated_at: "2026-05-17T10:00:00+09:00"}, {chunk_index: 0, text: "本文B", embedding: [0.3, 0.4], headers: "", tags: [], created_at: "2026-05-17T10:00:00+09:00", updated_at: "2026-05-17T10:00:00+09:00"}]` を渡す | `ChunkStoreInputError` を送出し、`ChunkStoreDuplicateChunkIndexError` は送出しない。backend `upsert(...)` は 1 回も呼ばれない | ルール間相互作用の優先順位 |

## Phase 3: エッジケース

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-20 | 保存入力の契約違反を網羅的に `ChunkStoreInputError` として拒否する | backend `upsert` 呼び出し有無を検査できる | ケースA: `source_path = ""`。ケースB: `chunk_index = -1`。ケースC: `text = "   "`。ケースD: `embedding = []`。ケースE: `embedding = [0.1, "0.2"]`。ケースF: `embedding = [0.1, NaN]`。ケースG: `embedding = [0.1, inf]`。ケースH: `tags = ["ok", 1]`。ケースI: `headers = 123`。ケースJ: `created_at = 123`。ケースK: `updated_at = null`。ケースL: 2 件入力で `embedding` 次元が `[0.1, 0.2]` と `[0.3, 0.4, 0.5]` の不一致 | 各ケースで `ChunkStoreInputError` を送出する。backend `upsert(...)` は各ケースで 1 回も呼ばれない | 仕様書記載の入力異常と次元不一致を集約 |
| TC-21 | `delete_by_source_path(...)` と `get_by_source_path(...)` は空 `source_path` を拒否する | backend `get` / `delete` 呼び出し有無を検査できる | ケースA: `delete_by_source_path("")`。ケースB: `get_by_source_path("")` | 各ケースで `ChunkStoreInputError` を送出する。backend `delete(...)` / `get(...)` は各ケースで 1 回も呼ばれない | `source_path` 入力契約 |
| TC-22 | 取得レコードの `id` と `metadata.source_path` / `chunk_index` が不整合なら結果全体を失敗させる | backend `get(where={"source_path": "study/a.md"})` が少なくとも 1 件、`id = "study/b.md_0"`、`metadata.source_path = "study/a.md"`、`metadata.chunk_index = 0` のレコードを返す | `get_by_source_path("study/a.md")` | `ChunkStoreRecordFormatError` を送出し、`StoredChunk` 配列は返さない | 仕様書の代表的不整合ケース |
| TC-23 | 取得レコードの必須項目欠落・`chunk_index` 不正・本文/ベクトル形式不正を `ChunkStoreRecordFormatError` として拒否する | backend `get(...)` が 1 件の不正レコードを返すようにできる | ケースA: `metadata` から `created_at` が欠落。ケースB: `metadata.chunk_index = -1` または非整数。ケースC: `text` が文字列でない、または欠落。ケースD: `embedding` が空配列。ケースE: `embedding` が `list` でない。ケースF: `embedding` に `NaN` / `inf` / 非数値を含む | 各ケースで `ChunkStoreRecordFormatError` を送出し、`StoredChunk` 配列は返さない | 取得結果の正規化と検証 |

## Phase 4: 外部連携

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-30 | backend `upsert` 例外は原因付きで `ChunkStoreBackendError` にラップし、失敗ログを出す | backend `upsert(...)` が `TimeoutError("upsert timed out")` を送出し、ログ収集を有効化する | 正常形式の 1 チャンクで `upsert_chunks(...)` を呼ぶ。`source_path = "study/backend/infra.md"` | `ChunkStoreBackendError` を送出し、`__cause__` が元の `TimeoutError("upsert timed out")` と同一である。`event = "chunk_store_upsert_failed"` のログがちょうど 1 件出力され、少なくとも `source_path = "study/backend/infra.md"`、`chunk_count = 1`、`error_type` キーの存在を確認できる（追加キーがあってもよい）。例外情報はスタックトレース付きで記録される | backend 障害の保存側ラップ |
| TC-31 | backend `get` 例外は原因付きで `ChunkStoreBackendError` にラップし、失敗ログを出す | backend `get(...)` が `ConnectionError("collection unavailable")` を送出し、ログ収集を有効化する | `get_by_source_path("study/backend/infra.md")` | `ChunkStoreBackendError` を送出し、`__cause__` が元の `ConnectionError("collection unavailable")` と同一である。`event = "chunk_store_get_failed"` のログがちょうど 1 件出力され、少なくとも `source_path = "study/backend/infra.md"`、`error_type` キーの存在を確認できる（追加キーがあってもよい）。例外情報はスタックトレース付きで記録される | backend 障害の取得側ラップ |
| TC-32 | backend `delete` 例外は原因付きで `ChunkStoreBackendError` にラップし、失敗ログを出す | backend `delete(...)` が `RuntimeError("delete failed")` を送出し、ログ収集を有効化する | `delete_by_source_path("study/backend/infra.md")` | `ChunkStoreBackendError` を送出し、`__cause__` が元の `RuntimeError("delete failed")` と同一である。`event = "chunk_store_delete_failed"` のログがちょうど 1 件出力され、少なくとも `source_path = "study/backend/infra.md"`、`error_type` キーの存在を確認できる（追加キーがあってもよい）。例外情報はスタックトレース付きで記録される | backend 障害の削除側ラップ |

# 網羅性チェック

仕様書の受け入れ基準の各項目に対応するテストケース ID を記載する。
全項目が少なくとも1つのテストケースでカバーされていることを確認する。

| 受け入れ基準 | 対応テストケース |
|---|---|
| `ChunkStore` 実装は ChromaDB concrete client ではなく `ChunkCollection` Protocol を DI で受け取る | TC-01 |
| `upsert_chunks(...)` で各チャンクの ID が `{source_path}_{chunk_index}` 形式で生成される | TC-01 |
| `upsert_chunks(...)` で正常なチャンク群を渡すと、入力順に対応する `stored_ids` と `stored_count` が返る | TC-01 |
| `upsert_chunks(...)` に空バッチを渡した場合、backend 呼び出しなしで成功する | TC-10 |
| 1 回の保存要求に重複 `chunk_index` が含まれる場合、`ChunkStoreDuplicateChunkIndexError` が送出される | TC-11 |
| 入力チャンクに空本文、非有限値ベクトル、型不正タグなどがある場合、`ChunkStoreInputError` が送出される | TC-14, TC-20, TC-21 |
| `delete_by_source_path(...)` は同一 `source_path` のチャンクを全件削除し、存在しない場合は `deleted_count=0` を返す | TC-03, TC-13 |
| `get_by_source_path(...)` は同一 `source_path` のチャンクだけを `chunk_index` 昇順で返す | TC-02, TC-12 |
| backend 呼び出しが失敗した場合、各操作で `ChunkStoreBackendError` が送出される | TC-30, TC-31, TC-32 |
| backend から不整合レコードが返った場合、`ChunkStoreRecordFormatError` が送出される | TC-22, TC-23 |
| 保存・取得・削除の成功時と backend 障害時に、規定イベント名で `structlog` の構造化ログが出力される | TC-01, TC-02, TC-03, TC-10, TC-12, TC-13, TC-30, TC-31, TC-32 |

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
