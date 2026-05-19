---
status: ready
---

# テストケース一覧

# 検証焦点

| テストの種類 | 検証焦点 |
|---|---|
| Phase 1（最小骨格） | `stored_ids` / `StoredChunk` / `deleted_count` の基本返却形 |
| Phase 2（コアロジック） | 自然キー生成、保存前検証順序、空バッチ短絡、完全一致条件、Protocol 注入 |
| Phase 3（エッジケース） | 入力契約違反、存在しない `source_path`、取得レコード破損 |
| Phase 4（外部連携） | backend 例外ラップ、構造化ログ、原因例外保持 |

## Phase 1: 最小骨格

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-01 | 正常な 2 チャンク保存で自然キー ID を入力順に返し、backend へ 1 回で保存する | `ChunkCollection` テストダブルは `upsert(ids, documents, embeddings, metadatas)` の呼び出し内容を検査できる | `upsert_chunks({source_path: "study/typescript/generics.md", chunks: [{chunk_index: 0, text: "TypeScriptのジェネリクスは型引数で再利用性を高める。", embedding: [0.12, -0.03, 0.44, 0.08], headers: "TypeScript入門 > ジェネリクス", tags: ["TypeScript"], created_at: "2026-05-17T10:00:00+09:00", updated_at: "2026-05-17T10:00:00+09:00"}, {chunk_index: 1, text: "extends で型制約を付与できる。", embedding: [0.09, 0.11, -0.05, 0.27], headers: "TypeScript入門 > ジェネリクス", tags: ["TypeScript"], created_at: "2026-05-17T10:00:00+09:00", updated_at: "2026-05-17T10:00:00+09:00"}]})` | 戻り値は `{source_path: "study/typescript/generics.md", stored_count: 2, stored_ids: ["study/typescript/generics.md_0", "study/typescript/generics.md_1"]}` と完全一致する。backend `upsert(...)` はちょうど 1 回呼ばれ、`ids`・`documents`・`embeddings`・`metadatas` は入力順を保持し、各 `metadata.source_path` は `"study/typescript/generics.md"` と完全一致する | 仕様書 例1 対応 |
| TC-02 | 取得結果を `chunk_index` 昇順へ正規化して `StoredChunk` 全項目を返す | backend `get(where={"source_path": "study/typescript/generics.md"})` は `chunk_index=1` のレコードを先に、`chunk_index=0` のレコードを後に返す | `get_by_source_path("study/typescript/generics.md")` | 戻り値は 2 件の `StoredChunk` 配列であり、1 件目が `id = "study/typescript/generics.md_0"`、2 件目が `id = "study/typescript/generics.md_1"` となる。各要素の `text`、`embedding`、`metadata.source_path`、`metadata.chunk_index`、`metadata.headers`、`metadata.tags`、`metadata.created_at`、`metadata.updated_at` は backend 生データを保持しつつ、返却順だけが `chunk_index` 昇順に正規化される | 仕様書 例2 対応 |
| TC-03 | 同一 `source_path` のみを一括削除し、`.bak` 側を巻き込まない | backend 側には `study/typescript/generics.md_0`、`study/typescript/generics.md_1`、`study/typescript/generics.md.bak_0` が存在し、テストダブルは `where` 条件を検査できる | `delete_by_source_path("study/typescript/generics.md")` | 戻り値は `{source_path: "study/typescript/generics.md", deleted_count: 2}` と完全一致する。backend `delete(...)` は `where={"source_path": "study/typescript/generics.md"}` でちょうど 1 回呼ばれ、`.bak` 側レコードは削除対象に含まれない | 仕様書 例3 と完全一致条件 |

