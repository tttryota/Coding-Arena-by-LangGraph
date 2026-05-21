---
feature: roadmap-item-crud
status: ready
---

# 概要

- この機能が解決する課題:
  永続化済みのロードマップに対して、項目の追加・移動・削除を行う。ユーザーが初回生成後のロードマップを、自分の学習順序や理解状況に合わせて局所的に調整できるようにする。
- 利用者・呼び出し元・前提条件:
  呼び出し元は presentation 層の API エンドポイントを想定する。対象ロードマップは `roadmap-persistence` により事前に保存済みであり、項目構造は `major -> middle -> detail` の 3 段固定とする。本機能は Protocol DI で注入された CRUD store と ID 生成ポートを利用する。

# 入出力

- 公開 API:
  モジュールレベル関数を 3 つ公開する。依存は keyword-only 引数で注入する。
  ```python
  add_roadmap_item(
      add_input: RoadmapItemAddInput,
      *,
      store: RoadmapItemCrudStore,
      id_generator: RoadmapItemIdGenerator,
  ) -> RoadmapItemAddResult

  move_roadmap_item(
      move_input: RoadmapItemMoveInput,
      *,
      store: RoadmapItemCrudStore,
  ) -> RoadmapItemMoveResult

  delete_roadmap_item(
      delete_input: RoadmapItemDeleteInput,
      *,
      store: RoadmapItemCrudStore,
  ) -> RoadmapItemDeleteResult
  ```

- 入力:
  - `RoadmapItemAddInput`
    frozen dataclass。
    - `roadmap_id: UUID`
      追加対象ロードマップ ID。
    - `parent_id: UUID | None`
      追加先の親項目 ID。root 直下へ major を追加する場合のみ `None` を許可する。
    - `title: str`
      `strip()` 後に空文字となる値は不可。検証は `strip()` ベースで行うが、保存値は入力文字列をそのまま保持し、trim/strip による正規化は行わない。
    - `description: str`
      空文字を許可する。空白のみの文字列も許可する。保存値は入力文字列をそのまま保持し、trim/strip による正規化は行わない。
    - `order: int | None`
      追加先 sibling 集合での 0 始まり index。`None` の場合は末尾追加。指定時はその index へ挿入する。負数および範囲外は不可。
  - `RoadmapItemMoveInput`
    frozen dataclass。
    - `roadmap_id: UUID`
      移動対象ロードマップ ID。
    - `item_id: UUID`
      移動する項目 ID。
    - `target_parent_id: UUID | None`
      移動先の親項目 ID。root 直下へ移動する場合のみ `None` を許可する。
    - `target_order: int`
      移動先 sibling 集合での 0 始まり index。移動元集合から対象を一度取り除いて order を詰めた後の sibling 集合に対する index として解釈する。負数および範囲外は不可。
  - `RoadmapItemDeleteInput`
    frozen dataclass。
    - `roadmap_id: UUID`
      削除対象ロードマップ ID。
    - `item_id: UUID`
      削除する項目 ID。
    - 補足:
      `confirmed` のような確認フラグは持たない。削除確認は UI / presentation 層責務であり、本 API 契約には含めない。

