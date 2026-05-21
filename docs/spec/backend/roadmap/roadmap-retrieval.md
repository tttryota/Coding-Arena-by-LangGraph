---
feature: roadmap/roadmap-retrieval
status: ready
---

# 概要

- この機能が解決する課題:
  RDB にフラットレコードとして保存されたロードマップ項目を、parent_id に基づいてツリー構造に再構築し、detail 項目の score から middle・major のスコアを集約して返す。フロントエンドがロードマップの全体像と進捗状況を表示するためのデータを提供する。
- 利用者・呼び出し元・前提条件:
  呼び出し元は presentation 層の API エンドポイントを想定する。ロードマップは `roadmap-persistence` モジュールによって事前に永続化されている前提。本機能は `Protocol` による DI で注入された読み取りポートを利用する。構造化ログ出力には `structlog` を用いる。

# 入出力

- 公開 API:
  モジュールレベル関数を 2 つ公開する。依存は keyword-only 引数で注入する。
  ```python
  get_roadmap(
      roadmap_id: UUID,
      *,
      reader: RoadmapRetrievalReader,
  ) -> RoadmapTree

  list_roadmaps(
      *,
      reader: RoadmapRetrievalReader,
  ) -> RoadmapListResult
  ```

- 入力:
  - `get_roadmap` の入力:
    - `roadmap_id: UUID` — 取得対象のロードマップ ID。
  - `list_roadmaps` の入力:
    引数なし（reader のみ）。

- 依存インターフェース:
  - `RoadmapRetrievalReader`
    以下の 2 メソッドを提供する Protocol。
    - `find_roadmap(roadmap_id: UUID) -> RoadmapRecord | None`
      指定された roadmap_id のロードマップメタ情報と配下の全項目を返す。存在しない場合は `None`。
    - `find_all_roadmaps() -> list[RoadmapRecord]`
      全ロードマップのメタ情報と配下の全項目を返す。ロードマップが 1 件もない場合は空リスト。返却順は不定。
  - `RoadmapRecord`
    reader が返すデータ構造。frozen dataclass。
    - `roadmap_id: UUID`
    - `topic: str`
    - `items: list[RoadmapItemRecord]`
      そのロードマップに属する全項目。返却順は不定。
  - `RoadmapItemRecord`
    reader が返すフラットな項目レコード。frozen dataclass。
    - `id: UUID`
    - `parent_id: UUID | None`
      major レベルの場合は `None`。
    - `level: Literal["major", "middle", "detail"]`
    - `title: str`
    - `description: str`
    - `order: int`
      ルート major 集合または同一親の子項目内での 0 始まりの表示順。同一集合内で一意。
    - `score: int`
      detail 項目のスコア（0–100）。middle・major の DB 上の score 値は使用しない（算出で上書きする）。
    - `last_quiz_at: str | None`
      最終クイズ日時。ISO 8601 文字列（offset 付き）。クイズ未実施の場合は `None`。
    - reader 契約:
      - 同一 roadmap 内で `id` は一意。
      - 階層は `major(parent_id=None) -> middle(parent_id=major.id) -> detail(parent_id=middle.id)` の 3 段のみ。
      - 非 root の `parent_id` は同一 roadmap 内の既存親を必ず参照する。
      - `order` はルート major 集合および各兄弟集合ごとに一意な 0 始まり表示順である。
      - 入力例・テスト入力は flat な `RoadmapItemRecord` 一覧のみを用いる。`children=[]` を含むツリー shorthand は reader 契約外であり、本仕様では扱わない。
  - `structlog`
    構造化ログ出力。モジュールロガーを使い、各ログ呼び出しでコンテキスト情報を渡す。

