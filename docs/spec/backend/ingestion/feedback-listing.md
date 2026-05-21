---
feature: ingestion/feedback-listing
status: draft
---

# 概要

- この機能が解決する課題:
  取り込み済み `IngestionFeedback` を日付範囲・既読状態でフィルタ取得し、個別に既読化できるようにする。presentation 層がこの機能を HTTP エンドポイントとして公開することで、フロントエンドからフィードバック一覧の閲覧・既読化が可能になる。
- 利用者・呼び出し元・前提条件:
  呼び出し元は presentation 層の API エンドポイントを想定する。フィードバックレコードは `ingestion-feedback` モジュールによって事前に永続化されている前提。本機能は `Protocol` による DI で注入された永続化ポートを利用する。構造化ログ出力には `structlog` を用いる。

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

- 入力:
  - `FeedbackListingQuery`
    一覧取得の公開入力 DTO。frozen dataclass。
    - `date_from: str | None`
      フィルタ開始日時。ISO 8601 文字列（offset 付き）。`None` の場合は下限なし。`created_at >= date_from` でフィルタする（inclusive）。
    - `date_to: str | None`
      フィルタ終了日時。ISO 8601 文字列（offset 付き）。`None` の場合は上限なし。`created_at <= date_to` でフィルタする（inclusive）。
    - `unread_only: bool`
      `True` の場合は `is_read=False` のレコードのみ返す。`False` の場合はフィルタしない。

  - `mark_feedback_as_read` の入力:
    - `feedback_id: UUID` — 対象フィードバックの ID。
    - `now: str` — 既読化日時を表す ISO 8601 文字列。`read_at` にそのまま使う。テスタビリティのために外部注入する。

- 依存インターフェース:
  - `FeedbackListingReader`
    `find_feedbacks(*, date_from: str | None, date_to: str | None, unread_only: bool) -> list[FeedbackListItem]` を提供する Protocol。
    - 戻り値の順序は不定。ソートはモジュール側で行う。
  - `FeedbackReadWriter`
    `get_by_id(feedback_id: UUID) -> FeedbackListItem | None` を提供する Protocol。
    `update_read_status(feedback_id: UUID, *, is_read: bool, read_at: str) -> FeedbackListItem` を提供する Protocol。
  - `structlog`
    構造化ログ出力。モジュールロガーを使い、各ログ呼び出しでコンテキスト情報を渡す。

- 出力:
  - `FeedbackListingResult`
    frozen dataclass。
    - `items: list[FeedbackListItem]`
      `created_at` 降順（新しい順）でソート済み。
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
  - `FeedbackListingInputError`: `date_from` または `date_to` が ISO 8601 として解析できない場合、正規化後に `date_from > date_to` となる場合、`now` が ISO 8601 として解析できない場合。
  - `FeedbackListingNotFoundError`: `mark_feedback_as_read` の対象 ID に対応するフィードバックが存在しない場合。
  - `FeedbackListingStoreError`: 永続化ポートの操作が失敗した場合。

# 具体例

## 例1: フィルタなしで全件取得

- 入力:
  ```yaml
  query:
    date_from: null
    date_to: null
    unread_only: false
  reader.find_feedbacks の返却値（順序不定）:
    - id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
      source_path: "study/docker/compose.md"
      roadmap_item_id: null
      title: "study/docker/compose.md の取り込みフィードバック"
      body: "..."
      is_read: true
      created_at: "2026-05-17T10:00:00+09:00"
      read_at: "2026-05-19T12:00:00+09:00"
    - id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
      source_path: "study/typescript/generics.md"
      roadmap_item_id: "11111111-1111-1111-1111-111111111111"
      title: "study/typescript/generics.md の取り込みフィードバック"
      body: "..."
      is_read: false
      created_at: "2026-05-20T21:30:00+09:00"
      read_at: null
  ```
- 期待される出力:
  ```yaml
  items:
    - id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"  # 新しい方が先
      created_at: "2026-05-20T21:30:00+09:00"
      ...
    - id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
      created_at: "2026-05-17T10:00:00+09:00"
      ...
  total_count: 2
  ```

## 例2: 未確認のみフィルタ

- 入力:
  ```yaml
  query:
    date_from: null
    date_to: null
    unread_only: true
  reader.find_feedbacks の返却値:
    - id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
      is_read: false
      created_at: "2026-05-20T21:30:00+09:00"
  ```
- 期待される出力:
  ```yaml
  items:
    - id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
  total_count: 1
  ```

## 例3: 日付範囲フィルタ

- 入力:
  ```yaml
  query:
    date_from: "2026-05-20T00:00:00+09:00"
    date_to: "2026-05-20T23:59:59+09:00"
    unread_only: false
  reader.find_feedbacks の返却値:
    - id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
      created_at: "2026-05-20T21:30:00+09:00"
  ```
