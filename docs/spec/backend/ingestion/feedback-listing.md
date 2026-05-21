---
feature: ingestion/feedback-listing
status: ready
---

# 概要

- この機能が解決する課題:
  取り込み済み `IngestionFeedback` を日付範囲・既読状態でフィルタ取得し、個別に既読化できるようにする。presentation 層がこの機能を HTTP エンドポイントとして公開することで、フロントエンドからフィードバック一覧の閲覧・既読化が可能になる。
- 利用者・呼び出し元・前提条件:
  呼び出し元は presentation 層の API エンドポイントを想定する。フィードバックレコードは `ingestion-feedback` モジュールによって事前に永続化されている前提。本機能は `Protocol` による DI で注入された永続化ポートを利用する。構造化ログ出力には `structlog` を用いる。
- スコープ補足:
  今回の修正は一覧取得時の既読状態フィルタ契約の補完であり、状態変更機能の追加ではない。既読化は `mark_feedback_as_read` のみを扱い、既読解除は引き続きスコープ外とする。

# 入出力

- 公開 API:
  モジュールレベル関数を 2 つ公開する。依存は keyword-only 引数で注入する。
  ```python
  list_feedbacks(
      query: FeedbackListingQuery,
      *,
      reader: FeedbackListingReader,
  ) -> FeedbackListingResult

  mark_feedback_as_read(
      feedback_id: UUID,
      *,
      writer: FeedbackReadWriter,
      now: str,
  ) -> FeedbackListItem
  ```

- 共通日時文字列契約:
  `FeedbackListingQuery.date_from`、`FeedbackListingQuery.date_to`、`mark_feedback_as_read(..., now=...)`、および reader / writer が返す `FeedbackListItem.created_at` に同じ契約を適用する。
  - 受理する形式:
    `YYYY-MM-DDTHH:MM:SS(Z|[+-]HH:MM)` または `YYYY-MM-DDTHH:MM:SS.[0-9]{1,6}(Z|[+-]HH:MM)` を受理する。すなわち小数秒は省略可能で、含める場合は 1 から 6 桁まで受理する。
  - 受理例:
    `2026-05-20T12:34:56+09:00`、`2026-05-20T03:34:56Z`、`2026-05-20T03:34:56.1Z`、`2026-05-20T03:34:56.12345+09:00`、`2026-05-20T03:34:56.123456-04:00`
  - 拒否する形式:
    `T` 以外の区切りを使う文字列、offset を持たない文字列、上記形式に合致しない ISO 8601 派生表現を拒否する。たとえば `2026-05-20 12:34:56+09:00`、`2026-05-20T12:34:56`、`2026-05-20` は不正入力として扱う。
  - 正規化と比較:
    バリデーション後は aware datetime として解釈し、`Z` は UTC offset `+00:00` と同じ instant として扱う。`date_from > date_to` 判定、`created_at` の並び順判定、その他の時刻比較は、文字列比較ではなくパース後の instant 比較で行う。
  - 文字列の保持:
    受理済みの `date_from` / `date_to` / `now` は reader / writer へ元の文字列のまま渡してよい。比較や検証のための内部正規化はしても、公開 DTO や永続化ポートの文字列表現をこの仕様で強制的に書き換えない。

- 入力:
  - `FeedbackListingQuery`
    一覧取得の公開入力 DTO。frozen dataclass。
    - `date_from: str | None`
      フィルタ開始日時。共通日時文字列契約に従う。`None` の場合は下限なし。`created_at >= date_from` を instant 比較で判定する（inclusive）。
    - `date_to: str | None`
      フィルタ終了日時。共通日時文字列契約に従う。`None` の場合は上限なし。`created_at <= date_to` を instant 比較で判定する（inclusive）。
    - `read_status: Literal["all", "unread", "read"]`
      既読状態フィルタ。`list_feedbacks` はこの値を `reader.find_feedbacks` へそのまま委譲し、返却後に `is_read` の追加フィルタを行わない。
      `all` は既読状態で絞り込まない検索意図。
      `unread` は未読のみを reader に要求する検索意図。
      `read` は既読のみを reader に要求する検索意図。

  - `mark_feedback_as_read` の入力:
    - `feedback_id: UUID` — 対象フィードバックの ID。
    - `now: str` — 既読化日時を表す文字列。共通日時文字列契約に従う。バリデーション後に `read_at` に使う。テスタビリティのために外部注入する。