## Phase 2: コアロジック

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-10 | 空バッチ保存は短絡成功し、backend `upsert` を呼ばず、成功ログを出す | `ChunkCollection` テストダブルは `upsert` 呼び出し有無を検査でき、構造化ログ収集を有効化する | `upsert_chunks({source_path: "study/empty.md", chunks: []})` | 戻り値は `{source_path: "study/empty.md", stored_count: 0, stored_ids: []}` と完全一致する。backend `upsert(...)` は 1 回も呼ばれない。`event = "chunk_store_upsert_completed"` のログがちょうど 1 件出力され、少なくとも `source_path = "study/empty.md"`、`chunk_count = 0`、`stored_count = 0` を含む（追加キーがあってもよい） | 境界条件の短絡成功 |
| TC-11 | 同一 `upsert` 内の重複 `chunk_index` は部分保存せず拒否する | `ChunkCollection` テストダブルは `upsert` 呼び出し有無を検査できる | `upsert_chunks({source_path: "study/invalid.md", chunks: [{chunk_index: 0, text: "本文A", embedding: [0.1, 0.2], headers: "", tags: [], created_at: "2026-05-17T10:00:00+09:00", updated_at: "2026-05-17T10:00:00+09:00"}, {chunk_index: 0, text: "本文B", embedding: [0.3, 0.4], headers: "", tags: [], created_at: "2026-05-17T10:00:00+09:00", updated_at: "2026-05-17T10:00:00+09:00"}]})` | `ChunkStoreDuplicateChunkIndexError` を送出する。backend `upsert(...)` は 1 回も呼ばれず、部分的な保存結果も返さない | 仕様書 例4 対応 |
| TC-12 | 入力不正と重複が同時にある場合は保存前バリデーションを優先し、重複判定より先に失敗する | `ChunkCollection` テストダブルは `upsert` 呼び出し有無を検査できる | `upsert_chunks({source_path: "study/invalid.md", chunks: [{chunk_index: 0, text: "本文A", embedding: [0.1, 0.2], headers: "", tags: [], created_at: "2026-05-17T10:00:00+09:00", updated_at: "2026-05-17T10:00:00+09:00"}, {chunk_index: 0, text: "   ", embedding: [0.3, 0.4], headers: "", tags: [], created_at: "2026-05-17T10:00:00+09:00", updated_at: "2026-05-17T10:00:00+09:00"}]})` | `ChunkStoreInputError` を送出し、`ChunkStoreDuplicateChunkIndexError` は送出しない。backend `upsert(...)` は 1 回も呼ばれない | ルール間相互作用の優先順位 |
| TC-13 | `ChunkCollection` Protocol を満たすテストダブルだけで機能が成立し、具体 client 型に依存しない | テストダブルは `upsert` / `get` / `delete` を実装するが ChromaDB concrete client を継承・import しない | 同一テストダブルを注入した `ChunkStore` に対して、`upsert_chunks(...)`、`get_by_source_path(...)`、`delete_by_source_path(...)` を順に実行する | 3 操作とも仕様通りの戻り値または副作用を返し、`ChunkStore` 側で concrete client 固有 API・型判定・モデル名分岐を要求しない | DI / Protocol 抽象化の受け入れ基準 |
| TC-14 | `get_by_source_path` は prefix ではなく完全一致で `.bak` を混同しない | backend テストダブルには `study/typescript/generics.md_0` と `study/typescript/generics.md.bak_0` が格納されている | `get_by_source_path("study/typescript/generics.md")` | 戻り値には `id = "study/typescript/generics.md_0"` のみが含まれ、`"study/typescript/generics.md.bak_0"` は含まれない。backend `get(...)` は `where={"source_path": "study/typescript/generics.md"}` で呼ばれる | 完全一致条件の取得側確認 |

## Phase 3: エッジケース

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-20 | `source_path` が空文字の各操作は入力エラーにする | `ChunkCollection` テストダブルは各 backend メソッド呼び出し有無を検査できる | ケース A: `upsert_chunks({source_path: "", chunks: []})`、ケース B: `get_by_source_path("")`、ケース C: `delete_by_source_path("")` | 各ケースで `ChunkStoreInputError` を送出する。対応する backend `upsert` / `get` / `delete` は 1 回も呼ばれない | 操作共通の最小入力境界 |
| TC-21 | 保存前バリデーションが各契約違反を `ChunkStoreInputError` に統一する | `ChunkCollection` テストダブルは `upsert` 呼び出し有無を検査できる | ケース A: `chunk_index = -1`、ケース B: `text = "   "`、ケース C: `embedding = []`、ケース D: `embedding = [0.1, NaN]`、ケース E: `embedding = [0.1, inf]`、ケース F: `embedding = [0.1, "0.2"]`、ケース G: `tags = ["ok", 1]`、ケース H: 2 件の `embedding` 次元が `[0.1, 0.2]` と `[0.3, 0.4, 0.5]` で不一致、ケース I: `headers = 1`、ケース J: `created_at = 1`、ケース K: `updated_at = null` をそれぞれ含む `upsert_chunks(...)` | 各ケースで `ChunkStoreInputError` を送出する。backend `upsert(...)` は 1 回も呼ばれず、保存結果も返さない | 受け入れ基準と境界条件の入力不正群 |
| TC-22 | 存在しない `source_path` の取得は空リストを返す | backend `get(where={"source_path": "study/not-found.md"})` は 0 件を返す | `get_by_source_path("study/not-found.md")` | `[]` を返す。例外は送出しない | 境界条件 |
| TC-23 | 存在しない `source_path` の削除は正常終了し、`deleted_count=0` を返す | backend 側に `"study/not-found.md"` の該当レコードは存在しない | `delete_by_source_path("study/not-found.md")` | 戻り値は `{source_path: "study/not-found.md", deleted_count: 0}` と完全一致する。`ChunkStoreBackendError` は送出しない | 境界条件 |
| TC-24 | backend 取得結果が保存契約を満たさない場合は取得全体を失敗にする | backend `get(...)` は次のいずれかを返す。ケース A: `metadata.source_path = "study/a.md"` なのに `id = "study/b.md_0"`、ケース B: `metadata.chunk_index` 欠落、ケース C: `metadata.chunk_index = -1`、ケース D: `embedding = []`、ケース E: `embedding = [0.1, NaN]` | `get_by_source_path("study/a.md")` | 各ケースで `ChunkStoreRecordFormatError` を送出する。破損していない他レコードが同時に含まれていても、部分返却せず取得結果全体を失敗として扱う | 取得結果の正規化と検証 |