- 依存インターフェース:
  - `RoadmapItemCrudStore`
    以下の 3 メソッドを提供する Protocol。
    - `find_roadmap(roadmap_id: UUID) -> RoadmapItemCrudRoadmapRecord | None`
      指定ロードマップの全項目 snapshot を返す。ロードマップが存在しない場合は `None`。
    - `find_item(item_id: UUID) -> RoadmapItemCrudItem | None`
      指定 item_id の項目をロードマップ横断で 1 件返す。存在しない場合は `None`。`roadmap_id` 不一致と純粋な未検出を区別するために使う。
    - `replace_items(roadmap_id: UUID, items: list[RoadmapItemCrudItem]) -> None`
      指定ロードマップに属する全項目集合を、与えられた `items` で原子的に置き換える。`items` は `RoadmapItemCrudRoadmapRecord.items` と同じ正準列挙順で渡される。成功時は当該ロードマップの項目集合が `items` と完全一致し、以後 `find_roadmap` が返す snapshot も同じ正準列挙順に従う。失敗時は部分更新を残さず例外を送出する。
  - `RoadmapItemIdGenerator`
    `generate() -> UUID` を提供する Protocol。`add_roadmap_item` で新規項目 ID の生成にのみ使う。入力検証通過後に 1 回だけ呼ばれ、この呼び出しが失敗した場合は `RoadmapItemCrudStoreError` を `raise ... from ...` で送出し、`store.replace_items` は呼ばれない。
  - `RoadmapItemCrudRoadmapRecord`
    store が返すロードマップ snapshot。frozen dataclass。
    - `roadmap_id: UUID`
    - `items: list[RoadmapItemCrudItem]`
      そのロードマップに属する全項目。返却順は正準列挙順に固定し、root major 集合を `order` 昇順で走査し、各項目の子集合も `order` 昇順でたどる pre-order DFS とする。delete の `deleted_item_ids` もこの正準列挙順を削除部分木へ制限した順で返す。
    - store 契約:
      - 同一 roadmap 内で `id` は一意。
      - 階層は `major(parent_id=None) -> middle(parent_id=major.id) -> detail(parent_id=middle.id)` の 3 段のみ。
      - 非 root の `parent_id` は同一 roadmap 内の既存親を参照する。
      - root major 集合および各 sibling 集合で `order` は 0 始まりかつ一意。
      - CRUD モジュールはこの整合済み snapshot を前提に動作し、事前に壊れた永続データの修復・自動補正・再採番は本仕様に含めない。
  - `RoadmapItemCrudItem`
    store が返し、かつ `replace_items` に渡すフラット項目 DTO。frozen dataclass。
    - `id: UUID`
    - `roadmap_id: UUID`
    - `parent_id: UUID | None`
    - `level: Literal["major", "middle", "detail"]`
    - `title: str`
    - `description: str`
    - `order: int`
      root major 集合または同一親配下 sibling 集合での 0 始まり index。同一集合内で一意。
    - `score: int`
      detail の進捗スコア。add 時の新規項目は常に `0`。move/delete は既存値を保持する。

- 出力:
  - `RoadmapItemAddResult`
    frozen dataclass。
    - `created_item: RoadmapItemCrudItem`
      追加後の新規項目。`id` は `id_generator.generate()` の返却値、`score=0`、`order` は挿入後の最終値。
  - `RoadmapItemMoveResult`
    frozen dataclass。
    - `moved_item: RoadmapItemCrudItem`
      移動後の項目。`id`、`title`、`description`、`score` は元の値を保持し、`parent_id` と `order` は移動後の値。
  - `RoadmapItemDeleteResult`
    frozen dataclass。
    - `deleted_item_ids: tuple[UUID, ...]`
      削除された項目 ID の集合。対象自身と配下 descendants を含む。順序は、削除対象自身を先頭に、その削除部分木を `RoadmapItemCrudRoadmapRecord.items` と同じ正準列挙順でたどる pre-order DFS とする。すなわち sibling は常に `order` 昇順で列挙する。
    - `deleted_count: int`
      `deleted_item_ids` の件数。

- 操作規約:
  - 共通:
    - 利用可能な階層は `major` / `middle` / `detail` の 3 段固定のみ。
    - `order` は root major 集合および各 sibling 集合ごとの 0 始まり index とし、同一集合内で一意であることを保つ。
    - 失敗時は `replace_items` を呼ばず、部分更新しない。`order` の再採番は成功時にのみ適用する。
  - add:
    - `parent_id=None` の場合は root major 追加とみなし、`level=major` を自動決定する。
    - `parent_id` が major の場合は `level=middle`、middle の場合は `level=detail` を自動決定する。
    - `parent_id` が detail の場合は 4 階層目になるため不正入力とする。
    - `order=None` の場合は追加先 sibling 集合の末尾へ追加する。
    - `order` 指定時はその index に挿入し、同一 sibling 集合で `order >= 指定値` の既存兄弟を `+1` シフトする。
    - `order` は `0 <= order <= sibling_count` の範囲のみ許可し、範囲外は補正せず入力エラーとする。
  - move:
    - 移動先 level は `target_parent_id` から自動判定する。`target_parent_id=None` の場合は root major 集合を意味し、移動対象が `major` のときのみ許可する。
    - `target_parent_id` が major の場合は移動対象 level は `middle`、middle の場合は `detail` でなければならない。level が一致しない移動は不正入力とする。
    - 同一親内 move も、先に移動元 sibling 集合から対象を取り除いて `order` を詰め、その後 `target_order` へ挿入する。
    - `target_order` は、取り除き後の移動先 sibling 集合に対して `0 <= target_order <= sibling_count_after_removal` の範囲のみ許可し、範囲外は補正せず入力エラーとする。
    - 移動対象自身またはその子孫配下への移動は循環を作るため不正入力とする。
  - delete:
    - 指定項目自身と、その全 descendants を連鎖削除する。
    - `deleted_item_ids` は削除部分木を正準列挙順でたどった結果と一致し、対象自身、子、孫の順に pre-order DFS で返す。
    - 削除後は残った sibling 集合の `order` を 0 から詰め直す。
    - 最後の major を削除してロードマップの root major 集合が空になる操作は不正入力とする。

