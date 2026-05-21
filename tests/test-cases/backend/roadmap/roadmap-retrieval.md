---
status: ready
---

# テストケース一覧

# 検証焦点

| テストの種類 | 検証焦点 |
|---|---|
| Phase 1（最小骨格） | `RoadmapTree` 全フィールド、非集約フィールド原値保持、detail の `score` / `last_quiz_at`、取得成功ログ |
| Phase 2（コアロジック） | 順不同入力からのツリー再構築、兄弟 `order` ソート、段階的スコア集約、一覧順保持、一覧成功ログ |
| Phase 3（エッジケース） | 0 件、子 0 件、全スコア 0、仕様外データを期待結果対象に含めないこと |
| Phase 4（外部連携） | `RoadmapRetrievalNotFoundError` / `RoadmapRetrievalStoreError`、失敗ログ、reader 呼び出し回数 |

## Phase 1: 最小骨格

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-01 | 最小 3 階層で `get_roadmap` が `RoadmapTree` の全フィールドを組み立て、非集約フィールドを reader 返却値のまま保持し、成功ログを出す | `RoadmapRetrievalReader` Protocol を満たすテストダブルで `find_roadmap(...)` の引数と呼び出し回数を検査できる。reader が返すデータは契約を満たす整合済みデータ。`structlog` 出力を収集できる | `get_roadmap(roadmap_id=aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa, reader=...)`。`reader.find_roadmap(...)` は `roadmap_id=aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa`、`topic="  TypeScript 入門  "`、items として次の flat records を返す: `major(id=11111111-1111-1111-1111-111111111111, parent_id=None, level="major", title=" 基礎 ", description=" 導入 ", order=0, score=999, last_quiz_at="2026-05-01T00:00:00+09:00")`、`middle(id=22222222-2222-2222-2222-222222222222, parent_id=11111111-1111-1111-1111-111111111111, level="middle", title=" 型 ", description=" 基本 ", order=0, score=123, last_quiz_at="2026-05-02T00:00:00+09:00")`、`detail(id=33333333-3333-3333-3333-333333333333, parent_id=22222222-2222-2222-2222-222222222222, level="detail", title=" string ", description=" 文字列 ", order=0, score=88, last_quiz_at="2026-05-03T09:30:00+09:00")` の 3 件 | 戻り値は `roadmap_id=aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa` と `topic="  TypeScript 入門  "` を reader 返却値と完全一致で保持し、`overall_score=88`、`items` は major 1 件だけを含む。major ノードは `id=11111111-1111-1111-1111-111111111111`、`title=" 基礎 "`、`description=" 導入 "`、`level="major"`、`order=0` を原値のまま保持し、`score=88`、`last_quiz_at=None`、children に middle 1 件だけを含む。middle ノードは `id=22222222-2222-2222-2222-222222222222`、`title=" 型 "`、`description=" 基本 "`、`level="middle"`、`order=0` を原値のまま保持し、`score=88`、`last_quiz_at=None`、children に detail 1 件だけを含む。detail ノードは `id=33333333-3333-3333-3333-333333333333`、`title=" string "`、`description=" 文字列 "`、`level="detail"`、`order=0`、`score=88`、`last_quiz_at="2026-05-03T09:30:00+09:00"` を原値のまま保持し、`children=[]`。major / middle の DB 上 `score` と `last_quiz_at` は出力へ引き継がれない。`reader.find_roadmap(...)` は指定 `roadmap_id` でちょうど 1 回だけ呼ばれる。`info` レベルの `event="roadmap_retrieved"` ログが少なくとも 1 件出力され、少なくとも `roadmap_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"`、`topic="  TypeScript 入門  "`、`overall_score=88`、`item_count=3` を含む。追加キーは許容する | 全フィールド検証の最小正常系 |