## Phase 4: 外部連携

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-30 | 保存・取得・削除の成功時に規定イベント名と必須キー付きの構造化ログを出す | 構造化ログ収集を有効化し、backend テストダブルで正常系の `upsert` / `get` / `delete` を実行できる | 1. `upsert_chunks(...)` に 4 次元ベクトル 2 件を渡す 2. `get_by_source_path("study/typescript/generics.md")` を実行する 3. `delete_by_source_path("study/typescript/generics.md")` を実行する | `chunk_store_upsert_completed`、`chunk_store_get_completed`、`chunk_store_delete_completed` の各ログがそれぞれちょうど 1 件出力される。`upsert` 成功ログは少なくとも `source_path = "study/typescript/generics.md"`、`chunk_count = 2`、`stored_count = 2`、`vector_dimension = 4` を含む。`get` 成功ログは少なくとも `source_path = "study/typescript/generics.md"`、`returned_count = 2` を含む。`delete` 成功ログは少なくとも `source_path = "study/typescript/generics.md"`、`deleted_count = 2` を含む。追加キーがあってもよい | 成功時可観測性 |
| TC-31 | backend `upsert` 例外は原因付き `ChunkStoreBackendError` にラップされ、失敗ログを出す | backend `upsert(...)` が `TimeoutError("upsert timed out")` を送出し、構造化ログ収集を有効化する | 正常な 4 次元ベクトル 2 件を含む `upsert_chunks(...)` | `ChunkStoreBackendError` を送出し、`__cause__` が元の `TimeoutError("upsert timed out")` と同一である。`event = "chunk_store_upsert_failed"` のログがちょうど 1 件出力され、少なくとも `source_path`、`chunk_count = 2`、`vector_dimension = 4`、`error_type = "TimeoutError"` を含む。例外スタックトレース記録は `exc_info = True` の存在で確認する | backend 例外ラップ |
| TC-32 | backend `get` 例外は原因付き `ChunkStoreBackendError` にラップされ、失敗ログを出す | backend `get(...)` が `ConnectionError("chroma unavailable")` を送出し、構造化ログ収集を有効化する | `get_by_source_path("study/typescript/generics.md")` | `ChunkStoreBackendError` を送出し、`__cause__` が元の `ConnectionError("chroma unavailable")` と同一である。`event = "chunk_store_get_failed"` のログがちょうど 1 件出力され、少なくとも `source_path = "study/typescript/generics.md"`、`error_type = "ConnectionError"` を含む。例外スタックトレース記録は `exc_info = True` の存在で確認する | backend 例外ラップ |
| TC-33 | backend `delete` 例外は原因付き `ChunkStoreBackendError` にラップされ、失敗ログを出す | backend `delete(...)` が `RuntimeError("delete failed")` を送出し、構造化ログ収集を有効化する | `delete_by_source_path("study/typescript/generics.md")` | `ChunkStoreBackendError` を送出し、`__cause__` が元の `RuntimeError("delete failed")` と同一である。`event = "chunk_store_delete_failed"` のログがちょうど 1 件出力され、少なくとも `source_path = "study/typescript/generics.md"`、`error_type = "RuntimeError"` を含む。例外スタックトレース記録は `exc_info = True` の存在で確認する | backend 例外ラップ |

# 網羅性チェック

仕様書の受け入れ基準の各項目に対応するテストケース ID を記載する。
全項目が少なくとも1つのテストケースでカバーされていることを確認する。

| 受け入れ基準 | 対応テストケース |
|---|---|
| `ChunkStore` 実装は ChromaDB concrete client ではなく `ChunkCollection` Protocol を DI で受け取る | TC-13 |
| `upsert_chunks(...)` で各チャンクの ID が `{source_path}_{chunk_index}` 形式で生成される | TC-01 |
| `upsert_chunks(...)` で正常なチャンク群を渡すと、入力順に対応する `stored_ids` と `stored_count` が返る | TC-01 |
| `upsert_chunks(...)` に空バッチを渡した場合、backend 呼び出しなしで成功する | TC-10 |
| 1 回の保存要求に重複 `chunk_index` が含まれる場合、`ChunkStoreDuplicateChunkIndexError` が送出される | TC-11 |
| 入力チャンクに空本文、非有限値ベクトル、型不正タグなどがある場合、`ChunkStoreInputError` が送出される | TC-12, TC-20, TC-21 |
| `delete_by_source_path(...)` は同一 `source_path` のチャンクを全件削除し、存在しない場合は `deleted_count=0` を返す | TC-03, TC-23 |
| `get_by_source_path(...)` は同一 `source_path` のチャンクだけを `chunk_index` 昇順で返す | TC-02, TC-14, TC-22 |
| backend 呼び出しが失敗した場合、各操作で `ChunkStoreBackendError` が送出される | TC-31, TC-32, TC-33 |
| backend から不整合レコードが返った場合、`ChunkStoreRecordFormatError` が送出される | TC-24 |
| 保存・取得・削除の成功時と backend 障害時に、規定イベント名で `structlog` の構造化ログが出力される | TC-10, TC-30, TC-31, TC-32, TC-33 |

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