- 出力:
  - `RoadmapTree`
    frozen dataclass。`get_roadmap` の戻り値。
    - `roadmap_id: UUID`
      `RoadmapRecord.roadmap_id` をそのまま設定する。trim・空白正規化・Unicode 正規化・大小文字変換・補完は行わない。
    - `topic: str`
      `RoadmapRecord.topic` をそのまま設定する。trim・空白正規化・Unicode 正規化・大小文字変換・補完は行わない。
    - `overall_score: int`
      全 major 項目のスコアの平均を小数点以下切り捨てした値。major が 0 件の場合は `0`。
    - `items: list[RoadmapTreeNode]`
      ルートレベル（major）のツリーノード一覧。reader 契約で root major 集合内の `order` が一意である前提で、`order` 昇順。
  - `RoadmapTreeNode`
    frozen dataclass。再帰構造のツリーノード。
    - `id: UUID`
      `RoadmapItemRecord.id` をそのまま設定する。trim・空白正規化・Unicode 正規化・大小文字変換・補完は行わない。
    - `title: str`
      `RoadmapItemRecord.title` をそのまま設定する。trim・空白正規化・Unicode 正規化・大小文字変換・補完は行わない。
    - `description: str`
      `RoadmapItemRecord.description` をそのまま設定する。trim・空白正規化・Unicode 正規化・大小文字変換・補完は行わない。
    - `level: Literal["major", "middle", "detail"]`
    - `score: int`
      detail: DB 値をそのまま使う。middle: 配下 detail のスコア平均を切り捨て。major: 配下 middle のスコア平均を切り捨て。子が 0 件の場合は `0`。
    - `order: int`
      `RoadmapItemRecord.order` をそのまま設定する。補正や再採番は行わない。
    - `children: list[RoadmapTreeNode]`
      子ノード一覧。reader 契約で同一親配下の `order` が一意である前提で、`order` 昇順。detail の場合は空リスト。
    - `last_quiz_at: str | None`
      detail のみ値を持つ。major・middle は `None`。
  - `RoadmapListResult`
    frozen dataclass。`list_roadmaps` の戻り値。
    - `items: list[RoadmapListItem]`
      reader が返す順序を保持する。
    - `total_count: int`
      `items` の件数。
  - `RoadmapListItem`
    frozen dataclass。
    - `roadmap_id: UUID`
      `RoadmapRecord.roadmap_id` をそのまま設定する。trim・空白正規化・Unicode 正規化・大小文字変換・補完は行わない。
    - `topic: str`
      `RoadmapRecord.topic` をそのまま設定する。trim・空白正規化・Unicode 正規化・大小文字変換・補完は行わない。
    - `overall_score: int`
      `RoadmapTree.overall_score` と同じ算出ロジック。

- エラー:
  - `RoadmapRetrievalNotFoundError`:
    `get_roadmap` で指定された `roadmap_id` に対応するロードマップが存在しない場合（`reader.find_roadmap` が `None` を返した場合）。
  - `RoadmapRetrievalStoreError`:
    reader の操作が失敗した場合（例外送出時）。

# 具体例

## 例1: 複数 major を含むツリー構造の取得

- 入力:
  ```yaml
  roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
  reader.find_roadmap の返却値:
    roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    topic: "TypeScript"
    items:
      - id: "11111111-1111-1111-1111-111111111111"
        parent_id: null
        level: major
        title: "基礎"
        description: "TypeScript の基本概念"
        order: 0
        score: 0
        last_quiz_at: null
      - id: "22222222-2222-2222-2222-222222222222"
        parent_id: "11111111-1111-1111-1111-111111111111"
        level: middle
        title: "変数と型"
        description: "型システムの基礎"
        order: 0
        score: 0
        last_quiz_at: null
      - id: "33333333-3333-3333-3333-333333333333"
        parent_id: "22222222-2222-2222-2222-222222222222"
        level: detail
        title: "プリミティブ型"
        description: "string, number, boolean 等の基本型"
        order: 0
        score: 90
        last_quiz_at: "2026-05-15T10:00:00+09:00"
      - id: "44444444-4444-4444-4444-444444444444"
        parent_id: "22222222-2222-2222-2222-222222222222"
        level: detail
        title: "配列とタプル"
        description: "配列型とタプル型の使い分け"
        order: 1
        score: 60
        last_quiz_at: "2026-05-16T14:00:00+09:00"
      - id: "55555555-5555-5555-5555-555555555555"
        parent_id: "11111111-1111-1111-1111-111111111111"
        level: middle
        title: "関数"
        description: "関数の型付けと引数"
        order: 1
        score: 0
        last_quiz_at: null
      - id: "66666666-6666-6666-6666-666666666666"
        parent_id: "55555555-5555-5555-5555-555555555555"
        level: detail
        title: "引数の型注釈"
        description: "パラメータと戻り値の型指定"
        order: 0
        score: 40
        last_quiz_at: "2026-05-17T09:00:00+09:00"
      - id: "77777777-7777-7777-7777-777777777777"
        parent_id: null
        level: major
        title: "応用"
        description: "TypeScript の応用技術"
        order: 1
        score: 0
        last_quiz_at: null
      - id: "88888888-8888-8888-8888-888888888888"
        parent_id: "77777777-7777-7777-7777-777777777777"
        level: middle
        title: "ジェネリクス"
        description: "型パラメータによる汎用化"
        order: 0
        score: 0
        last_quiz_at: null
      - id: "99999999-9999-9999-9999-999999999999"
        parent_id: "88888888-8888-8888-8888-888888888888"
        level: detail
        title: "基本構文"
        description: "T extends U の基本"
        order: 0
        score: 30
        last_quiz_at: "2026-05-18T11:00:00+09:00"
  ```
