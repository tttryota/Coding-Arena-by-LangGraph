---
feature: ingestion/chunk-store
status: ready
---

# 概要

- この機能が解決する課題:
  ingestion パイプラインで生成したチャンク本文・Embedding・メタデータを、後続の検索や再取り込みで再利用できる形で永続化する。ファイル更新時に `source_path` 単位で既存チャンクを安全に差し替えられるようにする。
- 利用者・呼び出し元・前提条件:
  呼び出し元は ingestion 系ユースケースまたはそれに準ずるアプリケーションサービスを想定する。永続化先は ChromaDB だが、本機能は ChromaDB クライアントそのものではなく `ChunkCollection` Protocol 越しに利用し、DI で差し替え可能であることを前提とする。構造化ログ出力には `structlog` を利用する。

# 入出力

- 入力:
  本機能は `ChunkStore` として次の 3 操作を提供する。
  - `upsert_chunks(input: ChunkStoreUpsertInput) -> ChunkStoreUpsertResult`
    - `source_path: str`
      - ファイル単位の論理キー。空文字不可。
      - ID 生成およびメタデータ保存に使用する。
    - `chunks: list[ChunkStoreChunkInput]`
      - 同一 `source_path` に属するチャンク一覧。入力順は保存要求順として保持する。
      - `ChunkStoreChunkInput`:
        - `chunk_index: int`
          - `source_path` 内での 0 始まりの順序。0 以上の整数でなければならない。
        - `text: str`
          - 保存対象本文。`strip()` 後に空であってはならない。
        - `embedding: list[float]`
          - 空でない有限実数列。バッチ内の全チャンクで次元一致が必要。
        - `headers: str`
          - H1/H2 由来の見出し階層。空文字は許容する。
        - `tags: list[str]`
          - チャンクに紐づくタグ一覧。空リストは許容する。
        - `created_at: str`
          - ISO 8601 文字列。保存時にそのままメタデータへ格納する。
        - `updated_at: str`
          - ISO 8601 文字列。保存時にそのままメタデータへ格納する。
  - `delete_by_source_path(source_path: str) -> ChunkStoreDeleteResult`
    - `source_path: str`
      - 削除対象ファイルの論理キー。空文字不可。
  - `get_by_source_path(source_path: str) -> list[StoredChunk]`
    - `source_path: str`
      - 取得対象ファイルの論理キー。空文字不可。
- 出力:
  - `ChunkStoreUpsertResult`
    - `source_path: str`
    - `stored_count: int`
      - 保存対象として受理されたチャンク件数。空バッチでは 0。
    - `stored_ids: list[str]`
      - 入力順で返す保存 ID 一覧。各 ID は `{source_path}_{chunk_index}`。
  - `ChunkStoreDeleteResult`
    - `source_path: str`
    - `deleted_count: int`
      - 削除されたチャンク件数。該当なしの場合は 0。
  - `StoredChunk`
    - `id: str`
      - `{source_path}_{chunk_index}` 形式の永続 ID。
    - `text: str`
    - `embedding: list[float]`
    - `metadata`
      - `source_path: str`
      - `chunk_index: int`
      - `headers: str`
      - `tags: list[str]`
      - `created_at: str`
      - `updated_at: str`
    - `get_by_source_path(...)` の返却順は `metadata.chunk_index` 昇順とする。
- エラー:
  送出する例外の型名と発生条件を定義する。
  例外型はテストで使用されるため、型名を具体的に指定すること。
  実装詳細ではなく、呼び出し元との契約として記述する。
  - `ChunkStoreInputError`: `source_path`、`chunks`、各チャンク項目が契約を満たさない場合。空文字 `source_path`、負の `chunk_index`、空本文、空ベクトル、非数値、`NaN`/`inf`、`tags` 内の非文字列を含む
  - `ChunkStoreDuplicateChunkIndexError`: 1 回の `upsert_chunks(...)` 内で同一 `chunk_index` が重複した場合
  - `ChunkStoreBackendError`: `ChunkCollection` Protocol 実装との `upsert`、`get`、`delete` のいずれかが失敗した場合。ChromaDB 未起動、コレクション取得失敗、接続断、タイムアウトを含む
  - `ChunkStoreRecordFormatError`: backend から取得したレコードが保存契約を満たさない場合。`id` と `metadata` の不整合、必須メタデータ欠落、`chunk_index` 不正、ベクトル形式不正を含む