- 依存インターフェース:
  - `FeedbackListingReader`
    `find_feedbacks(*, date_from: str | None, date_to: str | None, read_status: Literal["all", "unread", "read"]) -> list[FeedbackListItem]` を提供する Protocol。
    - 戻り値の順序は不定。ソートはモジュール側で行う。
    - `created_at` は共通日時文字列契約に従う DTO を返す。
  - `FeedbackReadWriter`
    `get_by_id(feedback_id: UUID) -> FeedbackListItem | None` を提供する Protocol。
    `update_read_status(feedback_id: UUID, *, is_read: bool, read_at: str) -> FeedbackListItem` を提供する Protocol。
    - `get_by_id` と `update_read_status` が `FeedbackListItem` を返す場合、その `created_at` は共通日時文字列契約に従う。
    - `mark_feedback_as_read` は `get_by_id` / `update_read_status` の返却 DTO を返却前に検証し、契約違反の `created_at` をそのまま公開しない。
  - `structlog`
    構造化ログ出力。モジュールロガーを使い、各ログ呼び出しでコンテキスト情報を渡す。

- 出力:
  - `FeedbackListingResult`
    frozen dataclass。
    - `items: list[FeedbackListItem]`
      `created_at` を instant 比較した降順（新しい順）でソート済み。同一 instant の場合は `id` の文字列表現昇順を tie-break とする。
    - `total_count: int`
      `items` の件数（フィルタ後）。
  - `FeedbackListItem`
    frozen dataclass。
    - `id: UUID`
    - `source_path: str`
    - `roadmap_item_id: UUID | None`
    - `title: str`
    - `body: str`
    - `is_read: bool`
    - `created_at: str`
    - `read_at: str | None`

- エラー:
  送出する例外の型名と発生条件を定義する。
  - `FeedbackListingInputError`:
    `date_from`、`date_to`、`now` が共通日時文字列契約に違反する場合、`read_status` が `all` / `unread` / `read` 以外の場合、または instant 比較後に `date_from > date_to` となる場合。
  - `FeedbackListingNotFoundError`:
    `mark_feedback_as_read` の対象 ID に対応するフィードバックが存在しない場合。
  - `FeedbackListingStoreError`:
    永続化ポートの操作が失敗した場合、または `reader.find_feedbacks` / `writer.get_by_id` / `writer.update_read_status` が返した `FeedbackListItem.created_at` が共通日時文字列契約に違反する場合。`list_feedbacks` のソート時だけでなく、`mark_feedback_as_read` が返却前に writer DTO を検証した結果の契約違反も同じ例外に分類する。

# 具体例

- 注記:
  以下の例で示す `FeedbackListItem` はすべて公開 DTO の完全形であり、必須 8 フィールドを省略しない。`reader.find_feedbacks` / `writer.get_by_id` / `writer.update_read_status` の返却値と関数返り値の例は、いずれも抜粋ではなく完全一致比較の対象として扱う。

## 例1: フィルタなしで全件取得

- 入力:
  ```yaml
  query:
    date_from: null
    date_to: null
    read_status: all
  reader.find_feedbacks の返却値（順序不定）:
    - id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
      source_path: "study/docker/compose.md"
      roadmap_item_id: null
      title: "study/docker/compose.md の取り込みフィードバック"
      body: "Docker Compose 設定の補足メモ"
      is_read: true
      created_at: "2026-05-17T10:00:00+09:00"
      read_at: "2026-05-19T12:00:00+09:00"
    - id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
      source_path: "study/typescript/generics.md"
      roadmap_item_id: "11111111-1111-1111-1111-111111111111"
      title: "study/typescript/generics.md の取り込みフィードバック"
      body: "ジェネリクス制約の追記候補"
      is_read: false
      created_at: "2026-05-20T21:30:00+09:00"
      read_at: null
  ```
