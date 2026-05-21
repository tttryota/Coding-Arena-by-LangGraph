---
feature: roadmap/roadmap-persistence
status: ready
---

# 概要

- この機能が解決する課題:
  LLM が生成したロードマップの階層構造（JSON）を、RDB に保存可能なフラットレコード群に変換して永続化する。これにより、ツリー構造の取得・スコア算出・CRUD 操作を SQL ベースで行える。
- 利用者・呼び出し元・前提条件:
  呼び出し元はロードマップ生成フロー（B2）の後段を想定する。入力は LLM が生成した 3 段固定構造（利用可能な `level` と親子関係は `major -> middle -> detail` に固定）の JSON 構造であり、LLM 応答のパースは完了済みであることを前提とする。`major` / `middle` の `children=[]` は許容する。本機能は `Protocol` による DI で注入された永続化ポートと ID 生成ポートを利用する。構造化ログ出力には `structlog` を用いる。

# 入出力

- 公開 API:
  モジュールレベル関数を 1 つ公開する。依存は keyword-only 引数で注入する。
  ```python
  save_roadmap(
      roadmap_input: RoadmapSaveInput,
      *,
      writer: RoadmapPersistenceWriter,
      id_generator: RoadmapIdGenerator,
  ) -> RoadmapSaveResult
  ```

- 入力:
  - `RoadmapSaveInput`
    frozen dataclass。
    - `topic: str`
      ロードマップのトピック名。`strip()` 後に空文字となる値は不可。検証は `strip()` ベースで行うが、保存時の値は入力文字列をそのまま保持し、trim/strip による正規化は行わない。
    - `items: list[RoadmapItemInput]`
      ルートレベルの項目一覧。空リストの場合は項目なしのロードマップとして扱う。
    - `created_at: str`
      ロードマップ生成日時。ISO 8601 文字列かつ UTC offset 必須。全レコードの `created_at` と `updated_at` にこの値を使う。`2026-05-21T10:00:00` のような parse 可能だが offset を含まない値は不正入力として扱う。
  - `RoadmapItemInput`
    frozen dataclass。再帰構造。
    - `title: str`
      項目名。`strip()` 後に空文字となる値は不可。検証は `strip()` ベースで行うが、保存時の値は入力文字列をそのまま保持し、trim/strip による正規化は行わない。
    - `description: str`
      LLM 生成の説明文。空文字許容。
    - `level: Literal["major", "middle", "detail"]`
      階層レベル。利用可能な値は `major` / `middle` / `detail` のみであり、これ以外の値は未サポートの不正入力として扱う。
    - `children: list[RoadmapItemInput]`
      子項目一覧。3 段固定構造とは `level` の親子関係制約を指し、`major` は `middle` を 0 件以上、`middle` は `detail` を 0 件以上持てる。`detail` レベルのみ子を持てず、`children=[]` が必須である。途中階層が欠ける入力（major のみ、または major 配下の middle が `children=[]`）も許容する。

- 依存インターフェース:
  - `RoadmapPersistenceWriter`
    `save_items(roadmap_id: UUID, topic: str, items: list[FlatRoadmapItem]) -> None` を提供する Protocol。
    - 1 回の呼び出しで全項目をトランザクション的に保存する。
    - 保存失敗時は例外を送出する。
  - `RoadmapIdGenerator`
    `generate() -> UUID` を提供する Protocol。
    - roadmap_id と各項目の id を生成するために呼ばれる。
  - `structlog`
    構造化ログ出力。モジュールロガーを使い、各ログ呼び出しでコンテキスト情報を渡す。

- 出力:
  `RoadmapSaveResult` を返す。frozen dataclass。
  - `roadmap_id: UUID`
    生成されたロードマップの ID。
  - `saved_count: int`
    保存した項目の総数。

- 内部 DTO:
  - `FlatRoadmapItem`
    frozen dataclass。writer に渡すフラット化済みレコード。
    - `id: UUID`
    - `roadmap_id: UUID`
    - `parent_id: UUID | None`
      major レベルの場合は `None`。
    - `level: Literal["major", "middle", "detail"]`
    - `title: str`
    - `description: str`
    - `order: int`
      同一親の子項目内での 0 始まりの表示順。入力の `items` / `children` リストの出現順に対応する。
    - `score: int`
      初期値は常に `0`。
    - `created_at: str`
    - `updated_at: str`