- エラー:
  - `RoadmapItemCrudInputError`
    以下のような、識別子未検出以外の不正入力または構造破壊要求の場合。
    - `title` が `strip()` 後に空文字
    - `order` / `target_order` が負数または範囲外
    - `parent_id` が detail を指す add
    - `target_parent_id` が detail を指す move
    - level 不整合な move
    - 他ロードマップ配下の `item_id` / `parent_id` / `target_parent_id` を参照する操作
    - 自己配下または子孫配下への move
    - 最後の major の delete
  - `RoadmapItemCrudNotFoundError`
    以下のような識別子未検出の場合。
    - `roadmap_id` が存在しない
    - `item_id` が存在しない
    - `parent_id` または `target_parent_id` が存在しない
  - `RoadmapItemCrudStoreError`
    `store.find_roadmap` / `store.find_item` / `store.replace_items` / `id_generator.generate()` の依存呼び出しが失敗した場合。元例外を `raise ... from ...` で保持して送出する。

# 具体例

## 例1: root 直下へ major を追加する

- 入力:
  ```yaml
  add_input:
    roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    parent_id: null
    title: "設計"
    description: "設計原則とレビュー観点"
    order: 1
  store.find_roadmap の返却値:
    roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    items:
      - id: "11111111-1111-1111-1111-111111111111"
        roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        parent_id: null
        level: major
        title: "基礎"
        description: "基本概念"
        order: 0
        score: 0
      - id: "22222222-2222-2222-2222-222222222222"
        roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        parent_id: null
        level: major
        title: "応用"
        description: "応用技術"
        order: 1
        score: 0
  id_generator.generate の返却値:
    - "33333333-3333-3333-3333-333333333333"
  ```
- `store.replace_items` に渡される `items`:
  ```yaml
  - id: "11111111-1111-1111-1111-111111111111"
    roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    parent_id: null
    level: major
    title: "基礎"
    description: "基本概念"
    order: 0
    score: 0
  - id: "33333333-3333-3333-3333-333333333333"
    roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    parent_id: null
    level: major
    title: "設計"
    description: "設計原則とレビュー観点"
    order: 1
    score: 0
  - id: "22222222-2222-2222-2222-222222222222"
    roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    parent_id: null
    level: major
    title: "応用"
    description: "応用技術"
    order: 2
    score: 0
  ```
- 期待される出力:
  ```yaml
  created_item:
    id: "33333333-3333-3333-3333-333333333333"
    roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    parent_id: null
    level: major
    title: "設計"
    description: "設計原則とレビュー観点"
    order: 1
    score: 0
  ```

## 例2: 同一親内で middle を move する

- 注記:
  この例は同一親内 move における sibling 順序の変化だけを示す説明用抜粋であり、`store.find_roadmap(...)` が返す full snapshot や `roadmap_id` / `level` / `description` / `score` を含む完全 fixture を規定するものではない。