- 期待される出力:
  ```yaml
  items:
    - id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
  total_count: 1
  ```

## 例4: 未読フィードバックの既読化

- 入力:
  ```yaml
  feedback_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
  now: "2026-05-21T09:00:00+09:00"
  writer.get_by_id の返却値:
    id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    is_read: false
    read_at: null
  writer.update_read_status の返却値:
    id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    is_read: true
    read_at: "2026-05-21T09:00:00+09:00"
  ```
- 期待される出力:
  ```yaml
  id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
  is_read: true
  read_at: "2026-05-21T09:00:00+09:00"
  ```

## 例5: 既読フィードバックの再既読化（冪等）

- 入力:
  ```yaml
  feedback_id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
  now: "2026-05-21T10:00:00+09:00"
  writer.get_by_id の返却値:
    id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    is_read: true
    read_at: "2026-05-19T12:00:00+09:00"
  ```
- 期待される出力:
  ```yaml
  id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
  is_read: true
  read_at: "2026-05-19T12:00:00+09:00"
  ```
  `writer.update_read_status` は呼ばれない。

# 主要ルール

1. 降順ソート:
   - 条件: `list_feedbacks` が結果を返す場合。
   - 振る舞い: `reader.find_feedbacks` の返却結果を `created_at` の降順（新しい順）でソートして返す。reader が返す順序には依存しない。
2. 日付範囲フィルタ:
   - 条件: `date_from` または `date_to` が指定されている場合。
   - 振る舞い: `date_from` / `date_to` をそのまま `reader.find_feedbacks` に渡す。
3. 未確認フィルタ:
   - 条件: `unread_only=True` の場合。
   - 振る舞い: `unread_only` をそのまま `reader.find_feedbacks` に渡す。
4. フィルタ委譲:
   - 条件: フィルタ条件がある場合。
   - 振る舞い: 日付範囲と未確認フィルタの条件は `reader.find_feedbacks` にそのまま渡す。モジュール側では追加のフィルタリングを行わない。ソートのみモジュール側で実施する。
5. 件数の算出:
   - 条件: `list_feedbacks` が結果を返す場合。
   - 振る舞い: `total_count` は `len(items)` で算出する。全件数ではなくフィルタ後の件数。
6. 既読化の冪等性:
   - 条件: `mark_feedback_as_read` を呼ぶ場合。
   - 振る舞い: 対象が既に `is_read=True` の場合、`writer.update_read_status` を呼ばずにそのまま返す。`read_at` は変更しない。
7. now パラメータの利用:
   - 条件: 未読の feedback を既読化する場合。
   - 振る舞い: `read_at` に `now` の値をそのまま設定する。モジュール内で現在時刻を取得しない。
8. Protocol DI による外部依存分離:
   - 条件: 永続化操作を行う場合。
   - 振る舞い: 実装は concrete class に依存せず、`FeedbackListingReader` と `FeedbackReadWriter` の Protocol だけを参照する。
9. structlog による構造化ログ:
   - 条件: 一覧取得成功、既読化成功、外部依存エラーのいずれかが発生した場合。
   - 振る舞い: `structlog` で構造化ログを出力する。イベント名は一覧取得成功時 `feedback_listing_queried`、既読化成功時 `feedback_listing_marked_read`、フィードバック未検出時 `feedback_listing_not_found`、永続化失敗時 `feedback_listing_store_failed` とする。少なくとも `total_count`、`date_from`、`date_to`、`unread_only`、`feedback_id`、`error_type` を必要に応じて含める。

# 境界条件

- ケース: フィルタ結果が 0 件。
  - 振る舞い: `items=[]`、`total_count=0` を返す。エラーにはしない。
  - 理由: 0 件は正常な検索結果。
- ケース: `date_from` だけ指定、`date_to` は `None`。
  - 振る舞い: `created_at >= date_from` でフィルタ。上限なし。
  - 理由: 「この日以降」の検索ニーズに対応。
- ケース: `date_to` だけ指定、`date_from` は `None`。
  - 振る舞い: `created_at <= date_to` でフィルタ。下限なし。
  - 理由: 「この日まで」の検索ニーズに対応。
- ケース: `date_from > date_to`。
  - 振る舞い: `FeedbackListingInputError` を送出する。
  - 理由: 論理的に矛盾したフィルタ条件。
- ケース: 存在しない `feedback_id` で `mark_feedback_as_read` を呼ぶ。
  - 振る舞い: `FeedbackListingNotFoundError` を送出する。
  - 理由: 存在しないリソースの更新は呼び出し元の不具合を示す。