- 期待される出力:
  ```yaml
  items:
    - id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"  # 新しい instant が先
      source_path: "study/typescript/generics.md"
      roadmap_item_id: "11111111-1111-1111-1111-111111111111"
      title: "study/typescript/generics.md の取り込みフィードバック"
      body: "ジェネリクス制約の追記候補"
      is_read: false
      created_at: "2026-05-20T21:30:00+09:00"
      read_at: null
    - id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
      source_path: "study/docker/compose.md"
      roadmap_item_id: null
      title: "study/docker/compose.md の取り込みフィードバック"
      body: "Docker Compose 設定の補足メモ"
      is_read: true
      created_at: "2026-05-17T10:00:00+09:00"
      read_at: "2026-05-19T12:00:00+09:00"
  total_count: 2
  ```

## 例2: 未読のみフィルタ

- 入力:
  ```yaml
  query:
    date_from: null
    date_to: null
    read_status: unread
  reader.find_feedbacks の返却値:
    - id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
      source_path: "study/typescript/generics.md"
      roadmap_item_id: "11111111-1111-1111-1111-111111111111"
      title: "study/typescript/generics.md の取り込みフィードバック"
      body: "ジェネリクス制約の追記候補"
      is_read: false
      created_at: "2026-05-20T21:30:00+09:00"
      read_at: null
  ```
- 期待される出力:
  ```yaml
  items:
    - id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
      source_path: "study/typescript/generics.md"
      roadmap_item_id: "11111111-1111-1111-1111-111111111111"
      title: "study/typescript/generics.md の取り込みフィードバック"
      body: "ジェネリクス制約の追記候補"
      is_read: false
      created_at: "2026-05-20T21:30:00+09:00"
      read_at: null
  total_count: 1
  ```

## 例3: 既読のみフィルタ

- 入力:
  ```yaml
  query:
    date_from: null
    date_to: null
    read_status: read
  reader.find_feedbacks の返却値:
    - id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
      source_path: "study/docker/compose.md"
      roadmap_item_id: null
      title: "study/docker/compose.md の取り込みフィードバック"
      body: "Docker Compose 設定の補足メモ"
      is_read: true
      created_at: "2026-05-17T10:00:00+09:00"
      read_at: "2026-05-19T12:00:00+09:00"
  ```
- 期待される出力:
  ```yaml
  items:
    - id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
      source_path: "study/docker/compose.md"
      roadmap_item_id: null
      title: "study/docker/compose.md の取り込みフィードバック"
      body: "Docker Compose 設定の補足メモ"
      is_read: true
      created_at: "2026-05-17T10:00:00+09:00"
      read_at: "2026-05-19T12:00:00+09:00"
  total_count: 1
  ```

## 例4: 日付範囲フィルタは instant 比較で判定する

- 入力:
  ```yaml
  query:
    date_from: "2026-05-19T15:00:00Z"
    date_to: "2026-05-20T14:59:59.500000Z"
    read_status: all
  reader.find_feedbacks の返却値:
    - id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
      source_path: "study/typescript/generics.md"
      roadmap_item_id: "11111111-1111-1111-1111-111111111111"
      title: "study/typescript/generics.md の取り込みフィードバック"
      body: "ジェネリクス制約の追記候補"
      is_read: false
      created_at: "2026-05-20T21:30:00+09:00"
      read_at: null
    - id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
      source_path: "study/python/datetime.md"
      roadmap_item_id: "22222222-2222-2222-2222-222222222222"
      title: "study/python/datetime.md の取り込みフィードバック"
      body: "UTC 境界の確認"
      is_read: false
      created_at: "2026-05-20T00:00:00+09:00"
      read_at: null
  ```