## Phase 2: コアロジック

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-10 | 順不同の flat records から複数 major / middle / detail のツリーを再構築し、各兄弟集合を `order` 昇順で返し、major / middle の DB `score` を使わずに段階的集約する | `RoadmapRetrievalReader` Protocol を満たすテストダブルで `find_roadmap(...)` の呼び出し回数を検査できる。reader が返す 9 項目は仕様書 例1 と同じ親子関係・`order` を持つが、返却順はランダムで、major / middle の DB 上 `score` には 0 以外の任意値を入れておく | `get_roadmap(roadmap_id=aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa, reader=...)` | 戻り値は仕様書 例1 の期待結果と完全一致する。`RoadmapTree.items` は major `order` 0, 1 の順、各 major 配下の middle は `order` 昇順、各 middle 配下の detail は `order` 昇順で並ぶ。middle `"変数と型"` は `75`、middle `"関数"` は `40`、major `"基礎"` は `57`、major `"応用"` は `30`、`overall_score=43` となる。major / middle の入力 `score` 値は出力に影響しない。detail の `score` と `last_quiz_at` は DB 値そのまま、major / middle の `last_quiz_at` はすべて `None`。`reader.find_roadmap(...)` はちょうど 1 回だけ呼ばれる | 仕様書 例1、ツリー再構築とソートの主ケース |
| TC-11 | スコア平均の端数を各レベルで切り捨てる | reader が返すデータは契約を満たす整合済みデータ | `get_roadmap(roadmap_id=cccccccc-cccc-cccc-cccc-cccccccccccc, reader=...)`。`reader.find_roadmap(...)` は仕様書 例3 のレコードを返す | 戻り値は仕様書 例3 の期待結果と完全一致する。detail `[80, 70, 50]` から middle `"データ構造"` の `score=66`、major `"基礎"` の `score=66`、`overall_score=66` となり、小数点以下は各レベルで切り捨てられる。middle 1 件、major 1 件のため上位レベルでは切り捨て済み整数 `66` がそのまま使われる | 段階的切り捨ての明示検証 |
| TC-12 | `list_roadmaps` が reader 返却順を保持しつつ各ロードマップに `overall_score` を付与し、成功ログを出す | `RoadmapRetrievalReader` Protocol を満たすテストダブルで `find_all_roadmaps()` の呼び出し回数を検査できる。`structlog` 出力を収集できる。reader が返すデータは契約を満たす整合済みデータ | `list_roadmaps(reader=...)`。`reader.find_all_roadmaps()` は 2 件を `[Rust(items=[]), TypeScript(仕様書 例1 と同じ 9 項目)]` の順で返す | 戻り値の `items` は reader 返却順と完全一致で Rust, TypeScript の順にちょうど 2 件を含む。Rust の `roadmap_id` / `topic` は原値のまま、`overall_score=0`。TypeScript の `roadmap_id` / `topic` は原値のまま、`overall_score=43`。`total_count=2`。モジュール側で並べ替えをしない。`reader.find_all_roadmaps()` はちょうど 1 回だけ呼ばれる。`info` レベルの `event="roadmap_list_retrieved"` ログが少なくとも 1 件出力され、少なくとも `total_count=2` を含む。追加キーは許容する | 一覧の順序保持とスコア算出 |