- スコア算出過程:
  - middle "変数と型": detail [90, 60] → floor(150 / 2) = 75
  - middle "関数": detail [40] → floor(40 / 1) = 40
  - major "基礎": middle [75, 40] → floor(115 / 2) = 57
  - middle "ジェネリクス": detail [30] → floor(30 / 1) = 30
  - major "応用": middle [30] → floor(30 / 1) = 30
  - overall: major [57, 30] → floor(87 / 2) = 43
- 期待される出力:
  ```yaml
  roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
  topic: "TypeScript"
  overall_score: 43
  items:
    - id: "11111111-1111-1111-1111-111111111111"
      title: "基礎"
      description: "TypeScript の基本概念"
      level: major
      score: 57
      order: 0
      last_quiz_at: null
      children:
        - id: "22222222-2222-2222-2222-222222222222"
          title: "変数と型"
          description: "型システムの基礎"
          level: middle
          score: 75
          order: 0
          last_quiz_at: null
          children:
            - id: "33333333-3333-3333-3333-333333333333"
              title: "プリミティブ型"
              description: "string, number, boolean 等の基本型"
              level: detail
              score: 90
              order: 0
              last_quiz_at: "2026-05-15T10:00:00+09:00"
              children: []
            - id: "44444444-4444-4444-4444-444444444444"
              title: "配列とタプル"
              description: "配列型とタプル型の使い分け"
              level: detail
              score: 60
              order: 1
              last_quiz_at: "2026-05-16T14:00:00+09:00"
              children: []
        - id: "55555555-5555-5555-5555-555555555555"
          title: "関数"
          description: "関数の型付けと引数"
          level: middle
          score: 40
          order: 1
          last_quiz_at: null
          children:
            - id: "66666666-6666-6666-6666-666666666666"
              title: "引数の型注釈"
              description: "パラメータと戻り値の型指定"
              level: detail
              score: 40
              order: 0
              last_quiz_at: "2026-05-17T09:00:00+09:00"
              children: []
    - id: "77777777-7777-7777-7777-777777777777"
      title: "応用"
      description: "TypeScript の応用技術"
      level: major
      score: 30
      order: 1
      last_quiz_at: null
      children:
        - id: "88888888-8888-8888-8888-888888888888"
          title: "ジェネリクス"
          description: "型パラメータによる汎用化"
          level: middle
          score: 30
          order: 0
          last_quiz_at: null
          children:
            - id: "99999999-9999-9999-9999-999999999999"
              title: "基本構文"
              description: "T extends U の基本"
              level: detail
              score: 30
              order: 0
              last_quiz_at: "2026-05-18T11:00:00+09:00"
              children: []
  ```

## 例2: 項目 0 件のロードマップ

- 入力:
  ```yaml
  roadmap_id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
  reader.find_roadmap の返却値:
    roadmap_id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    topic: "Rust"
    items: []
  ```
- 期待される出力:
  ```yaml
  roadmap_id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
  topic: "Rust"
  overall_score: 0
  items: []
  ```

## 例3: スコアの端数切り捨て