- 変更前 sibling 集合:
  ```yaml
  parent major: "11111111-1111-1111-1111-111111111111"
  children:
    - id: "aaaa1111-1111-1111-1111-111111111111"
      title: "変数"
      order: 0
    - id: "bbbb2222-2222-2222-2222-222222222222"
      title: "関数"
      order: 1
    - id: "cccc3333-3333-3333-3333-333333333333"
      title: "型推論"
      order: 2
  move_input:
    roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    item_id: "aaaa1111-1111-1111-1111-111111111111"
    target_parent_id: "11111111-1111-1111-1111-111111111111"
    target_order: 2
  ```
- 振る舞い:
  まず `"変数"` を sibling 集合から取り除いて `"関数"(0), "型推論"(1)` に詰め、その後 `target_order=2` へ挿入する。
- 変更後 sibling 集合:
  ```yaml
  children:
    - id: "bbbb2222-2222-2222-2222-222222222222"
      title: "関数"
      order: 0
    - id: "cccc3333-3333-3333-3333-333333333333"
      title: "型推論"
      order: 1
    - id: "aaaa1111-1111-1111-1111-111111111111"
      title: "変数"
      order: 2
  ```

## 例3: 別親へ detail を move する

- 注記:
  この例は別親 move による source / target sibling 集合の変化だけを示す説明用抜粋であり、`store.find_roadmap(...)` が返す full snapshot や `description` / `score` を含む完全 fixture を規定するものではない。

- 変更前:
  ```yaml
  source middle: "22222222-2222-2222-2222-222222222222"
  source children:
    - id: "dddd4444-4444-4444-4444-444444444444"
      title: "デコレータ"
      order: 0
    - id: "eeee5555-5555-5555-5555-555555555555"
      title: "ユーティリティ型"
      order: 1
  target middle: "33333333-3333-3333-3333-333333333333"
  target children:
    - id: "ffff6666-6666-6666-6666-666666666666"
      title: "ジェネリクス"
      order: 0
  move_input:
    roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    item_id: "eeee5555-5555-5555-5555-555555555555"
    target_parent_id: "33333333-3333-3333-3333-333333333333"
    target_order: 1
  ```
- 変更後:
  ```yaml
  source children:
    - id: "dddd4444-4444-4444-4444-444444444444"
      title: "デコレータ"
      order: 0
  target children:
    - id: "ffff6666-6666-6666-6666-666666666666"
      title: "ジェネリクス"
      order: 0
    - id: "eeee5555-5555-5555-5555-555555555555"
      title: "ユーティリティ型"
      order: 1
  ```

## 例4: delete による連鎖削除と order 圧縮

- 注記:
  この例は delete 対象部分木の正準列挙順と、削除後の root major 集合の変化だけを示す説明用抜粋であり、`store.find_roadmap(...)` が返す full snapshot や残存 descendants を含む完全 fixture を規定するものではない。

- 変更前:
  ```yaml
  root majors:
    - id: "11111111-1111-1111-1111-111111111111"
      title: "基礎"
      order: 0
    - id: "22222222-2222-2222-2222-222222222222"
      title: "応用"
      order: 1
    - id: "33333333-3333-3333-3333-333333333333"
      title: "実践"
      order: 2
  delete_input:
    roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    item_id: "22222222-2222-2222-2222-222222222222"
  subtree of "応用" in canonical order:
    - id: "22222222-2222-2222-2222-222222222222"
      parent_id: null
      level: major
      order: 1
    - id: "44444444-4444-4444-4444-444444444444"
      parent_id: "22222222-2222-2222-2222-222222222222"
      level: middle
      order: 0
    - id: "55555555-5555-5555-5555-555555555555"
      parent_id: "44444444-4444-4444-4444-444444444444"
      level: detail
      order: 0
  ```
- 変更後:
  ```yaml
  root majors:
    - id: "11111111-1111-1111-1111-111111111111"
      title: "基礎"
      order: 0
    - id: "33333333-3333-3333-3333-333333333333"
      title: "実践"
      order: 1
  delete_result:
    deleted_item_ids:
      - "22222222-2222-2222-2222-222222222222"
      - "44444444-4444-4444-4444-444444444444"
      - "55555555-5555-5555-5555-555555555555"
    deleted_count: 3
  ```

## 例5: 文字列入力の検証

- 正常:
  ```yaml
  title: "  Generics  "
  description: "   "
  ```
  - `title` は `strip()` 後に空ではないため許可する。
  - 保存値は `title="  Generics  "`、`description="   "` のまま保持する。