# 具体例

代表的な入力と、それに対して期待される出力をデータ例で示す。
テストケース生成やレビューで曖昧さが出ないよう、入力・出力ともに具体値で書く。

## 例1

- 入力:
  `upsert_chunks(...)`
  ```yaml
  source_path: "study/typescript/generics.md"
  chunks:
    - chunk_index: 0
      text: "TypeScriptのジェネリクスは型引数で再利用性を高める。"
      embedding: [0.12, -0.03, 0.44, 0.08]
      headers: "TypeScript入門 > ジェネリクス"
      tags: ["TypeScript"]
      created_at: "2026-05-17T10:00:00+09:00"
      updated_at: "2026-05-17T10:00:00+09:00"
    - chunk_index: 1
      text: "extends で型制約を付与できる。"
      embedding: [0.09, 0.11, -0.05, 0.27]
      headers: "TypeScript入門 > ジェネリクス"
      tags: ["TypeScript"]
      created_at: "2026-05-17T10:00:00+09:00"
      updated_at: "2026-05-17T10:00:00+09:00"
  ```
- 期待される出力:
  ```yaml
  source_path: "study/typescript/generics.md"
  stored_count: 2
  stored_ids:
    - "study/typescript/generics.md_0"
    - "study/typescript/generics.md_1"
  ```

## 例2

- 入力:
  `get_by_source_path("study/typescript/generics.md")`
  バックエンドには `chunk_index=1` と `chunk_index=0` の順で保存済みとする。
- 期待される出力:
  ```yaml
  - id: "study/typescript/generics.md_0"
    text: "TypeScriptのジェネリクスは型引数で再利用性を高める。"
    embedding: [0.12, -0.03, 0.44, 0.08]
    metadata:
      source_path: "study/typescript/generics.md"
      chunk_index: 0
      headers: "TypeScript入門 > ジェネリクス"
      tags: ["TypeScript"]
      created_at: "2026-05-17T10:00:00+09:00"
      updated_at: "2026-05-17T10:00:00+09:00"
  - id: "study/typescript/generics.md_1"
    text: "extends で型制約を付与できる。"
    embedding: [0.09, 0.11, -0.05, 0.27]
    metadata:
      source_path: "study/typescript/generics.md"
      chunk_index: 1
      headers: "TypeScript入門 > ジェネリクス"
      tags: ["TypeScript"]
      created_at: "2026-05-17T10:00:00+09:00"
      updated_at: "2026-05-17T10:00:00+09:00"
  ```

## 例3

- 入力:
  `delete_by_source_path("study/typescript/generics.md")`
  事前状態として `study/typescript/generics.md_0` と `study/typescript/generics.md_1` が保存されている。
- 期待される出力:
  ```yaml
  source_path: "study/typescript/generics.md"
  deleted_count: 2
  ```

## 例4

- 入力:
  `upsert_chunks(...)`
  ```yaml
  source_path: "study/invalid.md"
  chunks:
    - chunk_index: 0
      text: "本文A"
      embedding: [0.1, 0.2]
      headers: ""
      tags: []
      created_at: "2026-05-17T10:00:00+09:00"
      updated_at: "2026-05-17T10:00:00+09:00"
    - chunk_index: 0
      text: "本文B"
      embedding: [0.3, 0.4]
      headers: ""
      tags: []
      created_at: "2026-05-17T10:00:00+09:00"
      updated_at: "2026-05-17T10:00:00+09:00"
  ```
- 期待される出力:
  `ChunkStoreDuplicateChunkIndexError` が送出される。backend の `upsert` は呼び出されない。

# 主要ルール

1. Protocol による ChromaDB 抽象化:
   - 条件:
     `ChunkStore` 実装が ChromaDB へアクセスする場合。
   - 振る舞い:
     実装は `ChunkCollection` Protocol のみへ依存する。少なくとも `upsert(ids, documents, embeddings, metadatas) -> None`、`get(where: dict[str, object]) -> RawChunkCollectionResult`、`delete(where: dict[str, object]) -> None` を利用できればよい。呼び出し元は concrete class ではなく Protocol 実装を DI で注入する。