- 入力:
  ```yaml
  roadmap_id: "cccccccc-cccc-cccc-cccc-cccccccccccc"
  reader.find_roadmap の返却値:
    roadmap_id: "cccccccc-cccc-cccc-cccc-cccccccccccc"
    topic: "Python"
    items:
      - id: "aa111111-1111-1111-1111-111111111111"
        parent_id: null
        level: major
        title: "基礎"
        description: ""
        order: 0
        score: 0
        last_quiz_at: null
      - id: "aa222222-2222-2222-2222-222222222222"
        parent_id: "aa111111-1111-1111-1111-111111111111"
        level: middle
        title: "データ構造"
        description: ""
        order: 0
        score: 0
        last_quiz_at: null
      - id: "aa333333-3333-3333-3333-333333333333"
        parent_id: "aa222222-2222-2222-2222-222222222222"
        level: detail
        title: "リスト"
        description: ""
        order: 0
        score: 80
        last_quiz_at: null
      - id: "aa444444-4444-4444-4444-444444444444"
        parent_id: "aa222222-2222-2222-2222-222222222222"
        level: detail
        title: "辞書"
        description: ""
        order: 1
        score: 70
        last_quiz_at: null
      - id: "aa555555-5555-5555-5555-555555555555"
        parent_id: "aa222222-2222-2222-2222-222222222222"
        level: detail
        title: "集合"
        description: ""
        order: 2
        score: 50
        last_quiz_at: null
  ```
- スコア算出過程:
  - middle "データ構造": detail [80, 70, 50] → (80 + 70 + 50) / 3 = 66.666... → floor = 66
  - major "基礎": middle [66] → 66
  - overall: major [66] → 66
- 期待される出力:
  ```yaml
  roadmap_id: "cccccccc-cccc-cccc-cccc-cccccccccccc"
  topic: "Python"
  overall_score: 66
  items:
    - id: "aa111111-1111-1111-1111-111111111111"
      title: "基礎"
      description: ""
      level: major
      score: 66
      order: 0
      last_quiz_at: null
      children:
        - id: "aa222222-2222-2222-2222-222222222222"
          title: "データ構造"
          description: ""
          level: middle
          score: 66
          order: 0
          last_quiz_at: null
          children:
            - id: "aa333333-3333-3333-3333-333333333333"
              title: "リスト"
              description: ""
              level: detail
              score: 80
              order: 0
              last_quiz_at: null
              children: []
            - id: "aa444444-4444-4444-4444-444444444444"
              title: "辞書"
              description: ""
              level: detail
              score: 70
              order: 1
              last_quiz_at: null
              children: []
            - id: "aa555555-5555-5555-5555-555555555555"
              title: "集合"
              description: ""
              level: detail
              score: 50
              order: 2
              last_quiz_at: null
              children: []
  ```

## 例4: ロードマップ一覧取得

- 入力:
  ```yaml
  reader.find_all_roadmaps の返却値:
    - roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
      topic: "TypeScript"
      items: (例1 と同じ 9 項目)
    - roadmap_id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
      topic: "Rust"
      items: []
  ```
- 期待される出力:
  ```yaml
  items:
    - roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
      topic: "TypeScript"
      overall_score: 43
    - roadmap_id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
      topic: "Rust"
      overall_score: 0
  total_count: 2
  ```

# 主要ルール

1. reader 返却データの前提条件:
   - 条件: `RoadmapRetrievalReader` が `RoadmapRecord.items` を返す場合。
   - 振る舞い: retrieval は reader 契約を満たす整合済みの flat な `RoadmapItemRecord` 一覧を受け取る前提で動作する。欠落親、重複 `id`、`major -> middle -> detail` 以外の level 組み合わせ、`order` 重複、`children=[]` を含むツリー shorthand の検知・無視・自動親子付け・例外化は本仕様では扱わない。
2. ツリー構築:
   - 条件: `get_roadmap` がツリーを返す場合。
   - 振る舞い: `parent_id` が `None` の項目をルート（major）としてツリーのトップレベルに配置する。各項目の `children` には、`parent_id` がその項目の `id` と一致するレコードを含める。reader が返す項目の順序には依存しない。
   - 補足: `RoadmapItemRecord.parent_id` は親子関係の復元にのみ使い、reader が返した値をそのまま比較対象にする。trim・空白正規化・Unicode 正規化・大小文字変換・補完は行わない。
