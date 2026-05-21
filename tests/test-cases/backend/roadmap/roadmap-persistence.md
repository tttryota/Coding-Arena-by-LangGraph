---
status: ready
---

# テストケース一覧

# 検証焦点

| テストの種類 | 検証焦点 |
|---|---|
| Phase 1（最小骨格） | `RoadmapSaveResult` 全フィールド、`FlatRoadmapItem` 全フィールド、`writer.save_items(...)` 引数完全一致 |
| Phase 2（コアロジック） | DFS pre-order、`order` 採番、`parent_id`、文字列保持、`description` 空文字、部分構築許容 |
| Phase 3（エッジケース） | 入力バリデーション、未サポート level 値、階層不整合、外部依存の非呼び出し |
| Phase 4（外部連携） | Protocol 経由の呼び出し回数、成功ログ、例外ラップ、失敗ログ |

## Phase 1: 最小骨格

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-01 | 仕様書 例1 の 3 段階層を完全にフラット化し、保存引数と戻り値を全フィールドで検証する | `writer.save_items(...)` の引数、`id_generator.generate()` の呼び出し回数を検査できる Protocol 準拠テストダブルを使う | 仕様書 例1 の `RoadmapSaveInput` と `id_generator` の返却順をそのまま使う | 戻り値は仕様書 例1 の期待結果と完全一致する。`id_generator.generate()` はちょうど 10 回呼ばれる。1 回目は `roadmap_id`、2 回目以降は DFS pre-order の項目 ID として消費される。`writer.save_items(...)` はちょうど 1 回呼ばれ、`roadmap_id` は `aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa`、`topic` は `TypeScript`、`items` は仕様書 例1 の `FlatRoadmapItem` 一覧と順序・全フィールドまで完全一致する | 最小骨格の主正常系 |
| TC-02 | 空ロードマップでも `roadmap_id` を生成して空配列を保存できる | `writer` と `id_generator` の呼び出し回数を検査できる | 仕様書 例2 の入力と `id_generator` 返却値をそのまま使う | 戻り値は仕様書 例2 の期待結果と完全一致する。`id_generator.generate()` はちょうど 1 回だけ呼ばれる。`writer.save_items(...)` はちょうど 1 回呼ばれ、引数 `roadmap_id` は `bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb`、`topic` は `Rust`、`items` は空リストと完全一致する | 空入力の基準ケース |
| TC-03 | 最小有効構成 `major 1 -> middle 1 -> detail 1` を 3 レコードで保存できる | `writer.save_items(...)` の引数を検査できる | `topic="Go"`、`created_at="2026-05-21T11:00:00+09:00"`、`items=[major("基礎") -> middle("文法") -> detail("変数")]`。`id_generator` は `roadmap_id` 1 個と項目 ID 3 個を順に返す | 戻り値の `saved_count` は `3` で、`roadmap_id` は 1 回目の生成値と完全一致する。`writer.save_items(...)` に渡される `items` はちょうど 3 件で、major は `parent_id=None`、middle は major の ID、detail は middle の ID を持つ。各 `order` はすべて `0`、各 `score` はすべて `0`、各 `created_at` / `updated_at` は入力 `created_at` と完全一致する | 境界条件の最小有効構成 |