2. `source_path` 単位の保存契約:
   - 条件:
     `upsert_chunks(...)` を呼び出す場合。
   - 振る舞い:
     1 回の保存要求は単一 `source_path` に属するチャンク群として扱う。保存される全レコードの `metadata.source_path` は入力 `source_path` と一致しなければならない。
3. ナチュラルキーによる ID 生成:
   - 条件:
     保存対象チャンクを永続化する場合。
   - 振る舞い:
     各チャンクの ID は `"{source_path}_{chunk_index}"` で決定的に生成する。ID は入力で受け取らず、本機能が必ず再計算する。
4. 保存前バリデーション:
   - 条件:
     `upsert_chunks(...)` に 1 件以上のチャンクが渡される場合。
   - 振る舞い:
     backend 呼び出し前に全チャンクを検証する。`chunk_index` は 0 以上の整数、`text` は `strip()` 後に空でない文字列、`embedding` は空でない有限実数列、`headers` は文字列、`tags` は文字列リスト、`created_at` と `updated_at` は文字列でなければならない。1 件でも不正があれば `ChunkStoreInputError` を送出する。
5. 同一ファイル内の重複チャンク拒否:
   - 条件:
     1 回の保存要求に同一 `chunk_index` が複数含まれる場合。
   - 振る舞い:
     バッチ全体を失敗とし、`ChunkStoreDuplicateChunkIndexError` を送出する。後勝ち上書きや部分保存は行わない。
6. 空バッチの短絡成功:
   - 条件:
     `upsert_chunks(...)` の `chunks` が空リストの場合。
   - 振る舞い:
     `stored_count=0`、`stored_ids=[]` を返す。backend の `upsert` は呼び出さない。成功ログは出力する。
7. `source_path` による一括削除:
   - 条件:
     `delete_by_source_path(source_path)` を呼び出す場合。
   - 振る舞い:
     `where={"source_path": source_path}` の完全一致条件で該当レコードを削除する。削除対象が 0 件でも成功とし、`deleted_count=0` を返す。
8. `source_path` による一括取得:
   - 条件:
     `get_by_source_path(source_path)` を呼び出す場合。
   - 振る舞い:
     `where={"source_path": source_path}` の完全一致条件で該当レコードを取得し、`chunk_index` 昇順で返す。該当なしの場合は空リストを返す。
9. 取得結果の正規化と検証:
   - 条件:
     backend が取得結果を返した場合。
   - 振る舞い:
     各レコードについて `id`、`text`、`embedding`、必須メタデータを検証し、`id == "{metadata.source_path}_{metadata.chunk_index}"` を満たすことを確認する。満たさない場合は `ChunkStoreRecordFormatError` を送出する。
10. backend 例外のラップ:
    - 条件:
      backend Protocol 実装が `upsert`、`get`、`delete` のいずれかで例外を送出した場合。
    - 振る舞い:
      元例外を原因として保持したまま `ChunkStoreBackendError` を送出する。呼び出し元は ChromaDB 系障害として一括で扱える。
11. structlog による構造化ログ:
    - 条件:
      保存・取得・削除の成功時または backend 障害時。
    - 振る舞い:
      `structlog` で構造化ログを出力する。イベント名は保存成功 `chunk_store_upsert_completed`、保存失敗 `chunk_store_upsert_failed`、取得成功 `chunk_store_get_completed`、取得失敗 `chunk_store_get_failed`、削除成功 `chunk_store_delete_completed`、削除失敗 `chunk_store_delete_failed` とする。少なくとも `source_path`、`chunk_count`、`stored_count`、`returned_count`、`deleted_count`、`vector_dimension`、`error_type` を必要に応じて含める。

# 境界条件

- ケース:
  `upsert_chunks(...)` の `chunks` が空リスト。
  - 振る舞い:
    成功として扱い、`stored_count=0`、`stored_ids=[]` を返す。
  - 理由:
    上流の分割結果が空でも、差し替えフロー全体を例外で止める必要はないため。
- ケース:
  `delete_by_source_path(...)` の対象 `source_path` が存在しない。
  - 振る舞い:
    `ChunkStoreBackendError` にはせず、`deleted_count=0` を返す。
  - 理由:
    ファイル削除や初回更新時に「消すものがない」状態は正常系だから。