- エラー:
  - `RoadmapPersistenceInputError`: `topic` または `title` が `strip()` 後に空文字、`created_at` が ISO 8601 として解析できない、または UTC offset を含まない、`level` が `major` / `middle` / `detail` 以外である、または 3 段固定構造（`major -> middle -> detail` の `level` 親子関係と `detail.children=[]` 必須）を満たさない場合。
  - `RoadmapPersistenceWriteError`: 永続化ポートの操作が失敗した場合。元例外を `raise ... from ...` で保持して送出する。

# 具体例

## 例1: 基本的な 3 段階層

- 入力:
  ```yaml
  topic: "TypeScript"
  items:
    - title: "基礎"
      description: "TypeScript の基本概念"
      level: major
      children:
        - title: "変数と型"
          description: "型システムの基礎"
          level: middle
          children:
            - title: "プリミティブ型"
              description: "string, number, boolean 等の基本型"
              level: detail
              children: []
            - title: "配列とタプル"
              description: "配列型とタプル型の使い分け"
              level: detail
              children: []
        - title: "関数"
          description: "関数の型付けと引数"
          level: middle
          children:
            - title: "引数の型注釈"
              description: "パラメータと戻り値の型指定"
              level: detail
              children: []
    - title: "応用"
      description: "TypeScript の応用技術"
      level: major
      children:
        - title: "ジェネリクス"
          description: "型パラメータによる汎用化"
          level: middle
          children:
            - title: "基本構文"
              description: "T extends U の基本"
              level: detail
              children: []
  created_at: "2026-05-21T10:00:00+09:00"
  id_generator の返却値（呼び出し順）:
    - "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"  # roadmap_id
    - "11111111-1111-1111-1111-111111111111"  # 基礎
    - "22222222-2222-2222-2222-222222222222"  # 変数と型
    - "33333333-3333-3333-3333-333333333333"  # プリミティブ型
    - "44444444-4444-4444-4444-444444444444"  # 配列とタプル
    - "55555555-5555-5555-5555-555555555555"  # 関数
    - "66666666-6666-6666-6666-666666666666"  # 引数の型注釈
    - "77777777-7777-7777-7777-777777777777"  # 応用
    - "88888888-8888-8888-8888-888888888888"  # ジェネリクス
    - "99999999-9999-9999-9999-999999999999"  # 基本構文
  ```
- writer.save_items に渡される引数:
  ```yaml
  roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
  topic: "TypeScript"
  items:
    - id: "11111111-1111-1111-1111-111111111111"
      roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
      parent_id: null
      level: major
      title: "基礎"
      description: "TypeScript の基本概念"
      order: 0
      score: 0
      created_at: "2026-05-21T10:00:00+09:00"
      updated_at: "2026-05-21T10:00:00+09:00"
    - id: "22222222-2222-2222-2222-222222222222"
      roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
      parent_id: "11111111-1111-1111-1111-111111111111"
      level: middle
      title: "変数と型"
      description: "型システムの基礎"
      order: 0
      score: 0
      created_at: "2026-05-21T10:00:00+09:00"
      updated_at: "2026-05-21T10:00:00+09:00"
    - id: "33333333-3333-3333-3333-333333333333"
      roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
      parent_id: "22222222-2222-2222-2222-222222222222"
      level: detail
      title: "プリミティブ型"
      description: "string, number, boolean 等の基本型"
      order: 0
      score: 0
      created_at: "2026-05-21T10:00:00+09:00"
      updated_at: "2026-05-21T10:00:00+09:00"
    - id: "44444444-4444-4444-4444-444444444444"
      roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
      parent_id: "22222222-2222-2222-2222-222222222222"
      level: detail
      title: "配列とタプル"
      description: "配列型とタプル型の使い分け"
      order: 1
      score: 0
      created_at: "2026-05-21T10:00:00+09:00"
      updated_at: "2026-05-21T10:00:00+09:00"
    - id: "55555555-5555-5555-5555-555555555555"
      roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
      parent_id: "11111111-1111-1111-1111-111111111111"
      level: middle
      title: "関数"
      description: "関数の型付けと引数"
      order: 1
      score: 0
      created_at: "2026-05-21T10:00:00+09:00"
      updated_at: "2026-05-21T10:00:00+09:00"
    - id: "66666666-6666-6666-6666-666666666666"
      roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
      parent_id: "55555555-5555-5555-5555-555555555555"
      level: detail
      title: "引数の型注釈"
      description: "パラメータと戻り値の型指定"
      order: 0
      score: 0
      created_at: "2026-05-21T10:00:00+09:00"
      updated_at: "2026-05-21T10:00:00+09:00"
    - id: "77777777-7777-7777-7777-777777777777"
      roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
      parent_id: null
      level: major
      title: "応用"
      description: "TypeScript の応用技術"
      order: 1
      score: 0
      created_at: "2026-05-21T10:00:00+09:00"
      updated_at: "2026-05-21T10:00:00+09:00"
    - id: "88888888-8888-8888-8888-888888888888"
      roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
      parent_id: "77777777-7777-7777-7777-777777777777"
      level: middle
      title: "ジェネリクス"
      description: "型パラメータによる汎用化"
      order: 0
      score: 0
      created_at: "2026-05-21T10:00:00+09:00"
      updated_at: "2026-05-21T10:00:00+09:00"
    - id: "99999999-9999-9999-9999-999999999999"
      roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
      parent_id: "88888888-8888-8888-8888-888888888888"
      level: detail
      title: "基本構文"
      description: "T extends U の基本"
      order: 0
      score: 0
      created_at: "2026-05-21T10:00:00+09:00"
      updated_at: "2026-05-21T10:00:00+09:00"
  ```
