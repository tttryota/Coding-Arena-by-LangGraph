---
status: ready
---

# テストケース一覧

# 検証焦点

| テストの種類 | 検証焦点 |
|---|---|
| Phase 1（最小骨格） | `FeedbackListingResult` / `FeedbackListItem` 全フィールド、`total_count`、基本ソート、成功ログ |
| Phase 2（コアロジック） | `read_status` 委譲、日時 instant 比較、tie-break、片側境界、既読化冪等 |
| Phase 3（エッジケース） | 0 件、入力バリデーション、reader / writer の `created_at` 契約違反 |
| Phase 4（外部連携） | Protocol DI、未検出、port 障害の例外変換、失敗ログ、非呼び出し確認 |

## Phase 1: 最小骨格

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-01 | フィルタなしで全件を取得し、`created_at` の instant 降順ソート・`total_count`・成功ログを完全検証する | `FeedbackListingReader` Protocol を満たすテストダブルで `find_feedbacks(...)` の引数と呼び出し回数を検査できる。`structlog` 出力を収集できる | `list_feedbacks(query=FeedbackListingQuery(date_from=None, date_to=None, read_status="all"), reader=...)`。`reader.find_feedbacks(...)` は仕様書 例1 の 2 件を順不同で返す | 戻り値は仕様書 例1 の期待結果と完全一致する。`items` は `aaaaaaaa-...`、`bbbbbbbb-...` の順でちょうど 2 件、各 `FeedbackListItem` の全フィールドが reader 返却値と一致する。`total_count=2`。`reader.find_feedbacks(...)` は `date_from=None`、`date_to=None`、`read_status="all"` でちょうど 1 回だけ呼ばれる。`event="feedback_listing_queried"` のログがちょうど 1 件出力され、少なくとも `total_count=2`、`date_from=null`、`date_to=null`、`read_status="all"` を含む。追加キーは許容する | 仕様書 例1、受け入れ基準の最小正常系 |
| TC-02 | `read_status=unread` を reader へそのまま委譲し、未読 1 件の結果と成功ログを返す | `reader.find_feedbacks(...)` の引数、戻り値、ログを検査できる | `list_feedbacks(query=FeedbackListingQuery(date_from=None, date_to=None, read_status="unread"), reader=...)`。`reader.find_feedbacks(...)` は仕様書 例2 の 1 件を返す | 戻り値は仕様書 例2 の期待結果と完全一致する。`items` は未読 1 件だけを含み、`FeedbackListItem` の 8 フィールドすべてが仕様書 例2 の値と一致する。`total_count=1`。`reader.find_feedbacks(...)` は `date_from=None`、`date_to=None`、`read_status="unread"` でちょうど 1 回呼ばれる。`event="feedback_listing_queried"` のログがちょうど 1 件出力され、少なくとも `total_count=1`、`read_status="unread"` を含む。追加キーは許容する | `read_status=unread` の基本形 |
| TC-03 | 未読フィードバックを既読化し、`now` をそのまま `read_at` に使って更新結果と成功ログを返す | `FeedbackReadWriter` Protocol を満たすテストダブルで `get_by_id(...)` / `update_read_status(...)` の呼び出し回数と引数を検査できる。`structlog` 出力を収集できる | `mark_feedback_as_read(feedback_id=aaaaaaaa-..., now="2026-05-21T00:00:00Z", writer=...)`。`writer.get_by_id(...)` と `writer.update_read_status(...)` は仕様書 例6 の返却値を返す | 戻り値は仕様書 例6 の期待結果と完全一致する。返却された `FeedbackListItem` の 8 フィールドすべてが仕様書 例6 の更新後 DTO と一致する。`writer.get_by_id(...)` はちょうど 1 回、`writer.update_read_status(...)` は `feedback_id=aaaaaaaa-...`、`is_read=true`、`read_at="2026-05-21T00:00:00Z"` でちょうど 1 回呼ばれる。モジュール内で別の現在時刻を生成しない。`event="feedback_listing_marked_read"` のログがちょうど 1 件出力され、少なくとも `feedback_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"` を含む。追加キーは許容する | `now` の基本利用、`Z` 受理も兼ねる |