## Phase 3: エッジケース

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-20 | 項目 0 件のロードマップを正常に返す | reader が返すデータは契約を満たす整合済みデータ | `get_roadmap(roadmap_id=bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb, reader=...)`。`reader.find_roadmap(...)` は仕様書 例2 のレコードを返す | 戻り値は仕様書 例2 の期待結果と完全一致する。`roadmap_id` / `topic` は原値のまま、`overall_score=0`、`items=[]`。空ロードマップでも非エラーで返る | 仕様書 例2 |
| TC-21 | middle に detail が 0 件のとき middle の `score=0` となり、その 0 が major / overall 集約に使われる | reader が返すデータは契約を満たす整合済みデータ | `get_roadmap(roadmap_id=21212121-2121-2121-2121-212121212121, reader=...)`。`reader.find_roadmap(...)` は `roadmap_id=21212121-2121-2121-2121-212121212121`、`topic="Edge Case A"`、items として次の flat records を返す: `major(id=21111111-1111-1111-1111-111111111111, parent_id=None, level="major", order=0, score=999, last_quiz_at="2026-05-01T00:00:00+09:00")`、`middle-A(id=21111111-1111-1111-1111-111111111112, parent_id=21111111-1111-1111-1111-111111111111, level="middle", order=0, score=123, last_quiz_at="2026-05-02T00:00:00+09:00")`、`middle-B(id=21111111-1111-1111-1111-111111111113, parent_id=21111111-1111-1111-1111-111111111111, level="middle", order=1, score=456, last_quiz_at="2026-05-03T00:00:00+09:00")`、`detail-B1(id=21111111-1111-1111-1111-111111111114, parent_id=21111111-1111-1111-1111-111111111113, level="detail", order=0, score=100, last_quiz_at="2026-05-04T09:00:00+09:00")`、`detail-B2(id=21111111-1111-1111-1111-111111111115, parent_id=21111111-1111-1111-1111-111111111113, level="detail", order=1, score=50, last_quiz_at="2026-05-05T09:00:00+09:00")` | 戻り値で `middle-A.score=0`、`middle-A.children=[]`、`middle-B.score=floor((100 + 50) / 2)=75`、major の `score=floor((0 + 75) / 2)=37`、`overall_score=37` となる。major 配下の middle は `order` 0, 1 の順で返る。major / middle の `last_quiz_at` は `None` のままで、detail の `last_quiz_at` は input の原値を保持する | 子 0 件 middle の境界 |
| TC-22 | major に middle が 0 件のとき major の `score=0` となり、その 0 が overall 集約に使われる | reader が返すデータは契約を満たす整合済みデータ | `get_roadmap(roadmap_id=22222222-2222-2222-2222-222222222222, reader=...)`。`reader.find_roadmap(...)` は `roadmap_id=22222222-2222-2222-2222-222222222222`、`topic="Edge Case B"`、items として次の flat records を返す: `major-A(id=22111111-1111-1111-1111-111111111111, parent_id=None, level="major", order=0, score=999, last_quiz_at="2026-05-01T00:00:00+09:00")`、`major-B(id=22111111-1111-1111-1111-111111111112, parent_id=None, level="major", order=1, score=888, last_quiz_at="2026-05-02T00:00:00+09:00")`、`middle-B1(id=22111111-1111-1111-1111-111111111113, parent_id=22111111-1111-1111-1111-111111111112, level="middle", order=0, score=777, last_quiz_at="2026-05-03T00:00:00+09:00")`、`detail-B1(id=22111111-1111-1111-1111-111111111114, parent_id=22111111-1111-1111-1111-111111111113, level="detail", order=0, score=80, last_quiz_at="2026-05-04T09:00:00+09:00")` | 戻り値で `major-A.score=0`、`major-A.children=[]`、`major-B.score=80`、`overall_score=floor((0 + 80) / 2)=40` となる。`RoadmapTree.items` は major-A(`order=0`), major-B(`order=1`) の順で返る | 子 0 件 major の境界 |
| TC-23 | 全 detail の `score=0` のとき middle / major / overall がすべて 0 になる | reader が返すデータは契約を満たす整合済みデータ | `get_roadmap(roadmap_id=23232323-2323-2323-2323-232323232323, reader=...)`。`reader.find_roadmap(...)` は `roadmap_id=23232323-2323-2323-2323-232323232323`、`topic="Edge Case C"`、items として次の flat records を返す: `major(id=23111111-1111-1111-1111-111111111111, parent_id=None, level="major", order=0, score=999, last_quiz_at="2026-05-01T00:00:00+09:00")`、`middle-A(id=23111111-1111-1111-1111-111111111112, parent_id=23111111-1111-1111-1111-111111111111, level="middle", order=0, score=888, last_quiz_at="2026-05-02T00:00:00+09:00")`、`middle-B(id=23111111-1111-1111-1111-111111111113, parent_id=23111111-1111-1111-1111-111111111111, level="middle", order=1, score=777, last_quiz_at="2026-05-03T00:00:00+09:00")`、`detail-A1(id=23111111-1111-1111-1111-111111111114, parent_id=23111111-1111-1111-1111-111111111112, level="detail", order=0, score=0, last_quiz_at="2026-05-04T09:00:00+09:00")`、`detail-A2(id=23111111-1111-1111-1111-111111111115, parent_id=23111111-1111-1111-1111-111111111112, level="detail", order=1, score=0, last_quiz_at="2026-05-05T09:00:00+09:00")`、`detail-B1(id=23111111-1111-1111-1111-111111111116, parent_id=23111111-1111-1111-1111-111111111113, level="detail", order=0, score=0, last_quiz_at="2026-05-06T09:00:00+09:00")` | 戻り値で全 detail の `score=0` を保持し、`middle-A.score=0`、`middle-B.score=0`、major の `score=0`、`overall_score=0` となる。0 の平均でも非エラーで返る | 未着手一括ケース |
| TC-24 | ロードマップ 0 件で一覧取得できる | `RoadmapRetrievalReader` Protocol を満たすテストダブルとログ収集を用意する | `list_roadmaps(reader=...)`。`reader.find_all_roadmaps()` は空リストを返す | 戻り値は `items=[]`、`total_count=0` と完全一致する。`reader.find_all_roadmaps()` はちょうど 1 回だけ呼ばれる。`info` レベルの `event="roadmap_list_retrieved"` ログが少なくとも 1 件出力され、少なくとも `total_count=0` を含む。追加キーは許容する | 一覧 0 件の正常境界 |
| TC-25 | reader 契約違反データは本仕様の期待結果対象に含めない | テストケース文書レビューとして確認する | 欠落親、重複 `id`、`major -> middle -> detail` 以外の level 組み合わせ、同一兄弟集合での `order` 重複を含む reader 返却データ | 本テストケース文書では当該入力に対する runtime テストケースを新設しないことを確認する。該当入力に期待結果を置く場合は本仕様の外側なので `[要仕様追記]` 扱いとする | 仕様書のスコープ外固定 |