- ケース:
  `get_by_source_path(...)` の対象 `source_path` が存在しない。
  - 振る舞い:
    空リストを返す。
  - 理由:
    呼び出し元が差し替え前確認やデバッグ用途で安全に照会できるようにするため。
- ケース:
  入力チャンクの `embedding` 次元がバッチ内で不一致。
  - 振る舞い:
    `ChunkStoreInputError` を送出する。
  - 理由:
    同一コレクションへ保存するベクトルとして不整合であり、保存後に検知すると切り戻しが複雑になるため。
- ケース:
  backend から返った 1 件の `metadata.source_path` は `"study/a.md"` だが、`id` が `"study/b.md_0"` である。
  - 振る舞い:
    `ChunkStoreRecordFormatError` を送出し、その取得結果全体を失敗として扱う。
  - 理由:
    破損レコードを黙って返すと、差し替えや再取り込みの整合性が壊れるため。
- ケース:
  `source_path` が `"study/typescript/generics.md"` のとき、`"study/typescript/generics.md.bak"` のレコードも backend に存在する。
  - 振る舞い:
    `.bak` 側は取得・削除対象に含めない。
  - 理由:
    `source_path` 操作は prefix ではなく完全一致でなければならないため。
- ルール間の相互作用:
  1. `upsert_chunks(...)` では、まず `source_path` と `chunks` 全件の妥当性を検証し、その後に `chunk_index` 重複判定を行う。どちらかで失敗した場合は backend を呼び出さない。
  2. `get_by_source_path(...)` では backend 取得成功後にのみソートとレコード検証を行い、backend 例外は `ChunkStoreBackendError`、取得内容不正は `ChunkStoreRecordFormatError` を優先する。
  3. `delete_by_source_path(...)` の 0 件削除は正常終了として扱い、backend 接続失敗時のみ `ChunkStoreBackendError` を送出する。

# 非機能・制約

- 性能:
  保存は 1 回の `upsert_chunks(...)` につき backend の `upsert` を 1 回で完了すること。取得と削除は `source_path` 単位で完結し、少なくともチャンク件数に対して線形時間で処理できること。
- 可観測性:
  `structlog` により、少なくとも `event`、`source_path`、`chunk_count`、`stored_count`、`returned_count`、`deleted_count`、`vector_dimension`、`error_type` を機械可読なキーで記録できること。失敗時は例外スタックトレースを残せること。
- 外部依存:
  永続化 backend は `ChunkCollection` Protocol 実装に限定して参照し、ChromaDB の concrete client には直接依存しない。現在の標準実装は ChromaDB を想定するが、本仕様はその差し替えを妨げない。

# モジュール構成

design 時に、各モジュールが概ね 200-300 行に収まるかを責務単位で概算し、実装の切り方を先に決める。
厳密な計算式は不要だが、例外型・データ構造・主要ルール・バリデーション・ログなどの構成要素を踏まえて判断する。
単一ファイルで十分な場合も、その判断を明記する。

- 構成方針:
  - `単一ファイルで実装する`
- 概算メモ:
  - 例外型 4 つ（12行）、入出力モデル 5 つ（40行）、Protocol 1 つ（10行）、バリデーション（50行）、3 操作の本体（60行）、ログ（30行）、imports（20行）で合計約 220行
  - 200行を若干超えるが、全て同一永続化層の責務であり分割による複雑化の方がリスクが高い
- モジュール一覧:
  - `backend/ingestion/infrastructure/chroma_chunk_store.py`
    - 責務:
      入出力モデル、例外型、`ChunkCollection` Protocol、自然キー生成、入力検証、保存 payload 組み立て、取得結果の正規化、`structlog` 出力、backend 例外ラップ
    - 含める要素:
      `ChunkStoreUpsertInput`、`ChunkStoreChunkInput`、`ChunkStoreUpsertResult`、`ChunkStoreDeleteResult`、`StoredChunk`、各例外型、`ChunkCollection` Protocol、`ChromaChunkStore` クラス

# 技術判断

品質に直結する技術選定や実装方針がある場合は、その判断と理由を書く。

- 判断:
  `source_path` 単位で保存 API を切り、1 回の保存要求で複数ファイルを混在させない。
  - 理由:
    差し替えフローが「削除 -> 同一 `source_path` の再保存」で閉じ、ログとテストの粒度も安定するため。