## Phase 2: コアロジック

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-10 | `read_status=read` を reader へそのまま委譲し、既読 1 件の結果を返す | `reader.find_feedbacks(...)` の引数と呼び出し回数を検査できる | `list_feedbacks(query=FeedbackListingQuery(date_from=None, date_to=None, read_status="read"), reader=...)`。`reader.find_feedbacks(...)` は仕様書 例3 の 1 件を返す | 戻り値は仕様書 例3 の期待結果と完全一致する。`items` は既読 1 件だけを含み、`FeedbackListItem` の 8 フィールドすべてが仕様書 例3 の値と一致する。`total_count=1`。`reader.find_feedbacks(...)` は `read_status="read"` でちょうど 1 回呼ばれる | `read_status=read` の基本形 |
| TC-11 | `date_from` / `date_to` を instant 比較で検証し、元文字列のまま reader へ渡し、結果を instant 降順で返す | `reader.find_feedbacks(...)` の受け取る引数文字列を検査できる | `list_feedbacks(query=FeedbackListingQuery(date_from="2026-05-19T15:00:00Z", date_to="2026-05-20T14:59:59.500000Z", read_status="all"), reader=...)`。`reader.find_feedbacks(...)` は仕様書 例4 の 2 件を返す | 戻り値は仕様書 例4 の期待結果と完全一致する。`items` は `aaaaaaaa-...`、`bbbbbbbb-...` の順で、各 `FeedbackListItem` の 8 フィールドすべてが仕様書 例4 の期待結果と一致する。`created_at` の比較は文字列比較ではなく instant 比較で行われる。`reader.find_feedbacks(...)` は `date_from="2026-05-19T15:00:00Z"`、`date_to="2026-05-20T14:59:59.500000Z"`、`read_status="all"` でちょうど 1 回呼ばれる。reader へ渡す日時文字列は `+00:00` 等へ強制書き換えされない | `Z` と 6 桁小数秒の受理、範囲指定の基本形 |
| TC-12 | 同一 instant の `created_at` は `id` 文字列表現昇順で tie-break し、順序を一意に確定する | `reader.find_feedbacks(...)` は順不同で返す | `list_feedbacks(query=FeedbackListingQuery(date_from=None, date_to=None, read_status="all"), reader=...)`。`reader.find_feedbacks(...)` は仕様書 例5 の 2 件を返す | 戻り値は仕様書 例5 の期待結果と完全一致する。`2026-05-20T03:00:00Z` と `2026-05-20T12:00:00+09:00` は同一 instant として扱われ、`items[0].id` は `aaaaaaaa-...`、`items[1].id` は `bbbbbbbb-...` になる。各 `FeedbackListItem` の 8 フィールドは並び替え以外 reader 返却値から変化しない。`total_count=2` | tie-break 専用確認 |
| TC-13 | 片側境界と `read_status` をそのまま委譲し、モジュール側で追加フィルタを行わず `created_at` 検証・ソート・件数算出だけを行う | `reader.find_feedbacks(...)` の引数と戻り値を検査できる | ケースA: `list_feedbacks(query=FeedbackListingQuery(date_from="2026-05-20T00:00:00Z", date_to=None, read_status="all"), reader=...)`。`reader.find_feedbacks(...)` は次の 3 件をこの順不同で返す: `[{id="cccccccc-cccc-cccc-cccc-cccccccccccc", source_path="study/sql/index.md", roadmap_item_id="33333333-3333-3333-3333-333333333333", title="study/sql/index.md の取り込みフィードバック", body="索引設計の見直しメモ", is_read=false, created_at="2026-05-20T18:00:00+09:00", read_at=null}, {id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", source_path="study/api/errors.md", roadmap_item_id=null, title="study/api/errors.md の取り込みフィードバック", body="エラー分類の追記候補", is_read=true, created_at="2026-05-20T00:00:00Z", read_at="2026-05-20T12:00:00+09:00"}, {id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", source_path="study/python/timezone.md", roadmap_item_id="22222222-2222-2222-2222-222222222222", title="study/python/timezone.md の取り込みフィードバック", body="UTC 変換の注意点", is_read=false, created_at="2026-05-20T08:30:00-04:00", read_at=null}]`。ケースB: `list_feedbacks(query=FeedbackListingQuery(date_from=None, date_to="2026-05-20T23:59:59+09:00", read_status="read"), reader=...)`。`reader.find_feedbacks(...)` は次の 2 件をこの順不同で返す: `[{id="eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee", source_path="study/frontend/state.md", roadmap_item_id="55555555-5555-5555-5555-555555555555", title="study/frontend/state.md の取り込みフィードバック", body="状態管理の比較メモ", is_read=false, created_at="2026-05-20T21:00:00+09:00", read_at=null}, {id="dddddddd-dddd-dddd-dddd-dddddddddddd", source_path="study/backend/cache.md", roadmap_item_id="44444444-4444-4444-4444-444444444444", title="study/backend/cache.md の取り込みフィードバック", body="キャッシュ失効条件の確認", is_read=true, created_at="2026-05-19T23:00:00Z", read_at="2026-05-20T08:00:00+09:00"}]` | ケースAでは `reader.find_feedbacks(...)` が `date_from="2026-05-20T00:00:00Z"`、`date_to=None`、`read_status="all"` でちょうど 1 回呼ばれる。戻り値は 3 件で、期待順序の ID 列は `["bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "cccccccc-cccc-cccc-cccc-cccccccccccc", "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"]` と完全一致する。各 `FeedbackListItem` の 8 フィールドは並び順以外 reader 返却値から変化せず、`total_count=3`。ケースBでは `reader.find_feedbacks(...)` が `date_from=None`、`date_to="2026-05-20T23:59:59+09:00"`、`read_status="read"` でちょうど 1 回呼ばれる。戻り値は 2 件で、期待順序の ID 列は `["eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee", "dddddddd-dddd-dddd-dddd-dddddddddddd"]` と完全一致する。各 `FeedbackListItem` の 8 フィールドは並び順以外 reader 返却値から変化せず、`total_count=2`。ケースB では `is_read=false` の `eeeeeeee-...` も reader 返却のまま含まれ、モジュール側で `read_status="read"` を理由とする post-filter は行われない | ケースA は `date_from` のみ委譲される片側境界、ケースB は `date_to` のみ委譲される片側境界と `read_status` の委譲のみで post-filter しないことの確認 |
| TC-14 | 既読フィードバックの再既読化は冪等で、`read_at` を変更せず更新呼び出しを抑止する | `writer.get_by_id(...)` / `writer.update_read_status(...)` の呼び出し有無とログを検査できる | `mark_feedback_as_read(feedback_id=bbbbbbbb-..., now="2026-05-21T10:00:00+09:00", writer=...)`。`writer.get_by_id(...)` は仕様書 例7 の既読レコードを返す | 戻り値は仕様書 例7 の期待結果と完全一致する。返却された `FeedbackListItem` の 8 フィールドすべてが仕様書 例7 の DTO と一致する。`writer.get_by_id(...)` はちょうど 1 回呼ばれる。`writer.update_read_status(...)` は 1 回も呼ばれない。返却された `read_at` は `"2026-05-19T12:00:00+09:00"` のままで変更されない。`event="feedback_listing_marked_read"` のログがちょうど 1 件出力され、少なくとも `feedback_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"` を含む。追加キーは許容する | 既読化の冪等性 |
| TC-15 | 共通日時文字列契約として 1-5 桁の小数秒付き日時を受理し、元文字列のまま reader / writer へ渡す | `reader.find_feedbacks(...)` と `writer.get_by_id(...)` / `writer.update_read_status(...)` の受け取る引数文字列を検査できる | ケースA: `list_feedbacks(query=FeedbackListingQuery(date_from="2026-05-20T00:00:00.1Z", date_to=None, read_status="all"), reader=...)`。ケースB: `list_feedbacks(query=FeedbackListingQuery(date_from="2026-05-20T00:00:00.12+09:00", date_to=None, read_status="all"), reader=...)`。ケースC: `list_feedbacks(query=FeedbackListingQuery(date_from=None, date_to="2026-05-20T23:59:59.123Z", read_status="all"), reader=...)`。ケースD: `list_feedbacks(query=FeedbackListingQuery(date_from=None, date_to="2026-05-20T23:59:59.1234-04:00", read_status="all"), reader=...)`。ケースE: `mark_feedback_as_read(feedback_id=aaaaaaaa-..., now="2026-05-21T09:00:00.12345+09:00", writer=...)`。ケースA-D の `reader.find_feedbacks(...)` はそれぞれ `[]` を返す。ケースE では `writer.get_by_id(...)` と `writer.update_read_status(...)` が仕様書 例6 の DTO を返し、`writer.update_read_status(...)` の `read_at` は `"2026-05-21T09:00:00.12345+09:00"` になる | ケースA-D はすべて正常終了し、戻り値 `{items: [], total_count: 0}` と完全一致する。各ケースで `reader.find_feedbacks(...)` は入力に書かれた小数秒付き日時文字列を 1 文字も変更せずに受け取り、ちょうど 1 回だけ呼ばれる。ケースE も正常終了し、`writer.update_read_status(...)` は `feedback_id=aaaaaaaa-...`、`is_read=true`、`read_at="2026-05-21T09:00:00.12345+09:00"` でちょうど 1 回呼ばれる。ケースA-E のいずれでも `.1`、`.12`、`.123`、`.1234`、`.12345` を理由に `FeedbackListingInputError` は送出されない | 1-5 桁小数秒の具体受理例を値ベースで固定する TC |