- 期待される出力:
  ```yaml
  items:
    - id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"  # 2026-05-20T12:30:00Z
      source_path: "study/typescript/generics.md"
      roadmap_item_id: "11111111-1111-1111-1111-111111111111"
      title: "study/typescript/generics.md の取り込みフィードバック"
      body: "ジェネリクス制約の追記候補"
      is_read: false
      created_at: "2026-05-20T21:30:00+09:00"
      read_at: null
    - id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"  # 2026-05-19T15:00:00Z
      source_path: "study/python/datetime.md"
      roadmap_item_id: "22222222-2222-2222-2222-222222222222"
      title: "study/python/datetime.md の取り込みフィードバック"
      body: "UTC 境界の確認"
      is_read: false
      created_at: "2026-05-20T00:00:00+09:00"
      read_at: null
  total_count: 2
  ```

## 例5: 同一 instant の並び順

- 入力:
  ```yaml
  query:
    date_from: null
    date_to: null
    read_status: all
  reader.find_feedbacks の返却値:
    - id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
      source_path: "study/docker/compose.md"
      roadmap_item_id: null
      title: "study/docker/compose.md の取り込みフィードバック"
      body: "Docker Compose 設定の補足メモ"
      is_read: true
      created_at: "2026-05-20T03:00:00Z"
      read_at: "2026-05-20T06:00:00Z"
    - id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
      source_path: "study/typescript/generics.md"
      roadmap_item_id: "11111111-1111-1111-1111-111111111111"
      title: "study/typescript/generics.md の取り込みフィードバック"
      body: "ジェネリクス制約の追記候補"
      is_read: false
      created_at: "2026-05-20T12:00:00+09:00"
      read_at: null
  ```
- 期待される出力:
  ```yaml
  items:
    - id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"  # 同一 instant のため id 昇順で先頭
      source_path: "study/typescript/generics.md"
      roadmap_item_id: "11111111-1111-1111-1111-111111111111"
      title: "study/typescript/generics.md の取り込みフィードバック"
      body: "ジェネリクス制約の追記候補"
      is_read: false
      created_at: "2026-05-20T12:00:00+09:00"
      read_at: null
    - id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
      source_path: "study/docker/compose.md"
      roadmap_item_id: null
      title: "study/docker/compose.md の取り込みフィードバック"
      body: "Docker Compose 設定の補足メモ"
      is_read: true
      created_at: "2026-05-20T03:00:00Z"
      read_at: "2026-05-20T06:00:00Z"
  total_count: 2
  ```

## 例6: 未読フィードバックの既読化

- 入力:
  ```yaml
  feedback_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
  now: "2026-05-21T00:00:00Z"
  writer.get_by_id の返却値:
    id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    source_path: "study/typescript/generics.md"
    roadmap_item_id: "11111111-1111-1111-1111-111111111111"
    title: "study/typescript/generics.md の取り込みフィードバック"
    body: "ジェネリクス制約の追記候補"
    is_read: false
    created_at: "2026-05-20T21:30:00+09:00"
    read_at: null
  writer.update_read_status の返却値:
    id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    source_path: "study/typescript/generics.md"
    roadmap_item_id: "11111111-1111-1111-1111-111111111111"
    title: "study/typescript/generics.md の取り込みフィードバック"
    body: "ジェネリクス制約の追記候補"
    is_read: true
    created_at: "2026-05-20T21:30:00+09:00"
    read_at: "2026-05-21T00:00:00Z"
  ```
- 期待される出力:
  ```yaml
  id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
  source_path: "study/typescript/generics.md"
  roadmap_item_id: "11111111-1111-1111-1111-111111111111"
  title: "study/typescript/generics.md の取り込みフィードバック"
  body: "ジェネリクス制約の追記候補"
  is_read: true
  created_at: "2026-05-20T21:30:00+09:00"
  read_at: "2026-05-21T00:00:00Z"
  ```

## 例7: 既読フィードバックの再既読化（冪等）

- 入力:
  ```yaml
  feedback_id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
  now: "2026-05-21T10:00:00+09:00"
  writer.get_by_id の返却値:
    id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    source_path: "study/docker/compose.md"
    roadmap_item_id: null
    title: "study/docker/compose.md の取り込みフィードバック"
    body: "Docker Compose 設定の補足メモ"
    is_read: true
    created_at: "2026-05-17T10:00:00+09:00"
    read_at: "2026-05-19T12:00:00+09:00"
  ```