- 判断:
  ID は caller 提供ではなく、`source_path` と `chunk_index` から毎回再生成する。
  - 理由:
    同一ファイルの再取り込み時に決定的に同じ ID を再利用でき、重複管理が単純になるため。
- 判断:
  取得結果も再検証し、保存契約を満たさない raw データは `ChunkStoreRecordFormatError` とする。
  - 理由:
    永続層の破損や Protocol 実装ミスを早期に検知し、上位層へ不整合データを渡さないため。
- 判断:
  `source_path` による検索条件は prefix ではなく完全一致とする。
  - 理由:
    `study/a.md` と `study/a.md.bak` のような近接パス混入を防ぎ、削除事故を避けるため。

# スコープ外

この機能では扱わないこと、別 issue / 別機能で扱うことを明示する。

- 対応しないこと:
  ベクトル類似度検索、タグ検索、ハイブリッド検索
- 対応しないこと:
  チャンク単位の個別削除・個別取得
- 対応しないこと:
  `source_path` 自体の正規化ルール策定やファイルシステム走査
- 対応しないこと:
  ChromaDB コレクション生成戦略、インデックスチューニング、再試行ポリシー
- 対応しないこと:
  部分成功を返す保存 API

# 受け入れ基準

検証可能な条件をチェックリスト形式で書く。実装手段ではなく、満たされるべき事実を書く。

- [ ] `ChunkStore` 実装は ChromaDB concrete client ではなく `ChunkCollection` Protocol を DI で受け取る
- [ ] `upsert_chunks(...)` で各チャンクの ID が `{source_path}_{chunk_index}` 形式で生成される
- [ ] `upsert_chunks(...)` で正常なチャンク群を渡すと、入力順に対応する `stored_ids` と `stored_count` が返る
- [ ] `upsert_chunks(...)` に空バッチを渡した場合、backend 呼び出しなしで成功する
- [ ] 1 回の保存要求に重複 `chunk_index` が含まれる場合、`ChunkStoreDuplicateChunkIndexError` が送出される
- [ ] 入力チャンクに空本文、非有限値ベクトル、型不正タグなどがある場合、`ChunkStoreInputError` が送出される
- [ ] `delete_by_source_path(...)` は同一 `source_path` のチャンクを全件削除し、存在しない場合は `deleted_count=0` を返す
- [ ] `get_by_source_path(...)` は同一 `source_path` のチャンクだけを `chunk_index` 昇順で返す
- [ ] backend 呼び出しが失敗した場合、各操作で `ChunkStoreBackendError` が送出される
- [ ] backend から不整合レコードが返った場合、`ChunkStoreRecordFormatError` が送出される
- [ ] 保存・取得・削除の成功時と backend 障害時に、規定イベント名で `structlog` の構造化ログが出力される

# テスト観点メモ

各主要ルールに対して最低1つ、各境界条件に対して最低1つの観点を列挙する。
受け入れ基準の各項目が少なくとも1つの観点でカバーされていることを確認する。

- 正常系:
  - 2 件の正常チャンクを保存し、`stored_count=2` と自然キー ID が入力順で返ること
  - 取得結果が backend の返却順に依存せず `chunk_index` 昇順へ正規化されること
  - 同一 `source_path` の 2 件削除で `deleted_count=2` が返ること
  - `ChunkCollection` Protocol 実装のテストダブルを注入して機能が動作すること
- 境界系:
  - 空バッチ保存で backend `upsert` が呼ばれないこと
  - 存在しない `source_path` の削除で `deleted_count=0` が返ること
  - 存在しない `source_path` の取得で空リストが返ること
  - 同一バッチのベクトル次元不一致で `ChunkStoreInputError` になること
  - `source_path` 完全一致のため `.md` と `.md.bak` が混同されないこと
- 異常系:
  - 重複 `chunk_index` を含む保存で `ChunkStoreDuplicateChunkIndexError` が送出されること
  - 空本文、`NaN` 含みベクトル、`tags` 内の非文字列で `ChunkStoreInputError` が送出されること
  - backend `upsert`、`get`、`delete` 例外がそれぞれ `ChunkStoreBackendError` にラップされること
  - backend 取得結果の `id` と `metadata.source_path` / `chunk_index` が不整合な場合に `ChunkStoreRecordFormatError` が送出されること