## Phase 3: エッジケース

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-20 | フィルタ結果が 0 件でも正常終了し、空リスト・`total_count=0`・成功ログを返す | `reader.find_feedbacks(...)` の戻り値とログを検査できる | `list_feedbacks(query=FeedbackListingQuery(date_from="2026-05-22T00:00:00+09:00", date_to=None, read_status="all"), reader=...)`。`reader.find_feedbacks(...)` は `[]` を返す | 戻り値は `{items: [], total_count: 0}` と完全一致する。`reader.find_feedbacks(...)` はちょうど 1 回呼ばれる。`event="feedback_listing_queried"` のログがちょうど 1 件出力され、少なくとも `total_count=0`、`date_from="2026-05-22T00:00:00+09:00"`、`date_to=null`、`read_status="all"` を含む。追加キーは許容する | 0 件は正常結果 |
| TC-21 | 一覧取得の入力契約違反は `FeedbackListingInputError` とし、reader 呼び出し前に失敗させる | `reader.find_feedbacks(...)` の呼び出し有無を検査できる | ケースA: `date_from="2026-05-20 00:00:00+09:00"`。ケースB: `date_to="2026-05-20T00:00:00"`。ケースC: `read_status="archived"`。ケースD: `date_from="2026-05-20T12:00:00+09:00"`, `date_to="2026-05-20T02:59:59Z"` | 各ケースで `FeedbackListingInputError` を送出する。検証対象は例外型のみで、message と cause chain は検証対象外とする。`reader.find_feedbacks(...)` は各ケースで 1 回も呼ばれない。`feedback_listing_queried` と `feedback_listing_store_failed` のログは出力されないことを確認する | スペース区切り、offset なし、無効 `read_status`、instant 比較での逆転 |
| TC-22 | `now` の入力契約違反は `FeedbackListingInputError` とし、writer 呼び出し前に失敗させる | `writer.get_by_id(...)` / `writer.update_read_status(...)` の呼び出し有無を検査できる | ケースA: `now="2026-05-21 09:00:00+09:00"`。ケースB: `now="2026-05-21T09:00:00"` | 各ケースで `FeedbackListingInputError` を送出する。`writer.get_by_id(...)` と `writer.update_read_status(...)` は各ケースで 1 回も呼ばれない。`feedback_listing_marked_read`、`feedback_listing_not_found`、`feedback_listing_store_failed` のログは出力されないことを確認する | `now` 専用入力バリデーション |
| TC-23 | reader が不正な `created_at` を返した場合、`FeedbackListingStoreError` と失敗ログを返し、ソート不能として扱う | `reader.find_feedbacks(...)` の戻り値とログを検査できる | `list_feedbacks(query=FeedbackListingQuery(date_from=None, date_to=None, read_status="all"), reader=...)`。`reader.find_feedbacks(...)` は `created_at="2026-05-20 12:34:56+09:00"` の 1 件を返す | `FeedbackListingStoreError` を送出する。検証対象は例外型とログ有無で、message と cause chain は検証対象外とする。`reader.find_feedbacks(...)` はちょうど 1 回呼ばれる。`event="feedback_listing_store_failed"` のログがちょうど 1 件出力され、少なくとも `date_from=null`、`date_to=null`、`read_status="all"`、`error_type` を含む。追加キーは許容する。`feedback_listing_queried` の成功ログは出力されない | reader の `created_at` 契約違反によるソート不能 |
| TC-24 | `writer.get_by_id(...)` が不正な `created_at` を返した場合、`FeedbackListingStoreError` と失敗ログを返し、更新前に停止する | `writer.get_by_id(...)` / `writer.update_read_status(...)` の戻り値とログを検査できる | `mark_feedback_as_read(feedback_id=aaaaaaaa-..., now="2026-05-21T00:00:00Z", writer=...)`。`writer.get_by_id(...)` は `is_read=false` かつ `created_at="2026-05-20 21:30:00+09:00"` の DTO を返す | `FeedbackListingStoreError` を送出する。検証対象は例外型とログ有無で、message と cause chain は検証対象外とする。`writer.get_by_id(...)` はちょうど 1 回呼ばれる。`writer.update_read_status(...)` は 1 回も呼ばれない。`event="feedback_listing_store_failed"` のログがちょうど 1 件出力され、少なくとも `feedback_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"`、`error_type` を含む。追加キーは許容する。`feedback_listing_marked_read` と `feedback_listing_not_found` のログは出力されない | `writer.get_by_id` の `created_at` 契約違反 |
| TC-25 | `writer.update_read_status(...)` が不正な `created_at` を返した場合、`FeedbackListingStoreError` と失敗ログを返す | `writer.get_by_id(...)` / `writer.update_read_status(...)` の戻り値とログを検査できる | `mark_feedback_as_read(feedback_id=aaaaaaaa-..., now="2026-05-21T00:00:00Z", writer=...)`。`writer.get_by_id(...)` は仕様準拠の未読 DTO を返し、`writer.update_read_status(...)` は `created_at="2026-05-20 21:30:00+09:00"` の DTO を返す | `FeedbackListingStoreError` を送出する。検証対象は例外型とログ有無で、message と cause chain は検証対象外とする。`writer.get_by_id(...)` はちょうど 1 回、`writer.update_read_status(...)` は `feedback_id=aaaaaaaa-...`、`is_read=true`、`read_at="2026-05-21T00:00:00Z"` でちょうど 1 回呼ばれる。`event="feedback_listing_store_failed"` のログがちょうど 1 件出力され、少なくとも `feedback_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"`、`error_type` を含む。追加キーは許容する。`feedback_listing_marked_read` の成功ログは出力されない | `writer.update_read_status` の `created_at` 契約違反 |