- ケース: 既に `is_read=True` のフィードバックを `mark_feedback_as_read` する。
  - 振る舞い: エラーにせず、既存の `is_read=True` と `read_at` をそのまま返す。`writer.update_read_status` は呼ばない。
  - 理由: 既読ボタンの重複クリック等、冪等であることが UX 上望ましい。
- ルール間の相互作用:
  1. 入力バリデーションはフィルタ委譲より先に行う。`date_from` / `date_to` / `now` の形式不正は reader/writer を呼ぶ前にエラーにする。
  2. ソートはフィルタの後に行う。reader から返された結果をモジュール側でソートする。
  3. `mark_feedback_as_read` では冪等性チェック（既読確認）を writer の更新呼び出しより先に行う。

# 非機能・制約

- 性能:
  1 回の `list_feedbacks` 呼び出しにつき reader アクセスは 1 回。1 回の `mark_feedback_as_read` 呼び出しにつき writer アクセスは最大 2 回（取得 + 更新）、既読時は 1 回（取得のみ）。
- 可観測性:
  一覧取得の件数、フィルタ条件、既読化の feedback_id を構造化フィールドで追跡できること。
- 外部依存:
  依存先は `Protocol` で表現した `FeedbackListingReader` と `FeedbackReadWriter` のみ。RDB 実装の詳細はこの機能の契約に含めない。

# モジュール構成

- 構成方針: 2 モジュールに分割する
- 概算メモ:
  DTO・Protocol・例外型を `feedback_listing_types.py` に分離し、`list_feedbacks` / `mark_feedback_as_read` のオーケストレーションと入力バリデーションを `feedback_listing.py` にまとめる。既存 `ingestion_feedback.py` / `ingestion_feedback_types.py` は生成系の責務に限定し、一覧・既読化は新規モジュールへ切り出す。合計約 200 行で、1 ファイルあたり 130 行以内に収まる。
- モジュール一覧:
  - `backend/core/ingestion/infrastructure/feedback_listing_types.py`
    - 責務: DTO、Protocol、例外型の定義
    - 含める要素: `FeedbackListingQuery`、`FeedbackListingResult`、`FeedbackListItem`、`FeedbackListingReader`、`FeedbackReadWriter`、`FeedbackListingInputError`、`FeedbackListingNotFoundError`、`FeedbackListingStoreError`
  - `backend/core/ingestion/infrastructure/feedback_listing.py`
    - 責務: 処理全体のオーケストレーション、入力バリデーション、ソート
    - 含める要素: `list_feedbacks`、`mark_feedback_as_read`、日付形式バリデーション、ソート、structlog 出力

# 技術判断

- 判断:
  一覧取得・既読化は `ingestion_feedback.py` を拡張せず、`feedback_listing.py` / `feedback_listing_types.py` に分離する。
  - 理由:
    生成系の LLM オーケストレーションと、read-side の filter/既読化契約を同一モジュールへ混在させると責務境界とテスト対象が曖昧になるため。
- 判断:
  ソートはモジュール側で実施し、reader の返却順序には依存しない。
  - 理由:
    reader の実装（SQL の ORDER BY）に依存しないことで、テストで順序を検証でき、reader のインターフェース契約がシンプルになる。
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

- [ ] フィルタなしで全フィードバックが `created_at` 降順で取得できる
- [ ] 日付範囲（`date_from` / `date_to`）でフィルタできる
- [ ] 未確認のみ（`unread_only=True`）でフィルタできる
- [ ] フィルタ結果 0 件で空リスト・`total_count=0` が返る
- [ ] フィードバックを既読化すると `is_read=True` と `read_at` が設定される
- [ ] 既に既読のフィードバックを再度既読化してもエラーにならず、`read_at` が変更されない
- [ ] 存在しない `feedback_id` で既読化するとエラーが発生する
- [ ] 不正な日付形式や `date_from > date_to` でエラーが発生する
- [ ] 各操作で構造化ログが出力される

# テスト観点メモ

- 正常系:
  - フィルタなしで全件取得、`created_at` 降順確認
  - `unread_only=True` で未読のみ取得
  - `date_from` のみ指定で日付以降のみ取得
  - `date_to` のみ指定で日付以前のみ取得
  - `date_from` + `date_to` で範囲内のみ取得
  - `unread_only` + 日付範囲の複合フィルタ
  - 未読フィードバックの既読化成功
- 境界系:
  - フィルタ結果 0 件で空リスト
  - 既に既読のフィードバックの再既読化（冪等）
  - reader が返す順序がバラバラでもソート結果は正しい
- 異常系:
  - `date_from` が不正な ISO 8601 形式
  - `date_to` が不正な ISO 8601 形式
  - `date_from > date_to`
  - `now` が不正な ISO 8601 形式
  - 存在しない `feedback_id` で既読化
  - reader 操作失敗時のエラーハンドリング
  - writer 操作失敗時のエラーハンドリング