- 期待される出力:
  ```yaml
  roadmap_id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
  saved_count: 9
  ```

## 例2: 空のロードマップ

- 入力:
  ```yaml
  topic: "Rust"
  items: []
  created_at: "2026-05-21T10:30:00+09:00"
  id_generator の返却値:
    - "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"  # roadmap_id
  ```
- writer.save_items に渡される引数:
  ```yaml
  roadmap_id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
  topic: "Rust"
  items: []
  ```
- 期待される出力:
  ```yaml
  roadmap_id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
  saved_count: 0
  ```

# 主要ルール

1. 階層レベルの検証:
   - 条件: 入力を処理する場合。
   - 振る舞い: 各項目の `level` は `major` / `middle` / `detail` のいずれかでなければならず、これ以外の値は `RoadmapPersistenceInputError` を送出する。加えて、3 段固定構造としてルート項目は `level=major`、major の子は `level=middle`、middle の子は `level=detail` でなければならない。detail は `children` が空リストでなければならない。major / middle は `children` が空リストでも許容する。3 段固定構造の強制は入力の `level` 属性の親子関係と `detail.children=[]` 制約に対してのみ行う。
2. 文字列入力の検証:
   - 条件: `topic` と各項目 `title` を検証する場合。
   - 振る舞い: `topic` と `title` は `strip()` 後に 1 文字以上を含まなければならない。検証通過後も保存値は入力文字列をそのまま保持し、trim/strip による正規化は行わない。
3. created_at の検証:
   - 条件: `created_at` を検証する場合。
   - 振る舞い: `created_at` は ISO 8601 として解析可能で、かつ UTC offset を含まなければならない。offset を欠く値は parse 可能でも `RoadmapPersistenceInputError` を送出する。
4. DFS 順のフラット化:
   - 条件: 階層構造をフラット化する場合。
   - 振る舞い: 深さ優先探索（pre-order）で項目を走査し、`FlatRoadmapItem` のリストを構築する。走査順序は入力の `items` / `children` リストの出現順に従う。
5. order の決定:
   - 条件: `FlatRoadmapItem.order` を設定する場合。
   - 振る舞い: 同一親の子項目内での 0 始まりの連番。入力リストの出現順に対応する。
6. parent_id の設定:
   - 条件: `FlatRoadmapItem.parent_id` を設定する場合。
   - 振る舞い: major レベルの項目は `parent_id=None`。middle は親 major の `id`。detail は親 middle の `id`。
7. ID 生成:
   - 条件: roadmap_id と各項目 id を生成する場合。
   - 振る舞い: `id_generator.generate()` を呼ぶ。最初の呼び出しで `roadmap_id` を取得し、以降の呼び出しで各項目の `id` を DFS 順に取得する。
8. score の初期化:
   - 条件: `FlatRoadmapItem` を生成する場合。
   - 振る舞い: `score` は常に `0` で初期化する。入力から score を受け取らない。
9. created_at / updated_at の設定:
   - 条件: `FlatRoadmapItem` を生成する場合。
   - 振る舞い: 全レコードの `created_at` と `updated_at` に入力の `created_at` をそのまま使う。