## Phase 4: 外部連携

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-30 | Protocol だけを満たす最小スタブで一覧取得・既読化を完結でき、concrete class に依存しない | `find_feedbacks(...)` だけを持つ reader スタブと、`get_by_id(...)` / `update_read_status(...)` だけを持つ writer スタブを注入する。Protocol 外の属性参照があれば失敗するようにする | ケースA: 正常な `list_feedbacks(...)` 1 件。ケースB: 正常な `mark_feedback_as_read(...)` 1 件 | 両ケースとも正常終了する。依存オブジェクトに対するアクセスは Protocol で定義されたメソッド呼び出しだけで完了し、追加属性や concrete class 固有 API への参照は発生しない | Protocol DI の確認 |
| TC-31 | 存在しない `feedback_id` で既読化すると `FeedbackListingNotFoundError` を送出し、更新せず、`feedback_listing_not_found` ログを出す | `writer.get_by_id(...)` / `writer.update_read_status(...)` とログを検査できる | `mark_feedback_as_read(feedback_id=cccccccc-..., now="2026-05-21T00:00:00Z", writer=...)`。`writer.get_by_id(...)` は `None` を返す | `FeedbackListingNotFoundError` を送出する。検証対象は例外型とログ有無で、message と cause chain は検証対象外とする。`writer.get_by_id(...)` はちょうど 1 回呼ばれる。`writer.update_read_status(...)` は 1 回も呼ばれない。`event="feedback_listing_not_found"` のログがちょうど 1 件出力され、少なくとも `feedback_id="cccccccc-cccc-cccc-cccc-cccccccccccc"` を含む。追加キーは許容する | not found も正式なログ契約に含まれる分岐 |
| TC-32 | reader 操作失敗時は `FeedbackListingStoreError` に変換し、失敗ログを残す | `reader.find_feedbacks(...)` が `TimeoutError("reader timeout")` を送出し、ログを検査できる | `list_feedbacks(query=FeedbackListingQuery(date_from=None, date_to=None, read_status="all"), reader=...)` | `FeedbackListingStoreError` を送出する。検証対象は例外型とログ有無で、message と cause chain は検証対象外とする。`event="feedback_listing_store_failed"` のログがちょうど 1 件出力され、少なくとも `date_from=null`、`date_to=null`、`read_status="all"`、`error_type="TimeoutError"` を含む。追加キーは許容する。`feedback_listing_queried` の成功ログは出力されない | reader 障害のラップ |
| TC-33 | writer 操作失敗時は `FeedbackListingStoreError` に変換し、失敗ログを残す | ケースA: `writer.get_by_id(...)` が `ConnectionError("writer unavailable")` を送出する。ケースB: `writer.get_by_id(...)` は未読 1 件を返し、`writer.update_read_status(...)` が `RuntimeError("update failed")` を送出する。ログを検査できる | `mark_feedback_as_read(feedback_id=aaaaaaaa-..., now="2026-05-21T09:00:00.123456+09:00", writer=...)` | 各ケースで `FeedbackListingStoreError` を送出する。検証対象は例外型とログ有無で、message と cause chain は検証対象外とする。ケースAでは `writer.update_read_status(...)` は呼ばれない。ケースBでは `writer.update_read_status(...)` がちょうど 1 回呼ばれる。各ケースで `event="feedback_listing_store_failed"` のログがちょうど 1 件出力され、少なくとも `feedback_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"`、`error_type` を含む。追加キーは許容する。`feedback_listing_marked_read` の成功ログは出力されない | writer 障害のラップ、`now` の 6 桁小数秒受理も兼ねる |