3. 兄弟ノードのソート:
   - 条件: ツリーノードの `children` および `RoadmapTree.items` を返す場合。
   - 振る舞い: ルート major 集合および同一親を持つ兄弟ノードを `order` 昇順でソートする。`order` の tie-break は追加せず、reader 契約で同一集合内の `order` が一意である前提で順序を一意に決定する。
4. 非集約フィールドの写像:
   - 条件: `RoadmapRecord -> RoadmapTree` / `RoadmapListItem` または `RoadmapItemRecord -> RoadmapTreeNode` を構築する場合。
   - 振る舞い: 非集約フィールドである `roadmap_id`、`topic`、`id`、`title`、`description`、`order` は reader が返した値をそのまま保持する。trim・空白正規化・Unicode 正規化・大小文字変換・補完・再採番は行わない。`parent_id` は出力 DTO には含めないが、ツリー構築時の親子判定に reader が返した値をそのまま使う。
5. detail のスコア:
   - 条件: detail レベルのツリーノードを構築する場合。
   - 振る舞い: `RoadmapItemRecord.score` の値をそのまま `RoadmapTreeNode.score` に設定する。
6. middle のスコア集約:
   - 条件: middle レベルのツリーノードを構築する場合。
   - 振る舞い: 配下の detail ノードの `score` の平均を算出し、小数点以下を切り捨てて整数にする。配下に detail が 0 件の場合は `0`。
7. major のスコア集約:
   - 条件: major レベルのツリーノードを構築する場合。
   - 振る舞い: 配下の middle ノードの `score`（ルール 6 で算出済みの整数値）の平均を算出し、小数点以下を切り捨てて整数にする。配下に middle が 0 件の場合は `0`。
8. overall_score の算出:
   - 条件: `RoadmapTree` または `RoadmapListItem` を構築する場合。
   - 振る舞い: 全 major ノードの `score`（ルール 7 で算出済みの整数値）の平均を算出し、小数点以下を切り捨てて整数にする。major が 0 件の場合は `0`。
9. last_quiz_at の設定:
   - 条件: ツリーノードを構築する場合。
   - 振る舞い: detail ノードは `RoadmapItemRecord.last_quiz_at` をそのまま設定する。major・middle ノードは `None` を設定する。
10. ロードマップ一覧の順序:
   - 条件: `list_roadmaps` が結果を返す場合。
   - 振る舞い: `reader.find_all_roadmaps` の返却順をそのまま保持する。モジュール側でソートは行わない。
11. Protocol DI による外部依存分離:
   - 条件: 読み取り操作を行う場合。
   - 振る舞い: 実装は concrete class に依存せず、`RoadmapRetrievalReader` の Protocol だけを参照する。
12. structlog による構造化ログ:
    - 条件: ロードマップ取得成功、一覧取得成功、ロードマップ未検出、外部依存エラーのいずれかが発生した場合。
    - 振る舞い: `structlog` で以下の契約どおりに構造化ログを出力する。

      | event | log level | 必須フィールド |
      | --- | --- | --- |
      | `roadmap_retrieved` | `info` | `roadmap_id`、`topic`、`overall_score`、`item_count`（全項目数） |
      | `roadmap_list_retrieved` | `info` | `total_count` |
      | `roadmap_not_found` | `warning` | `roadmap_id` |
      | `roadmap_retrieval_store_failed` | `error` | `error_type`、`get_roadmap` の場合のみ `roadmap_id` |

    - 補足: 本仕様が固定するのは `event` 名、`log level`、必須フィールドのみであり、追加キー、追加診断ログ、同一契約イベントの複数出力可否、他イベントの非出力までは規定しない。
    - 補足: `roadmap_retrieval_store_failed.error_type` の値は `exc.__class__.__name__` で得られる単純クラス名の文字列に固定する。例外オブジェクトそのもの、fully-qualified 名、`repr(exc)`、クラスオブジェクトは使用しない。

# 境界条件

- ケース: 存在しない `roadmap_id` を指定。
  - 振る舞い: `RoadmapRetrievalNotFoundError` を送出する。
  - 理由: 呼び出し元の不具合またはデータ削除を示す。
- ケース: 項目 0 件のロードマップを取得。
  - 振る舞い: `overall_score=0`、`items=[]` の `RoadmapTree` を返す。
  - 理由: 空ロードマップは `roadmap-persistence` で許容されている正常状態。