10. 空ロードマップの許容:
   - 条件: `items` が空リストの場合。
   - 振る舞い: `roadmap_id` を生成し、`writer.save_items` に空リストを渡す。`saved_count=0` を返す。
11. Protocol DI による外部依存分離:
   - 条件: 永続化操作と ID 生成を行う場合。
   - 振る舞い: 実装は concrete class に依存せず、`RoadmapPersistenceWriter` と `RoadmapIdGenerator` の Protocol だけを参照する。
12. structlog による構造化ログ:
   - 条件: 保存成功、または外部依存エラーが発生した場合。
   - 振る舞い: `structlog` で構造化ログを出力する。イベント名は保存成功時 `roadmap_persisted`、永続化失敗時 `roadmap_persistence_failed` とする。
      - `roadmap_persisted`: `roadmap_id`、`topic`、`saved_count`
      - `roadmap_persistence_failed`: `topic`、`error_type`
    - 補足: `writer.save_items` が例外を送出した場合は、その元例外を `raise RoadmapPersistenceWriteError(...) from original_error` でラップする。`roadmap_persistence_failed.error_type` には wrapper 例外名ではなく元例外のクラス名を記録する。

# 境界条件

- ケース: `items` が空リスト。
  - 振る舞い: `roadmap_id` のみ生成し、項目なしで `writer.save_items` を呼ぶ。`saved_count=0`。
  - 理由: 手動で項目を追加するユースケースに対応。
- ケース: major 項目が 1 つだけ、detail まで 1 項目ずつの最小構成。
  - 振る舞い: 3 レコード（major, middle, detail）を保存する。
  - 理由: 最小有効構成。
- ケース: major が `children=[]`。
  - 振る舞い: 正常に保存する。major 1 レコードのみ。
  - 理由: 3 段固定構造は `level` の親子関係のみを制約し、major の空 children は許容する。
- ケース: middle が `children=[]`。
  - 振る舞い: 正常に保存する。major + middle のレコードのみ。
  - 理由: 3 段固定構造は `level` の親子関係のみを制約し、middle の空 children は許容する。
- ケース: detail が children を持つ。
  - 振る舞い: `RoadmapPersistenceInputError` を送出する。
  - 理由: 4 段以上の階層は許可しない。
- ケース: `level` が `major` / `middle` / `detail` 以外。
  - 振る舞い: `RoadmapPersistenceInputError` を送出する。
  - 理由: 利用可能な階層レベルは 3 種類に限定する。
- ケース: ルート項目が `level=middle` または `level=detail`。
  - 振る舞い: `RoadmapPersistenceInputError` を送出する。
  - 理由: ルートは major のみ。
- ケース: major の直下に detail がある（middle をスキップ）。
  - 振る舞い: `RoadmapPersistenceInputError` を送出する。
  - 理由: 3 段固定構造の `level` 親子関係に違反。
- ケース: `topic` が空文字。
  - 振る舞い: `RoadmapPersistenceInputError` を送出する。
  - 理由: ロードマップの識別に必要。
- ケース: `topic` が空白のみ、または `title` が空白のみ。
  - 振る舞い: `RoadmapPersistenceInputError` を送出する。
  - 理由: `strip()` 後に空文字となる値は識別に使えない。
- ケース: `title` が空文字の項目がある。
  - 振る舞い: `RoadmapPersistenceInputError` を送出する。
  - 理由: 項目の識別に必要。
- ケース: `created_at` が ISO 8601 として parse 可能だが UTC offset を含まない。
  - 振る舞い: `RoadmapPersistenceInputError` を送出する。
  - 理由: 全レコードに offset 付きタイムスタンプを保持する入力契約に違反する。
- ルール間の相互作用:
  1. 入力バリデーション（階層レベル、`topic` / `title` の `strip()` ベース検証、`created_at` の offset 必須チェック）はフラット化より先に行う。不正な入力で `id_generator` や `writer` を呼ばない。
  2. 正常入力でバリデーション通過後、`id_generator` は `roadmap_id` 用に 1 回、項目数分呼ばれる。空ロードマップでは 1 回のみ。
  3. 正常入力でバリデーション通過後、`writer.save_items` は 1 回だけ呼ばれる（空リストでも呼ぶ）。
  4. `writer.save_items` が失敗した場合は、元例外を cause として保持した `RoadmapPersistenceWriteError` を送出し、失敗ログの `error_type` には元例外のクラス名を記録する。