## Phase 4: 外部連携

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-30 | 存在しない `roadmap_id` では `RoadmapRetrievalNotFoundError` を送出し、warning ログを出す | `RoadmapRetrievalReader` Protocol を満たすテストダブルとログ収集を用意する | `get_roadmap(roadmap_id=dddddddd-dddd-dddd-dddd-dddddddddddd, reader=...)`。`reader.find_roadmap(...)` は `None` を返す | `RoadmapRetrievalNotFoundError` を送出する。検証対象は例外型とログ有無で、message と cause chain は検証対象外とする。`reader.find_roadmap(...)` は指定 `roadmap_id` でちょうど 1 回だけ呼ばれる。`warning` レベルの `event="roadmap_not_found"` ログが少なくとも 1 件出力され、少なくとも `roadmap_id="dddddddd-dddd-dddd-dddd-dddddddddddd"` を含む。追加キーは許容する | not found 分岐 |
| TC-31 | `get_roadmap` で reader が例外を送出したとき `RoadmapRetrievalStoreError` に変換し、error ログへ `roadmap_id` と単純クラス名の `error_type` を出す | `RoadmapRetrievalReader` Protocol を満たすテストダブルとログ収集を用意する。`reader.find_roadmap(...)` は `TimeoutError("reader timeout")` を送出する | `get_roadmap(roadmap_id=eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee, reader=...)` | `RoadmapRetrievalStoreError` を送出する。検証対象は例外型とログ有無で、message と cause chain は検証対象外とする。`reader.find_roadmap(...)` はちょうど 1 回だけ呼ばれる。`error` レベルの `event="roadmap_retrieval_store_failed"` ログが少なくとも 1 件出力され、少なくとも `roadmap_id="eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"`、`error_type="TimeoutError"` を含む。`error_type` は文字列の単純クラス名だけを検証し、例外オブジェクト・`repr(exc)`・完全修飾名ではないことを確認する。追加キーは許容する | get 系の reader 障害 |
| TC-32 | `list_roadmaps` で reader が例外を送出したとき `RoadmapRetrievalStoreError` に変換し、error ログへ単純クラス名の `error_type` を出す | `RoadmapRetrievalReader` Protocol を満たすテストダブルとログ収集を用意する。`reader.find_all_roadmaps()` は `ConnectionError("db unavailable")` を送出する | `list_roadmaps(reader=...)` | `RoadmapRetrievalStoreError` を送出する。検証対象は例外型とログ有無で、message と cause chain は検証対象外とする。`reader.find_all_roadmaps()` はちょうど 1 回だけ呼ばれる。`error` レベルの `event="roadmap_retrieval_store_failed"` ログが少なくとも 1 件出力され、少なくとも `error_type="ConnectionError"` を含む。`get_roadmap` 以外の失敗なので `roadmap_id` キーは必須検証対象に含めない。追加キーは許容する | list 系の reader 障害 |