- 異常:
  ```yaml
  title: "   "
  description: ""
  ```
  - `title` は `strip()` 後に空文字となるため `RoadmapItemCrudInputError`。
  - `description` が空文字であること自体はエラー理由にしない。

# 境界条件

- ケース: `roadmap_id` が存在しない。
  - 振る舞い: `RoadmapItemCrudNotFoundError` を送出する。
  - 理由: 対象ロードマップの snapshot を取得できないため。
- ケース: `item_id` が存在しない。
  - 振る舞い: `RoadmapItemCrudNotFoundError` を送出する。
  - 理由: 操作対象を特定できないため。
- ケース: `parent_id` または `target_parent_id` が存在しない。
  - 振る舞い: `RoadmapItemCrudNotFoundError` を送出する。
  - 理由: 追加先・移動先を特定できないため。
- ケース: `item_id` / `parent_id` / `target_parent_id` は存在するが、指定 `roadmap_id` とは別ロードマップに属する。
  - 振る舞い: `RoadmapItemCrudInputError` を送出する。
  - 理由: 識別子は存在しても、対象ロードマップに対する正当な参照ではないため。
- ケース: root major 追加で `parent_id=None`、`order=None`。
  - 振る舞い: `level=major` として root major 集合の末尾へ追加する。
  - 理由: major 追加の入力形状を通常 add API 内で表現するため。
- ケース: `parent_id` が detail を指す add。
  - 振る舞い: `RoadmapItemCrudInputError` を送出する。
  - 理由: 4 階層目の追加を許可しないため。
- ケース: `target_parent_id=None` で middle または detail を root へ move しようとする。
  - 振る舞い: `RoadmapItemCrudInputError` を送出する。
  - 理由: root 直下は major のみ許可するため。
- ケース: major を major 配下へ move しようとする、または detail を major 配下へ move しようとする。
  - 振る舞い: `RoadmapItemCrudInputError` を送出する。
  - 理由: `major -> middle -> detail` の level 規約に反するため。
- ケース: 同一親内 move で `target_order` が現 sibling 件数に対して末尾。
  - 振る舞い: 取り除き後の sibling 集合の末尾へ挿入する。
  - 理由: remove 後 index 規約を採用するため最終 order が一意に決まる。
- ケース: `order` または `target_order` が負数。
  - 振る舞い: `RoadmapItemCrudInputError` を送出する。
  - 理由: 0 始まり index 契約に反するため。
- ケース: `order` または `target_order` が許容範囲を超える。
  - 振る舞い: `RoadmapItemCrudInputError` を送出する。末尾への丸め込みや自動補正はしない。
  - 理由: downstream テストで最終 order を一意に固定するため。
- ケース: 自己自身または子孫配下への move。
  - 振る舞い: `RoadmapItemCrudInputError` を送出する。
  - 理由: 循環構造を防ぐため。
- ケース: 削除対象が middle または detail。
  - 振る舞い: 対象自身と配下 descendants を削除し、残った sibling 集合の order を詰める。
  - 理由: 連鎖削除を許可する通常ケース。
- ケース: delete の `deleted_item_ids` の順序。
  - 振る舞い: 削除部分木を正準列挙順でたどった tuple を返す。対象自身を先頭にし、その後は sibling を `order` 昇順でたどる pre-order DFS とする。
  - 理由: snapshot 列挙順から delete 結果を機械的に導けるようにし、downstream テストの期待値を一意に固定するため。
- ケース: major が 1 件だけのロードマップで、その major を削除しようとする。
  - 振る舞い: `RoadmapItemCrudInputError` を送出する。
  - 理由: ロードマップの root major 集合を空にしないため。
- ケース: `title=""` または `title` が空白のみ。
  - 振る舞い: `RoadmapItemCrudInputError` を送出する。
  - 理由: `strip()` 後に空文字となる title は識別に使えないため。
- ケース: `description=""`。
  - 振る舞い: 正常に処理する。
  - 理由: 空の説明文を許可する契約のため。
- ケース: `description` が空白のみ。
  - 振る舞い: 正常に処理し、入力文字列をそのまま保持する。
  - 理由: description に `strip()` ベースの正規化・拒否を入れないため。