# 非機能・制約

- 性能:
  1 回の `save_roadmap` 呼び出しにつき `writer.save_items` は 1 回。`id_generator.generate()` は `1 + 項目数` 回。フラット化は項目数に対して線形時間。
- 可観測性:
  保存成功時の `roadmap_id`、`topic`、`saved_count`、失敗時の `error_type` を構造化フィールドで追跡できること。
- 外部依存:
  依存先は `Protocol` で表現した `RoadmapPersistenceWriter` と `RoadmapIdGenerator` のみ。RDB 実装や UUID ライブラリの詳細はこの機能の契約に含めない。

# モジュール構成

- 構成方針: 2 モジュールに分割する
- 概算メモ:
  DTO・Protocol・例外型を `roadmap_persistence_types.py` に分離し、入力バリデーション・フラット化・writer 呼び出しのオーケストレーションを `roadmap_persistence.py` にまとめる。合計約 200 行で、1 ファイルあたり 130 行以内に収まる。
- 配置先:
  `backend/roadmap/infrastructure/` に配置する。
- モジュール一覧:
  - `roadmap_persistence_types.py`
    - 責務: DTO（`RoadmapSaveInput`、`RoadmapItemInput`、`FlatRoadmapItem`、`RoadmapSaveResult`）、Protocol（`RoadmapPersistenceWriter`、`RoadmapIdGenerator`）、例外型の定義
  - `roadmap_persistence.py`
    - 責務: `save_roadmap` のオーケストレーション、階層バリデーション、DFS フラット化、structlog 出力

# 技術判断

- 判断:
  parent_id 方式（隣接リスト）で階層を表現する。
  - 理由:
    固定 3 段で項目数も小規模のため、シンプルな隣接リストで十分（ADR-002 参照）。
- 判断:
  フラット化は DFS pre-order で行う。
  - 理由:
    入力の構造順序を保ちつつ、テストで一意に検証可能な走査順序を固定するため。
- 判断:
  ID 生成を Protocol で外部注入する。
  - 理由:
    テストで ID の生成順序を固定でき、フラット化結果を一意に検証できるため。
- 判断:
  `created_at` を外部注入する。
  - 理由:
    ingestion-feedback の `generated_at` と同じパターン。テスタビリティを確保する。

# スコープ外

- 対応しないこと: ロードマップの削除
- 対応しないこと: ロードマップ間のマージ
- 対応しないこと: 既存ロードマップの更新（常に新規保存）
- 対応しないこと: LLM 応答のパース（入力は変換済みの DTO を前提）
- 対応しないこと: score の計算・更新

# 受け入れ基準

- [ ] 3 段固定構造（`major -> middle -> detail` の `level` 親子関係）に沿う JSON 構造が `FlatRoadmapItem` レコード群に正しく変換される
- [ ] 親子関係が `parent_id` で正しく表現される
- [ ] 同階層内の順序が `order`（0 始まり連番）で保持される
- [ ] 初期 `score` が `0` で設定される
- [ ] 全レコードの `created_at` と `updated_at` が入力の `created_at` と一致する
- [ ] `roadmap_id` で全項目が紐付けられる
- [ ] 空ロードマップ（`items=[]`）が正常に処理される
- [ ] major のみ（`children=[]`）や major→middle のみが正常に処理される
- [ ] 階層レベルの不整合がエラーになる
- [ ] 保存成功・失敗で構造化ログが出力される

# テスト観点メモ

- 正常系:
  - 3 段固定構造の完全な変換（例1 相当）
  - 空ロードマップの処理
  - 複数 major 項目、各 major に複数 middle
  - order の連番確認
  - parent_id の正しい紐付け
- 境界系:
  - 最小構成（major 1 → middle 1 → detail 1）
  - major のみ（children=[]）→ 正常保存
  - major→middle のみ（middle の children=[]）→ 正常保存
  - description が空文字
  - `topic` / `title` が前後空白を含むが、`strip()` 後は空でない
- 異常系:
  - topic が空文字
  - topic / title が空白のみ
  - title が空文字
  - created_at が offset なし
  - `level` が `major` / `middle` / `detail` 以外
  - ルートが middle/detail
  - major 直下に detail
  - detail に children がある
  - writer 保存失敗