- 期待される出力:
  ```yaml
  id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
  source_path: "study/docker/compose.md"
  roadmap_item_id: null
  title: "study/docker/compose.md の取り込みフィードバック"
  body: "Docker Compose 設定の補足メモ"
  is_read: true
  created_at: "2026-05-17T10:00:00+09:00"
  read_at: "2026-05-19T12:00:00+09:00"
  ```
  `writer.update_read_status` は呼ばれない。

# 主要ルール

1. 共通日時文字列契約の適用:
   - 条件: `date_from` / `date_to` / `now` を受け取る場合、または `FeedbackListItem.created_at` を扱う場合。
   - 振る舞い: すべて共通日時文字列契約で検証する。日時比較は文字列ではなく aware datetime の instant 比較で行う。
2. 降順ソート:
   - 条件: `list_feedbacks` が結果を返す場合。
   - 振る舞い: `reader.find_feedbacks` の返却結果を `created_at` の instant 降順（新しい順）でソートして返す。reader が返す順序には依存しない。同一 instant の場合は `id` の文字列表現昇順を tie-break とする。
3. 日付範囲フィルタ:
   - 条件: `date_from` または `date_to` が指定されている場合。
   - 振る舞い: `date_from` / `date_to` を検証し、instant 比較で `date_from <= date_to` を満たすことを確認してから `reader.find_feedbacks` に渡す。
4. 既読状態フィルタ:
   - 条件: `list_feedbacks` を呼ぶ場合。
   - 振る舞い: `read_status` を問い合わせ条件として `reader.find_feedbacks` にそのまま渡す。`all` は既読状態で絞り込まない要求、`unread` は未読のみを要求する値、`read` は既読のみを要求する値として扱う。
5. フィルタ委譲:
   - 条件: フィルタ条件がある場合。
   - 振る舞い: 日付範囲と既読状態の条件は `reader.find_feedbacks` にそのまま渡す。モジュール側では `created_at` 契約検証、結果ソート、件数算出以外の post-filter を行わない。reader が `read_status` と整合しない DTO を返した場合でも、その整合性補正は本モジュールの責務に含めない。
6. 件数の算出:
   - 条件: `list_feedbacks` が結果を返す場合。
   - 振る舞い: `total_count` は `len(items)` で算出する。全件数ではなくフィルタ後の件数。
7. 既読化の冪等性:
   - 条件: `mark_feedback_as_read` を呼ぶ場合。
   - 振る舞い: 対象が既に `is_read=True` の場合、`writer.get_by_id` の返却 DTO の `created_at` を検証したうえで `writer.update_read_status` を呼ばずにそのまま返す。`read_at` は変更しない。
8. now パラメータの利用:
   - 条件: 未読の feedback を既読化する場合。
   - 振る舞い: `now` を共通日時文字列契約で検証したうえで `read_at` に設定する。モジュール内で現在時刻を取得しない。
9. writer 返却 DTO の検証:
   - 条件: `mark_feedback_as_read` が `writer.get_by_id` または `writer.update_read_status` から `FeedbackListItem` を受け取る場合。
   - 振る舞い: `created_at` を共通日時文字列契約で検証してから返す。検証に失敗した場合は生 DTO を返さず `FeedbackListingStoreError` に分類する。
10. Protocol DI による外部依存分離:
   - 条件: 永続化操作を行う場合。
   - 振る舞い: 実装は concrete class に依存せず、`FeedbackListingReader` と `FeedbackReadWriter` の Protocol だけを参照する。