- ケース: add の入力検証通過後に `id_generator.generate()` が失敗する。
  - 振る舞い: `RoadmapItemCrudStoreError` を送出し、元例外を cause として保持する。`store.replace_items` は呼ばれず、永続状態は変更されない。
  - 理由: ID 生成も依存呼び出しの一部であり、最終 snapshot を確定できないまま部分保存してはならないため。
- ルール間の相互作用:
  1. 各操作は `store.find_roadmap` で対象ロードマップ snapshot を取得し、識別子未検出の可能性がある場合のみ `store.find_item` を追加利用して「存在しない」と「別ロードマップ」を区別する。
  2. add は入力検証後に `id_generator.generate()` を 1 回だけ呼ぶ。`generate()` が失敗した場合は `RoadmapItemCrudStoreError` を送出し、その add では `store.replace_items` を呼ばない。
  3. add の成功経路、move、delete は入力検証通過後に `store.replace_items` を 1 回だけ呼ぶ。成功時のみ order 再採番結果を保存する。
  4. `store.replace_items` を含む依存呼び出しが失敗した場合は `RoadmapItemCrudStoreError` を送出し、呼び出し元から見える永続状態は変更前のままでなければならない。

# 非機能・制約

- 性能:
  各操作は対象ロードマップ全項目 snapshot を 1 回読み、メモリ上で検証と再採番を行い、成功時のみ `replace_items` を 1 回呼ぶ。項目数に対して線形時間とし、個人用ツールでのロードマップ規模では十分な性能とする。
- 原子性:
  add / move / delete は成功時にのみ最終 snapshot を保存し、失敗時は部分更新を残さない。`id_generator.generate()` 失敗時を含めて `store.replace_items` を呼ばなかった操作は永続状態を変更しない。`order` の詰め直しや descendants 削除も同一保存単位で扱う。
- 外部依存:
  依存先は `Protocol` で表現した `RoadmapItemCrudStore` と `RoadmapItemIdGenerator` のみ。RDB 実装詳細、トランザクション実装詳細、UI の確認ダイアログ、HTTP レスポンス整形はこの機能の契約に含めない。
- 入力正規化:
  `title` 以外の文字列に trim・空白正規化・Unicode 正規化・大小文字変換・補完は行わない。`title` も検証にのみ `strip()` を使い、保存値そのものは変換しない。

# モジュール構成

- 構成方針: 2 モジュールに分割する
- 配置先:
  `backend/roadmap/infrastructure/` に配置する。
- モジュール一覧:
  - `roadmap_item_crud_types.py`
    - 責務: DTO（`RoadmapItemAddInput`、`RoadmapItemMoveInput`、`RoadmapItemDeleteInput`、`RoadmapItemCrudItem`、`RoadmapItemCrudRoadmapRecord`、`RoadmapItemAddResult`、`RoadmapItemMoveResult`、`RoadmapItemDeleteResult`）、Protocol（`RoadmapItemCrudStore`、`RoadmapItemIdGenerator`）、例外型（`RoadmapItemCrudInputError`、`RoadmapItemCrudNotFoundError`、`RoadmapItemCrudStoreError`）の定義
  - `roadmap_item_crud.py`
    - 責務: `add_roadmap_item` / `move_roadmap_item` / `delete_roadmap_item` のオーケストレーション、階層検証、order 再採番、連鎖削除対象の決定、store 呼び出し

# 技術判断

- 判断:
  `order` は root major 集合および各 sibling 集合ごとの 0 始まり index に固定する。
  - 理由:
    Python list の index と一致し、add/move の挿入位置を変換なしで扱えるため。範囲外を補正しない契約にすると最終 sibling order を downstream テストで一意に期待できる。
- 判断:
  snapshot と delete 結果の列挙順は、root major から sibling を `order` 昇順でたどる pre-order DFS に固定する。
  - 理由:
    `deleted_item_ids` の tuple 順序を snapshot 列挙規則から機械的に導けるようにし、実装ごとの差分なく downstream テスト期待値を一意に固定するため。