# 網羅性チェック

仕様書の受け入れ基準の各項目に対応するテストケース ID を記載する。
全項目が少なくとも1つのテストケースでカバーされていることを確認する。

| 受け入れ基準 | 対応テストケース |
|---|---|
| フィルタなしで全フィードバックが `created_at` の instant 降順で取得できる | TC-01 |
| `read_status=unread` で未読のみフィルタできる | TC-02 |
| `read_status=read` で既読のみフィルタできる | TC-10 |
| `read_status=all` で既読状態による絞り込みをしない | TC-01, TC-13 |
| 日付範囲（`date_from` / `date_to`）で instant 比較によるフィルタができる | TC-11 |
| `Z` 付き日時と 1-6 桁の小数秒付き日時を受理できる | TC-03, TC-11, TC-15, TC-33 |
| スペース区切り日時と offset なし日時を拒否できる | TC-21, TC-22 |
| `date_from > date_to` を instant 比較後にエラーとして扱える | TC-21 |
| 同一 instant の `created_at` を持つ場合でも tie-break により順序が一意に決まる | TC-12 |
| フィルタ結果 0 件で空リスト・`total_count=0` が返る | TC-20 |
| フィードバックを既読化すると `is_read=True` と `read_at` が設定される | TC-03 |
| 既に既読のフィードバックを再度既読化してもエラーにならず、`read_at` が変更されない | TC-14 |
| 存在しない `feedback_id` で既読化するとエラーが発生する | TC-31 |
| port が不正な `created_at` を返した場合はエラーが発生する | TC-23（reader）, TC-24（writer.get_by_id）, TC-25（writer.update_read_status） |
| 各操作で構造化ログが出力される | TC-01, TC-02, TC-03, TC-14, TC-20, TC-23, TC-24, TC-25, TC-31, TC-32, TC-33 |

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