11. structlog による構造化ログ:
   - 条件: 一覧取得成功、既読化成功、フィードバック未検出、外部依存エラーのいずれかが発生した場合。
   - 振る舞い: `structlog` で構造化ログを出力する。イベント名は一覧取得成功時 `feedback_listing_queried`、既読化成功時 `feedback_listing_marked_read`、フィードバック未検出時 `feedback_listing_not_found`、永続化失敗時 `feedback_listing_store_failed` とする。イベント別の必須フィールドは次のとおり。
     - `feedback_listing_queried`: `total_count`、`date_from`、`date_to`、`read_status`
     - `feedback_listing_marked_read`: `feedback_id`
     - `feedback_listing_not_found`: `feedback_id`
     - `feedback_listing_store_failed`（一覧取得系）: `date_from`、`date_to`、`read_status`、`error_type`
     - `feedback_listing_store_failed`（既読化系）: `feedback_id`、`error_type`
   - `feedback_listing_store_failed` は port 例外だけでなく、reader / writer 返却 DTO の `created_at` 契約違反でも出力し得る。
12. 状態変更スコープ:
   - 条件: 既読状態に関する振る舞いを定義する場合。
   - 振る舞い: 本仕様が追加するのは一覧取得時の `read_status` フィルタ契約のみである。状態変更は `mark_feedback_as_read` に限り、既読解除は扱わない。

# 境界条件

- ケース: フィルタ結果が 0 件。
  - 振る舞い: `items=[]`、`total_count=0` を返す。エラーにはしない。
  - 理由: 0 件は正常な検索結果。
- ケース: `date_from` だけ指定、`date_to` は `None`。
  - 振る舞い: `created_at >= date_from` を instant 比較で満たすレコードを対象とする。上限なし。
  - 理由: 「この日以降」の検索ニーズに対応。
- ケース: `date_to` だけ指定、`date_from` は `None`。
  - 振る舞い: `created_at <= date_to` を instant 比較で満たすレコードを対象とする。下限なし。
  - 理由: 「この日まで」の検索ニーズに対応。
- ケース: `read_status=read`。
  - 振る舞い: `reader.find_feedbacks` に `read_status="read"` をそのまま渡す。モジュール側は返却後に `is_read=True` の追加選別を行わない。
  - 理由: requirements の「既読状態でフィルタ取得」は reader に委譲する契約であり、モジュール側の責務は `created_at` 検証・ソート・件数算出に限定するため。
- ケース: `date_from > date_to`。
  - 振る舞い: 文字列表現ではなく instant 比較後に `FeedbackListingInputError` を送出する。
  - 理由: 論理的に矛盾したフィルタ条件。
- ケース: `date_from="2026-05-20T00:00:00Z"`、`date_to="2026-05-20T23:59:59.1+09:00"`、`now="2026-05-21T09:00:00.12345+09:00"`、または `now="2026-05-21T09:00:00.123456+09:00"`。
  - 振る舞い: 受理する。
  - 理由: `Z` と 1-6 桁の小数秒は共通日時文字列契約の受理範囲。
- ケース: `date_from="2026-05-20 00:00:00+09:00"`。
  - 振る舞い: `FeedbackListingInputError` を送出する。
  - 理由: `T` 区切り必須であり、スペース区切りは受理しない。
- ケース: `date_to="2026-05-20T00:00:00"`。
  - 振る舞い: `FeedbackListingInputError` を送出する。
  - 理由: offset 必須であり、offset なし文字列は受理しない。
- ケース: 同一 instant の `created_at` を持つ複数レコードがある。
  - 振る舞い: `id` の文字列表現昇順で順序を確定する。
  - 理由: テストが一意に書けるようにするため。
- ケース: port が共通日時文字列契約に違反した `created_at` を返す。
  - 振る舞い: `FeedbackListingStoreError` を送出する。
  - 理由: 返却 DTO が port 契約に違反しており、モジュールはその DTO を公開できないため。
- ケース: `mark_feedback_as_read` で `writer.get_by_id` が共通日時文字列契約に違反した `created_at` を返す。
  - 振る舞い: `FeedbackListingStoreError` を送出する。既読判定に使える `is_read` が入っていても、その DTO は返さない。
  - 理由: idempotent return を含めて writer DTO も公開契約の対象であり、契約違反 DTO をそのまま返せないため。
- ケース: `mark_feedback_as_read` で `writer.update_read_status` が共通日時文字列契約に違反した `created_at` を返す。
  - 振る舞い: `FeedbackListingStoreError` を送出する。
  - 理由: 更新成功後の返却 DTO も writer 契約違反として同一分類で扱うため。