## Phase 2: コアロジック

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-10 | DFS pre-order の走査順と sibling ごとの `order` 採番を検証する | `writer.save_items(...)` に渡された順序と ID を検査できる | 2 つの major を持つ入力。1 つ目の major に middle を 2 件、1 件目 middle に detail を 2 件、2 件目 middle に detail を 1 件、2 つ目 major に middle を 1 件持たせ、その middle3 は `children=[]` とする。`id_generator` は判別しやすい連番 UUID を返す | `writer.save_items(...)` に渡される `items` の並びは level 別のまとめ順ではなく `major1 -> middle1 -> detail1 -> detail2 -> middle2 -> detail3 -> major2 -> middle3` の DFS pre-order と完全一致する。`major2` 配下の middle3 は `children=[]` のため、その後続レコードは存在しない。`order` はルート major 同士で `0,1`、major1 配下 middle で `0,1`、middle1 配下 detail で `0,1`、middle2 配下 detail で `0`、major2 配下 middle3 で `0` になる。各 `parent_id` は直近の親 ID と一致する | DFS と `order` の主検証 |
| TC-11 | `topic` / `title` は `strip()` ベースで妥当性判定しつつ、保存値は前後空白を保持する | `writer.save_items(...)` の引数文字列を厳密比較できる | `topic="  TypeScript 入門  "`、major `title="  基礎  "`、middle `title="  型  "`、detail `title="  string  "`、detail `description=""`、`created_at` は offset 付き正常値 | 正常終了する。`writer.save_items(...)` に渡される `topic` と各 `FlatRoadmapItem.title` は `strip()` された値ではなく入力文字列そのままと完全一致する。detail の `description` は空文字のまま保存される。`created_at` / `updated_at` は入力値そのままと完全一致する | `description` 空文字許容も同時に確認 |
| TC-12 | major の `children=[]` を正常入力として保存できる | `writer.save_items(...)` の件数と内容を検査できる | `topic="Rust"`、major 1 件のみ、`level="major"`、`children=[]`、`created_at` は offset 付き正常値 | 正常終了する。`writer.save_items(...)` はちょうど 1 回呼ばれ、`items` は major 1 件だけを含む。保存レコードの `parent_id` は `None`、`level` は `major`、`order` は `0`、`score` は `0` である | partial tree 許容契約の正常系 |
| TC-13 | middle の `children=[]` を正常入力として保存できる | `writer.save_items(...)` の件数と内容を検査できる | `topic="Rust"`、major 1 件の配下に middle 1 件、middle の `children=[]`、`created_at` は offset 付き正常値 | 正常終了する。`writer.save_items(...)` の `items` は major と middle の 2 件だけを含み、detail は生成されない。middle の `parent_id` は親 major の ID、major の `parent_id` は `None`、両レコードの `score` は `0`、`created_at` / `updated_at` は入力値と完全一致する | partial tree 許容契約の正常系 |

## Phase 3: エッジケース

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-20 | `topic` が空文字または空白のみなら `RoadmapPersistenceInputError` を送出する | `id_generator` と `writer` の呼び出し有無を検査できる | 同一の正常な `items` / `created_at` を使い、`topic=""` と `topic="   "` の 2 パターンで実施する | 各パターンで `RoadmapPersistenceInputError` を送出する。`id_generator.generate()` と `writer.save_items(...)` はいずれも 1 回も呼ばれない。例外 message は仕様未規定のため検証対象外とする | `strip()` ベース検証 |
| TC-21 | 任意 level の `title` が空文字または空白のみなら `RoadmapPersistenceInputError` を送出する | `id_generator` と `writer` の呼び出し有無を検査できる | 同一の正常な `major -> middle -> detail` 入力をベースに、`title=""` と `title="  "` を各 level に個別適用する 6 サブパターンで実施する。内訳は major `title=""`、major `title="  "`、middle `title=""`、middle `title="  "`、detail `title=""`、detail `title="  "` の 6 件とする | 6 サブパターンすべてで `RoadmapPersistenceInputError` を送出する。各サブパターンで `id_generator.generate()` と `writer.save_items(...)` はいずれも 1 回も呼ばれない。例外 message は仕様未規定のため検証対象外とする。どの level と無効値の組合せでも結果は同じであることを確認する | title 妥当性の網羅 |
| TC-22 | `created_at` は ISO 8601 解析可能かつ UTC offset 必須である | `id_generator` と `writer` の呼び出し有無を検査できる | `created_at="2026-05-21T10:00:00"` と `created_at="not-a-datetime"` の 2 パターンで実施する | 各パターンで `RoadmapPersistenceInputError` を送出する。offset なしの parse 可能値も不正として扱われる。`id_generator.generate()` と `writer.save_items(...)` はいずれも 1 回も呼ばれない | offset 欠落と parse 不可を同時確認 |
| TC-23 | ルート項目が `major` 以外なら `RoadmapPersistenceInputError` を送出する | `id_generator` と `writer` の呼び出し有無を検査できる | ルート 1 件の `level` を `middle`、別パターンで `detail` にした 2 パターンを実施する | 各パターンで `RoadmapPersistenceInputError` を送出する。`id_generator.generate()` と `writer.save_items(...)` はいずれも 1 回も呼ばれない | ルート level 制約 |
| TC-24 | 親子の `level` 関係が `major -> middle -> detail` を外れると `RoadmapPersistenceInputError` を送出する | `id_generator` と `writer` の呼び出し有無を検査できる | `major` の直下に `detail` を置くパターンと、`middle` の直下に `major` を置くパターンを実施する | 各パターンで `RoadmapPersistenceInputError` を送出する。`id_generator.generate()` と `writer.save_items(...)` はいずれも 1 回も呼ばれない | 親子 level 整合性 |
| TC-25 | `detail` が非空 `children` を持つと `RoadmapPersistenceInputError` を送出する | `id_generator` と `writer` の呼び出し有無を検査できる | `detail` 1 件の `children` に下位項目を 1 件入れた入力 | `RoadmapPersistenceInputError` を送出する。`id_generator.generate()` と `writer.save_items(...)` はいずれも 1 回も呼ばれない | 4 段以上禁止 |
| TC-26 | `level` が未サポート値なら `RoadmapPersistenceInputError` を送出する | `id_generator` と `writer` の呼び出し有無を検査できる | 正常な `major -> middle -> detail` 入力をベースに、いずれか 1 項目の `level` を `foo` に置き換えたパターンを実施する | `RoadmapPersistenceInputError` を送出する。`id_generator.generate()` と `writer.save_items(...)` はいずれも 1 回も呼ばれない。例外 message は仕様未規定のため検証対象外とする | 未サポート level 値の検証 |