- 判断:
  root 直下追加は `parent_id=None` で表現する。
  - 理由:
    major 追加だけのために別 API や `level` 手入力を増やさず、既存の parent_id ベース CRUD 契約のまま root major 追加を扱えるため。
- 判断:
  move の index 解釈は「移動元から一度抜いて詰める -> 移動先へ挿入」の順に固定する。
  - 理由:
    同一親内 move と別親 move を同じ規則で扱え、target_order の意味が一つに定まるため。
- 判断:
  delete 確認は UI / presentation 層責務とし、backend delete API は確認フラグを受け取らない。
  - 理由:
    確認ダイアログは対話 UI の責務であり、infrastructure 契約に `confirmed` のような状態を持ち込むと downstream の API・テストが不要に複雑化するため。
- 判断:
  store への書き込みは `replace_items` 1 回の snapshot 置換に寄せる。
  - 理由:
    項目数が小規模であり、add/move/delete 後の最終状態を決定してから原子的に保存する方が order 再採番・連鎖削除・循環防止をテストしやすいため。

# スコープ外

- 対応しないこと: 項目の title / description の編集
- 対応しないこと: reorder 専用 API の追加
- 対応しないこと: `level` の手入力 API
- 対応しないこと: 4 階層目以降の追加
- 対応しないこと: 削除の取り消し（undo）
- 対応しないこと: 削除確認ダイアログや `confirmed` フラグの処理
- 対応しないこと: 既に壊れている永続データの修復・自動補正

# 受け入れ基準

- [ ] 公開 API は `add_roadmap_item` / `move_roadmap_item` / `delete_roadmap_item` の module-level function として定義され、依存は keyword-only DI で受け取る
- [ ] 実装対象モジュールは `backend/roadmap/infrastructure/roadmap_item_crud.py` と `backend/roadmap/infrastructure/roadmap_item_crud_types.py` に固定される
- [ ] add は `parent_id=None` で root major 追加を表現でき、`level=major` を自動決定する
- [ ] add は `parent_id=major` なら middle、`parent_id=middle` なら detail を自動決定し、`parent_id=detail` ではエラーになる
- [ ] `order` は 0 始まり sibling index として扱われ、add の `order=None` は末尾追加、`order` 指定は挿入と兄弟 `+1` シフトになる
- [ ] add / move の範囲外 `order` は補正されず `RoadmapItemCrudInputError` になる
- [ ] move は「移動元から対象を抜いて詰める -> 移動先へ挿入」の順で order を決定し、同一親内 move でも最終 order が一意に定まる
- [ ] move で存在しない `item_id` / `target_parent_id` は `RoadmapItemCrudNotFoundError` になる
- [ ] add / move / delete で、存在するが別ロードマップに属する `item_id` / `parent_id` / `target_parent_id` は `RoadmapItemCrudInputError` になる
- [ ] move で自己配下または子孫配下への移動は `RoadmapItemCrudInputError` になる
- [ ] delete は対象自身と配下 descendants を連鎖削除し、残った sibling 集合の order を 0 から詰め直す
- [ ] `RoadmapItemCrudRoadmapRecord.items` と `RoadmapItemDeleteResult.deleted_item_ids` の列挙順は、root major から sibling を `order` 昇順でたどる pre-order DFS に固定され、delete 結果の tuple 順序は snapshot 規約から一意に導ける
- [ ] 最後の major を削除する操作は `RoadmapItemCrudInputError` になる
- [ ] add の `title` は `strip()` 後に空文字なら `RoadmapItemCrudInputError` になり、通過時も保存値は入力文字列をそのまま保持する
- [ ] add の `description` は空文字と空白のみ文字列を許可し、保存値は入力文字列をそのまま保持する
- [ ] delete API は確認フラグを要求せず、削除確認は UI / presentation 層責務として仕様から除外される
- [ ] 失敗時は部分更新せず、`order` 再採番は成功時にのみ保存される
- [ ] add は入力検証通過後に `id_generator.generate()` を 1 回だけ呼び、生成失敗時は `RoadmapItemCrudStoreError` が送出され、元例外が cause として保持され、`store.replace_items` は呼ばれない
- [ ] store の lookup / replace 失敗時は `RoadmapItemCrudStoreError` が送出され、元例外が cause として保持される