- ケース: 存在しない `feedback_id` で `mark_feedback_as_read` を呼ぶ。
  - 振る舞い: `FeedbackListingNotFoundError` を送出する。
  - 理由: 存在しないリソースの更新は呼び出し元の不具合を示す。
- ケース: 既に `is_read=True` のフィードバックを `mark_feedback_as_read` する。
  - 振る舞い: エラーにせず、既存の `is_read=True` と `read_at` をそのまま返す。`writer.update_read_status` は呼ばない。
  - 理由: 既読ボタンの重複クリック等、冪等であることが UX 上望ましい。
- ルール間の相互作用:
  1. 入力バリデーションはフィルタ委譲より先に行う。`date_from` / `date_to` / `now` の形式不正や `date_from > date_to` は reader / writer を呼ぶ前にエラーにする。
  2. ソートはフィルタの後に行う。reader から返された結果をモジュール側で `created_at` の instant 降順にソートする。
  3. `created_at` のパース失敗は入力エラーではなく port 契約違反として扱い、reader / writer のどの返却 DTO でも `FeedbackListingStoreError` に分類する。
  4. `mark_feedback_as_read` では `writer.get_by_id` が `None` を返した場合のみ not found を判定し、DTO がある場合は `created_at` 検証後に冪等性チェック（既読確認）を行う。
  5. `mark_feedback_as_read` で未読レコードを更新した場合、`writer.update_read_status` の返却 DTO も返却前に `created_at` を検証する。

# 非機能・制約

- 性能:
  1 回の `list_feedbacks` 呼び出しにつき reader アクセスは 1 回。1 回の `mark_feedback_as_read` 呼び出しにつき writer アクセスは最大 2 回（取得 + 更新）、既読時は 1 回（取得のみ）。
- 可観測性:
  一覧取得の件数とフィルタ条件、既読化対象の `feedback_id`、永続化失敗時の `error_type` を構造化フィールドで追跡できること。`read_status` を必須で含めるのは `feedback_listing_queried` と一覧取得系の `feedback_listing_store_failed` に限る。`mark_feedback_as_read` 系ログでは `read_status` を要求しない。
- 外部依存:
  依存先は `Protocol` で表現した `FeedbackListingReader` と `FeedbackReadWriter` のみ。RDB 実装の詳細はこの機能の契約に含めない。

# モジュール構成

- 構成方針: 2 モジュールに分割する
- 概算メモ:
  DTO・Protocol・例外型を `feedback_listing_types.py` に分離し、`list_feedbacks` / `mark_feedback_as_read` のオーケストレーションと入力バリデーションを `feedback_listing.py` にまとめる。既存 `ingestion_feedback.py` / `ingestion_feedback_types.py` は生成系の責務に限定し、一覧・既読化は新規モジュールへ切り出す。合計約 200 行で、1 ファイルあたり 130 行以内に収まる。
- モジュール一覧:
  - `backend/ingestion/infrastructure/feedback_listing_types.py`
    - 責務: DTO、Protocol、例外型の定義
    - 含める要素: `FeedbackListingQuery`、`FeedbackListingResult`、`FeedbackListItem`、`FeedbackListingReader`、`FeedbackReadWriter`、`FeedbackListingInputError`、`FeedbackListingNotFoundError`、`FeedbackListingStoreError`
  - `backend/ingestion/infrastructure/feedback_listing.py`
    - 責務: 処理全体のオーケストレーション、入力バリデーション、ソート
    - 含める要素: `list_feedbacks`、`mark_feedback_as_read`、共通日時文字列契約のバリデーション、instant 比較、structlog 出力

# 技術判断

- 判断:
  一覧取得・既読化は `ingestion_feedback.py` を拡張せず、`feedback_listing.py` / `feedback_listing_types.py` に分離する。
  - 理由:
    生成系の LLM オーケストレーションと、read-side の filter / 既読化契約を同一モジュールへ混在させると責務境界とテスト対象が曖昧になるため。