## Phase 4: 外部連携

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-30 | 成功時に Protocol 経由で依存を所定回数だけ呼び、`roadmap_persisted` ログを値一致で 1 件だけ出力する | `id_generator` / `writer` / `structlog` を差し替え、呼び出し回数とログイベントを検査できる | 正常な 3 件構成 `major -> middle -> detail` を使う | `id_generator.generate()` は `1 + 項目数` である 4 回だけ呼ばれる。`writer.save_items(...)` はちょうど 1 回だけ呼ばれる。`event="roadmap_persisted"` のログがちょうど 1 件だけ出力され、`roadmap_id` は 1 回目の生成値、`topic` は入力値、`saved_count` は `3` と完全一致する。追加キーは許容する。`event="roadmap_persistence_failed"` のログは 0 件である | 成功時の外部連携契約 |
| TC-31 | `writer.save_items(...)` 失敗時は `RoadmapPersistenceWriteError` にラップし、cause chain と失敗ログを値一致で 1 件だけ保持する | `writer.save_items(...)` が例外送出する Protocol 準拠テストダブルと、ログ検査可能な `structlog` を使う | 正常な入力を与え、`writer.save_items(...)` が `RuntimeError("insert failed")` を送出するようにする | `RoadmapPersistenceWriteError` を送出する。送出例外の `__cause__` は元の `RuntimeError` である。`writer.save_items(...)` は 1 回だけ呼ばれる。`event="roadmap_persistence_failed"` のログがちょうど 1 件だけ出力され、`topic` は入力値、`error_type` は `RuntimeError` と完全一致する。`error_type` は wrapper 例外名ではなく元例外クラス名である。追加キーは許容する。`event="roadmap_persisted"` のログは 0 件である | 失敗時の例外変換と可観測性 |

# 網羅性チェック

仕様書の受け入れ基準の各項目に対応するテストケース ID を記載する。
全項目が少なくとも1つのテストケースでカバーされていることを確認する。

| 受け入れ基準 | 対応テストケース |
|---|---|
| 3 段固定構造（`major -> middle -> detail` の `level` 親子関係）に沿う JSON 構造が `FlatRoadmapItem` レコード群に正しく変換される | TC-01, TC-03, TC-10 |
| 親子関係が `parent_id` で正しく表現される | TC-01, TC-03, TC-10, TC-13 |
| 同階層内の順序が `order`（0 始まり連番）で保持される | TC-01, TC-03, TC-10 |
| 初期 `score` が `0` で設定される | TC-01, TC-03, TC-12, TC-13 |
| 全レコードの `created_at` と `updated_at` が入力の `created_at` と一致する | TC-01, TC-03, TC-11, TC-13 |
| `roadmap_id` で全項目が紐付けられる | TC-01, TC-02, TC-03 |
| 空ロードマップ（`items=[]`）が正常に処理される | TC-02 |
| major のみ（`children=[]`）や major→middle のみが正常に処理される | TC-12, TC-13 |
| 未サポート level 値または階層レベルの不整合がエラーになる | TC-23, TC-24, TC-25, TC-26 |
| 保存成功・失敗で構造化ログが出力される | TC-30, TC-31 |

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