- ケース: 全 detail のスコアが 0（未着手）。
  - 振る舞い: middle、major、overall 全て `0` になる。
  - 理由: 0 の平均は 0。
- ケース: middle に detail が 0 件（CRUD で削除された結果）。
  - 振る舞い: その middle の `score=0`。
  - 理由: 子がない場合は未着手と同等に扱う。
- ケース: major に middle が 0 件（CRUD で削除された結果）。
  - 振る舞い: その major の `score=0`。
  - 理由: 子がない場合は未着手と同等に扱う。
- ケース: ロードマップが 1 件も存在しない状態で `list_roadmaps` を呼ぶ。
  - 振る舞い: `items=[]`、`total_count=0` の `RoadmapListResult` を返す。エラーにはしない。
  - 理由: 0 件は正常な検索結果。
- ケース: reader が例外を送出。
  - 振る舞い: `RoadmapRetrievalStoreError` を送出する。
  - 理由: 読み取りポートの障害を呼び出し元に通知する。
- ケース: スコア平均の端数。
  - 振る舞い: 小数点以下を切り捨て（例: (80 + 70 + 50) / 3 = 66.666... → 66）。
  - 理由: 切り捨ては決定的でテストしやすい。表示精度として整数で十分。
- ルール間の相互作用:
  1. スコア集約は detail → middle → major → overall の順に行う。各レベルで切り捨て済みの整数を上位レベルの入力とする。
  2. ツリー構築とスコア集約は reader 呼び出し後に行う。reader 失敗時はツリー構築・スコア集約を試みない。
  3. `list_roadmaps` は各ロードマップについて `get_roadmap` と同じスコア算出ロジックを適用する。

# 非機能・制約

- 性能:
  1 回の `get_roadmap` 呼び出しにつき `reader.find_roadmap` は 1 回。1 回の `list_roadmaps` 呼び出しにつき `reader.find_all_roadmaps` は 1 回。ツリー構築とスコア集約は項目数に対して線形時間。個人用ツールでロードマップ数・項目数が小規模のため十分な性能。
- 可観測性:
  構造化ログは `event`・`log level`・必須フィールドまで本仕様の契約として固定し、ロードマップ取得の `roadmap_id`・`topic`・`overall_score`・`item_count`、一覧取得の `total_count`、未検出の `roadmap_id`、失敗時の `error_type=exc.__class__.__name__` を追跡できること。
- 外部依存:
  依存先は `Protocol` で表現した `RoadmapRetrievalReader` のみ。RDB 実装の詳細はこの機能の契約に含めない。

# モジュール構成

- 構成方針: 2 モジュールに分割する
- 概算メモ:
  DTO・Protocol・例外型を `roadmap_retrieval_types.py` に分離し、ツリー構築・スコア集約・ログ出力のオーケストレーションを `roadmap_retrieval.py` にまとめる。合計約 200 行で、1 ファイルあたり 130 行以内に収まる。
- 配置先:
  `backend/roadmap/infrastructure/` に配置する。
- モジュール一覧:
  - `roadmap_retrieval_types.py`
    - 責務: DTO（`RoadmapRecord`、`RoadmapItemRecord`、`RoadmapTree`、`RoadmapTreeNode`、`RoadmapListResult`、`RoadmapListItem`）、Protocol（`RoadmapRetrievalReader`）、例外型（`RoadmapRetrievalNotFoundError`、`RoadmapRetrievalStoreError`）の定義
  - `roadmap_retrieval.py`
    - 責務: `get_roadmap` と `list_roadmaps` のオーケストレーション、ツリー構築、スコア集約、structlog 出力

# 技術判断

- 判断:
  アプリケーション側でツリー構築する。
  - 理由:
    parent_id 方式（隣接リスト）のため、全件取得してメモリ上で組み立てる。固定 3 段・小規模なので十分な性能（ADR-002 参照）。
- 判断:
  middle・major のスコアを都度算出し、DB には保持しない。
  - 理由:
    detail 項目の score が更新されるたびに上位を再計算するよりシンプル。規模が小さいので性能問題にならない。
- 判断:
  スコア平均の端数は切り捨て（floor）にする。
  - 理由:
    四捨五入（round）より結果が決定的でテストが書きやすい。表示目的の整数スコアでは実用上の差はない。