# 網羅性チェック

仕様書の受け入れ基準の各項目に対応するテストケース ID を記載する。
全項目が少なくとも1つのテストケースでカバーされていることを確認する。

| 受け入れ基準 | 対応テストケース |
|---|---|
| 受け入れ基準の正常系は reader 契約を満たす整合済みの flat `RoadmapItemRecord` 一覧のみを対象とする | TC-01, TC-10, TC-11, TC-12, TC-20, TC-21, TC-22, TC-23, TC-24 |
| roadmap_id でロードマップがツリー構造で返る | TC-01, TC-10 |
| `RoadmapTree.items` と各 `children` が、root major 集合および各兄弟集合で `order` 一意前提の `order` 昇順で返る | TC-10, TC-21, TC-22 |
| `roadmap_id`、`topic`、`id`、`title`、`description`、`order` は reader 返却値をそのまま保持し、trim・空白正規化・Unicode 正規化・大小文字変換・補完・再採番を行わない | TC-01 |
| detail 項目の score が DB 値のまま返る | TC-01, TC-10, TC-23 |
| middle のスコアが配下 detail の平均（切り捨て）で算出される | TC-10, TC-11, TC-21 |
| major のスコアが配下 middle のスコアの平均（切り捨て）で算出される | TC-10, TC-11, TC-21, TC-22 |
| overall_score が全 major のスコアの平均（切り捨て）で算出される | TC-01, TC-10, TC-11, TC-12, TC-20, TC-22, TC-23 |
| detail のみ last_quiz_at が設定され、major・middle は null | TC-01, TC-10, TC-21 |
| 項目 0 件のロードマップで overall_score=0、items=[] が返る | TC-20 |
| 存在しない roadmap_id で RoadmapRetrievalNotFoundError が発生する | TC-30 |
| ロードマップ一覧が取得でき、各ロードマップに overall_score が含まれる | TC-12 |
| ロードマップ 0 件で空リスト・total_count=0 が返る | TC-24 |
| 各操作で本仕様の structlog 契約どおりに、イベント名・log level・必須フィールドが出力され、`roadmap_retrieval_store_failed.error_type` は `exc.__class__.__name__` の文字列になる | TC-01, TC-12, TC-24, TC-30, TC-31, TC-32 |
| reader 失敗時に RoadmapRetrievalStoreError が発生する | TC-31, TC-32 |
| 欠落親・重複 `id`・不正 level 組み合わせ・`order` 重複を含む不正データ時の期待結果は本仕様では新設しない | TC-25 |

# 記述ルール

- 仕様書に明記された振る舞いだけを前提にする
- 仕様未記載の振る舞いを期待結果に置く場合は `[要仕様追記]` タグを付ける
- 入力例・テスト入力は flat な `RoadmapItemRecord` 一覧のみを用い、`children=[]` を含むツリー shorthand は使わない
- 正常系・境界系・異常系が重複なく網羅されていることを確認する
- 仕様書の受け入れ基準の各項目に対応するテストケースが最低1つあることを確認する
- 期待結果に「含まれる」「完全一致」「少なくとも1件」「ちょうど1件」などの検証粒度を明示する
- ログ検証を含む場合は、検証対象イベント名、必須キー、期待値、追加キー許容の有無を明示し、件数制約や排他制約は spec が明示的に固定した場合にのみ書く
- 例外検証を含む場合は、例外型、message、cause chain、ログ記録有無のうち何を確認するかを明示する
- テストが「存在確認」なのか「内容検証」なのかを期待結果で区別して書く
- テストケース文書に書いていない検証を impl レビューで追加要求しなくて済む粒度まで、期待結果を具体化する