- 判断:
  ソートはモジュール側で実施し、reader の返却順序には依存しない。
  - 理由:
    reader の実装（SQL の ORDER BY）に依存しないことで、テストで順序を検証でき、reader のインターフェース契約がシンプルになる。
- 判断:
  `created_at` の順序は文字列の辞書順ではなく、パース後の instant で比較する。
  - 理由:
    異なる offset を持つ日時文字列でも実時刻順を一意に決めるため。
- 判断:
  既読化の時刻は `now: str` パラメータで外部注入する。
  - 理由:
    `ingestion-feedback` の `generated_at` と同じパターン。テスタビリティを確保しつつ、Clock Protocol のような追加抽象を避ける。
- 判断:
  タグによるトピックフィルタは実装しない。
  - 理由:
    チャンクのタグは ChromaDB に保存されており、SQLite の IngestionFeedback テーブルとの cross-store join が必要。個人用ツールのデータ量では `source_path` で十分にフィルタできるため、複雑性に見合わない。
- 判断:
  ページネーションは実装しない。
  - 理由:
    個人用ツールでデータ量が小規模のため不要。

# スコープ外

- 対応しないこと: タグによるトピックフィルタ（cross-store join が必要）
- 対応しないこと: ページネーション
- 対応しないこと: フィードバックの削除・編集
- 対応しないこと: 既読解除
- 対応しないこと: HTTP エンドポイントの実装（presentation 層で別途実装）

# 受け入れ基準

- [ ] フィルタなしで全フィードバックが `created_at` の instant 降順で取得できる
- [ ] `read_status=unread` で未読のみフィルタできる
- [ ] `read_status=read` で既読のみフィルタできる
- [ ] `read_status=all` で既読状態による絞り込みをしない
- [ ] 日付範囲（`date_from` / `date_to`）で instant 比較によるフィルタができる
- [ ] `Z` 付き日時と 1-6 桁の小数秒付き日時を受理できる
- [ ] スペース区切り日時と offset なし日時を拒否できる
- [ ] `date_from > date_to` を instant 比較後にエラーとして扱える
- [ ] 同一 instant の `created_at` を持つ場合でも tie-break により順序が一意に決まる
- [ ] フィルタ結果 0 件で空リスト・`total_count=0` が返る
- [ ] フィードバックを既読化すると `is_read=True` と `read_at` が設定される
- [ ] 既に既読のフィードバックを再度既読化してもエラーにならず、`read_at` が変更されない
- [ ] 存在しない `feedback_id` で既読化するとエラーが発生する
- [ ] port が不正な `created_at` を返した場合はエラーが発生する
- [ ] 各操作で構造化ログが出力される

# テスト観点メモ

- 正常系:
  - フィルタなしで全件取得し、`created_at` の instant 降順を確認
  - `read_status=unread` で未読のみ取得
  - `read_status=read` で既読のみ取得
  - `read_status=all` で既読・未読が混在した結果を取得
  - `date_from` のみ指定で日付以降のみ取得
  - `date_to` のみ指定で日付以前のみ取得
  - `date_from` + `date_to` で範囲内のみ取得
  - `read_status` + 日付範囲の複合フィルタ
  - `Z` 付き日時を受理
  - 小数秒付き日時を受理
  - 未読フィードバックの既読化成功
- 境界系:
  - フィルタ結果 0 件で空リスト
  - 既に既読のフィードバックの再既読化（冪等）
  - reader が返す順序がバラバラでもソート結果は正しい
  - 異なる offset だが同じ instant の `created_at` を tie-break で一意に並べる
- 異常系:
  - `date_from` がスペース区切りの日時
  - `date_from` が offset なし日時
  - `date_to` が不正な共通日時文字列契約違反
  - `date_from > date_to` が offset 正規化後に成立するケース
  - `now` が不正な共通日時文字列契約違反
  - `read_status` が `all` / `unread` / `read` 以外
  - port が不正な `created_at` を返す
  - 存在しない `feedback_id` で既読化
  - reader 操作失敗時のエラーハンドリング
  - writer 操作失敗時のエラーハンドリング