- 判断:
  スコア集約は各レベルで切り捨て後の整数を次のレベルの入力とする（段階的切り捨て）。
  - 理由:
    各レベルのスコアが独立した意味を持ち（middle は配下 detail の進捗、major は配下 middle の進捗）、テストで中間結果を検証できるため。
- 判断:
  `list_roadmaps` のソートをモジュール側で行わない。
  - 理由:
    ソート基準（作成日時、トピック名等）は presentation 層の関心。本モジュールはスコア算出に責務を限定する。

# スコープ外

- 対応しないこと: ロードマップの生成（`roadmap-persistence` の責務）
- 対応しないこと: ロードマップの更新・削除（`roadmap-item-crud` の責務）
- 対応しないこと: 欠落親・重複 `id`・不正 level 組み合わせ・`order` 重複を含む不正階層データの修復、検知、バリデーション、無視、自動親子付け、例外化
  - これらの責務は生成・更新・永続化側に属し、本機能では定義しない。
- 対応しないこと: スコアの加重平均や重み付け（単純平均を使用）
- 対応しないこと: ページネーション（個人用ツールで項目数が小規模のため不要）
- 対応しないこと: ロードマップのフィルタ検索（トピック名での検索等）
- 対応しないこと: HTTP エンドポイントの実装（presentation 層で別途実装）

# 受け入れ基準

- [ ] 受け入れ基準の正常系は reader 契約を満たす整合済みの flat `RoadmapItemRecord` 一覧のみを対象とする
- [ ] roadmap_id でロードマップがツリー構造で返る
- [ ] `RoadmapTree.items` と各 `children` が、root major 集合および各兄弟集合で `order` 一意前提の `order` 昇順で返る
- [ ] `roadmap_id`、`topic`、`id`、`title`、`description`、`order` は reader 返却値をそのまま保持し、trim・空白正規化・Unicode 正規化・大小文字変換・補完・再採番を行わない
- [ ] detail 項目の score が DB 値のまま返る
- [ ] middle のスコアが配下 detail の平均（切り捨て）で算出される
- [ ] major のスコアが配下 middle のスコアの平均（切り捨て）で算出される
- [ ] overall_score が全 major のスコアの平均（切り捨て）で算出される
- [ ] detail のみ last_quiz_at が設定され、major・middle は null
- [ ] 項目 0 件のロードマップで overall_score=0、items=[] が返る
- [ ] 存在しない roadmap_id で RoadmapRetrievalNotFoundError が発生する
- [ ] ロードマップ一覧が取得でき、各ロードマップに overall_score が含まれる
- [ ] ロードマップ 0 件で空リスト・total_count=0 が返る
- [ ] 各操作で本仕様の structlog 契約どおりに、イベント名・log level・必須フィールドが出力され、`roadmap_retrieval_store_failed.error_type` は `exc.__class__.__name__` の文字列になる
- [ ] reader 失敗時に RoadmapRetrievalStoreError が発生する
- [ ] 欠落親・重複 `id`・不正 level 組み合わせ・`order` 重複を含む不正データ時の期待結果は本仕様では新設しない

# テスト観点メモ

- 正常系:
  - reader 契約を満たす flat records の複数 major・multiple middle・multiple detail のツリー取得（例1 相当）
  - 項目 0 件のロードマップ取得
  - スコアの端数切り捨て確認（例3 相当）
  - ロードマップ一覧取得
  - reader が返す items の順序がバラバラでも、root major 集合と各兄弟集合で `order` 一意前提の `order` 昇順でツリーが正しく構築される
- 境界系:
  - 最小構成（major 1 → middle 1 → detail 1）
  - middle に detail が 0 件 → middle score = 0
  - major に middle が 0 件 → major score = 0
  - 全 detail が score=0 → 全スコア 0
  - ロードマップ 0 件で一覧取得
- 異常系:
  - 存在しない roadmap_id
  - reader.find_roadmap 例外送出
  - reader.find_all_roadmaps 例外送出
- 方針メモ:
  - 欠落親・重複 `id`・不正 level 組み合わせ・`order` 重複を含む不正データは retrieval 仕様外とし、期待結果や追加テストケースは定義しない
