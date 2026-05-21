---
feature: ingestion/ingestion-feedback
status: ready
---

# 概要

- この機能が解決する課題:
  ノート取り込みパイプラインの最終段で、取り込み済みチャンク群から「どのロードマップ項目へ反映すべきか」「記述に不正確さがないか」「何を補強すると理解が深まるか」を人手なしで整理し、後から確認できる形で DB に残す。これにより、取り込みは完了しているが学習ノートの質改善が後回しになる問題を減らす。
- 利用者・呼び出し元・前提条件:
  呼び出し元は ingestion 系のアプリケーションサービスを想定する。入力は単一 `source_path` に属するチャンク一覧であり、チャンク分割と保存対象ファイルの特定は完了済みであることを前提とする。本機能は `Protocol` による DI で注入された LLM クライアント、ロードマップ取得ポート、フィードバック永続化ポートを利用する。構造化ログ出力には `structlog` を用いる。

# 入出力

- 公開 API:
  モジュールレベル関数 `generate_for_file` を公開する。依存は引数で注入する。
  ```
  generate_for_file(
      feedback_input: IngestionFeedbackGenerateInput,
      *,
      llm_client: IngestionFeedbackLlmClient,
      roadmap_reader: RoadmapItemReader,
      writer: IngestionFeedbackWriter,
  ) -> IngestionFeedbackGenerateResult
  ```
- 入力:
  - `IngestionFeedbackGenerateInput`
    - `source_path: str`
      取り込み対象ファイルの論理パス。空文字不可。
    - `chunks: list[IngestionFeedbackChunkInput]`
      同一 `source_path` に属するチャンク一覧。入力順は任意だが、分析時は `chunk_index` 昇順に並べて扱う。
      - `chunk_index: int`
        ファイル内での 0 始まり順序。0 以上の整数でなければならない。
      - `text: str`
        チャンク本文。`strip()` 後に空文字でも受け取れるが、分析対象にはならない。
    - `minimum_chunk_characters: int`
      分析可能とみなす最小文字数。1 以上の整数。`len(text.strip()) < minimum_chunk_characters` のチャンクは分析対象から除外する。
    - `generated_at: str`
      フィードバック生成日時を表す ISO 8601 文字列。保存レコードの `created_at` にそのまま使う。
  - `IngestionFeedbackLlmRequest`
    LLM 分析に渡すリクエスト。`llm_client.analyze(...)` の引数。
    - `source_path: str`
    - `chunk_texts: list[str]`
      分析対象チャンクの本文を `chunk_index` 昇順で格納したリスト。入力の `text` をそのまま格納する（strip は行わない）。文字数しきい値判定は `len(text.strip())` で行うが、LLM に渡す本文は原文のまま。
    - `roadmap_candidates: list[RoadmapCandidate]`
      ロードマップ候補一覧。候補がない場合は空リスト。
  - `NewIngestionFeedbackRecord`
    保存用レコード。`writer.create(...)` の引数。
    - `source_path: str`
    - `roadmap_item_id: UUID | null`
    - `title: str`
    - `body: str`
    - `is_read: bool`
    - `created_at: str`
    - `read_at: str | null`
- 依存インターフェース:
    - `IngestionFeedbackLlmClient`
      `analyze(request: IngestionFeedbackLlmRequest) -> IngestionFeedbackLlmResponse` を提供する Protocol。
    - `RoadmapItemReader`
      `list_items() -> list[RoadmapCandidate]` を提供する Protocol。
      - `RoadmapCandidate`
        - `id: UUID`
        - `display_path: str`
          例: `TypeScript > 基礎 > ジェネリクス`
    - `IngestionFeedbackWriter`
      `create(record: NewIngestionFeedbackRecord) -> StoredIngestionFeedback` を提供する Protocol。
    - `structlog`
      構造化ログ出力。モジュールロガーを使い、各ログ呼び出しで `source_path` 等のキーを渡す。
- 出力:
  `IngestionFeedbackGenerateResult` を返す。
  - `status: "created" | "skipped"`
  - `used_chunk_count: int`
    実際に LLM 分析へ渡したチャンク件数。
  - `skipped_chunk_count: int`
    文字数不足で分析対象から除外したチャンク件数。
  - `created_feedback: StoredIngestionFeedback | null`
    `status="created"` のときのみ値を持つ。
    - `id: UUID`
    - `source_path: str`
    - `roadmap_item_id: UUID | null`
    - `title: str`
    - `body: str`
    - `is_read: bool`
    - `created_at: str`
    - `read_at: str | null`
  - `skip_reason: "no_analyzable_chunks" | null`
    `status="skipped"` のときのみ値を持つ。
- エラー:
  送出する例外の型名と発生条件を定義する。
  例外型はテストで使用されるため、型名を具体的に指定すること。
  実装詳細ではなく、呼び出し元との契約として記述する。
  - `IngestionFeedbackInputError`: `source_path` が空、`minimum_chunk_characters` が 1 未満、`generated_at` が ISO 8601 として扱えない、`chunk_index` が負数、同一入力内で `chunk_index` が重複する場合
  - `IngestionFeedbackRoadmapLookupError`: ロードマップ候補の取得に失敗した場合
  - `IngestionFeedbackLlmCallError`: LLM 呼び出しが失敗した場合。タイムアウト、接続失敗、モデル実行失敗を含む
  - `IngestionFeedbackResponseFormatError`: LLM 応答の必須項目が欠落している、空文字しか返さない、`selected_roadmap_item_id` が候補一覧に存在しない場合
  - `IngestionFeedbackPersistenceError`: フィードバック保存に失敗した場合

# 具体例

代表的な入力と、それに対して期待される出力をデータ例で示す。
テストケース生成やレビューで曖昧さが出ないよう、入力・出力ともに具体値で書く。

## 例1

- 入力:
  ```yaml
  source_path: "study/typescript/generics.md"
  chunks:
    - chunk_index: 1
      text: "T は型パラメータとして使え、extends で制約も付けられる。"
    - chunk_index: 0
      text: "TypeScript のジェネリクスは型安全性を保ちながら再利用可能な関数や型を表現する仕組み。"
    - chunk_index: 2
      text: "補足"
  minimum_chunk_characters: 10
  generated_at: "2026-05-20T21:30:00+09:00"
  roadmap_reader の返却値:
    - id: "11111111-1111-1111-1111-111111111111"
      display_path: "TypeScript > 基礎 > ジェネリクス"
    - id: "22222222-2222-2222-2222-222222222222"
      display_path: "TypeScript > 応用 > Conditional Types"
  llm_client の返却値:
    selected_roadmap_item_id: "11111111-1111-1111-1111-111111111111"
    accuracy_check: "ジェネリクスを型安全性の文脈で説明できており、大きな誤りはない。"
    improvement_suggestions:
      - "関数だけでなくクラスやインターフェースにも適用できる点を追記する。"
      - "型推論と明示的な型引数指定の違いを例で補う。"
  writer.create(...) の返却値:
    id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    source_path: "study/typescript/generics.md"
    roadmap_item_id: "11111111-1111-1111-1111-111111111111"
    title: "study/typescript/generics.md の取り込みフィードバック"
    body: |-
      反映先ロードマップ: TypeScript > 基礎 > ジェネリクス

      正確性チェック:
      ジェネリクスを型安全性の文脈で説明できており、大きな誤りはない。

      改善提案:
      - 関数だけでなくクラスやインターフェースにも適用できる点を追記する。
      - 型推論と明示的な型引数指定の違いを例で補う。
    is_read: false
    created_at: "2026-05-20T21:30:00+09:00"
    read_at: null
  ```
- 期待される出力:
  ```yaml
  status: "created"
  used_chunk_count: 2
  skipped_chunk_count: 1
  created_feedback:
    id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    source_path: "study/typescript/generics.md"
    roadmap_item_id: "11111111-1111-1111-1111-111111111111"
    title: "study/typescript/generics.md の取り込みフィードバック"
    body: |-
      反映先ロードマップ: TypeScript > 基礎 > ジェネリクス

      正確性チェック:
      ジェネリクスを型安全性の文脈で説明できており、大きな誤りはない。

      改善提案:
      - 関数だけでなくクラスやインターフェースにも適用できる点を追記する。
      - 型推論と明示的な型引数指定の違いを例で補う。
    is_read: false
    created_at: "2026-05-20T21:30:00+09:00"
    read_at: null
  skip_reason: null
  ```

## 例2

- 入力:
  ```yaml
  source_path: "study/docker/compose.md"
  chunks:
    - chunk_index: 0
      text: "Docker Compose では複数コンテナの起動設定をまとめて管理できる。"
  minimum_chunk_characters: 10
  generated_at: "2026-05-20T21:35:00+09:00"
  roadmap_reader の返却値: []
  llm_client の返却値:
    selected_roadmap_item_id: null
    accuracy_check: "概要説明としては妥当だが、ネットワークや volume の観点が省略されている。"
    improvement_suggestions:
      - "service 間通信の説明を 1 文追加する。"
  writer.create(...) の返却値:
    id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    source_path: "study/docker/compose.md"
    roadmap_item_id: null
    title: "study/docker/compose.md の取り込みフィードバック"
    body: |-
      正確性チェック:
      概要説明としては妥当だが、ネットワークや volume の観点が省略されている。

      改善提案:
      - service 間通信の説明を 1 文追加する。
    is_read: false
    created_at: "2026-05-20T21:35:00+09:00"
    read_at: null
  ```
- 期待される出力:
  ```yaml
  status: "created"
  used_chunk_count: 1
  skipped_chunk_count: 0
  created_feedback:
    id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    source_path: "study/docker/compose.md"
    roadmap_item_id: null
    title: "study/docker/compose.md の取り込みフィードバック"
    body: |-
      正確性チェック:
      概要説明としては妥当だが、ネットワークや volume の観点が省略されている。

      改善提案:
      - service 間通信の説明を 1 文追加する。
    is_read: false
    created_at: "2026-05-20T21:35:00+09:00"
    read_at: null
  skip_reason: null
  ```

## 例3

- 入力:
  ```yaml
  source_path: "daily/2026-05-20.md"
  chunks:
    - chunk_index: 0
      text: "会議"
    - chunk_index: 1
      text: "後で調べる"
  minimum_chunk_characters: 10
  generated_at: "2026-05-20T21:40:00+09:00"
  ```
- 期待される出力:
  ```yaml
  status: "skipped"
  used_chunk_count: 0
  skipped_chunk_count: 2
  created_feedback: null
  skip_reason: "no_analyzable_chunks"
  ```

## 例4

- 入力:
  `source_path="study/typescript/generics.md"` に対して過去の `IngestionFeedback` が 1 件保存済み。
  ```yaml
  source_path: "study/typescript/generics.md"
  chunks:
    - chunk_index: 0
      text: "ジェネリクスの基本に加えて、型引数の推論規則も追記した。"
  minimum_chunk_characters: 10
  generated_at: "2026-05-21T08:00:00+09:00"
  ```
- 期待される出力:
  ```yaml
  status: "created"
  created_feedback:
    id: "cccccccc-cccc-cccc-cccc-cccccccccccc"
    source_path: "study/typescript/generics.md"
    created_at: "2026-05-21T08:00:00+09:00"
  ```
  かつ、永続化は既存レコードの更新ではなく新規 `create(...)` で行われ、旧レコードは残る。

# 主要ルール

1. ファイル単位 1 レコード生成:
   - 条件:
     `generate_for_file(...)` が呼ばれ、分析可能チャンクが 1 件以上ある場合。
   - 振る舞い:
     同一 `source_path` の全分析対象チャンクを 1 回の LLM 分析にまとめ、保存レコードは 1 件だけ作成する。チャンクごとの個別フィードバックレコードは作成しない。
2. 文字数しきい値によるチャンク除外:
   - 条件:
     `len(text.strip()) < minimum_chunk_characters` のチャンクがある場合。
   - 振る舞い:
     当該チャンクは LLM に渡さず、`skipped_chunk_count` に加算する。他チャンクが分析可能なら処理全体は継続する。
3. 分析可能チャンク 0 件時のスキップ:
   - 条件:
     文字数しきい値適用後に分析対象チャンクが 0 件になる場合。
   - 振る舞い:
     `status="skipped"` と `skip_reason="no_analyzable_chunks"` を返す。ロードマップ取得、LLM 呼び出し、DB 保存は行わない。
4. チャンク順序の正規化:
   - 条件:
     入力 `chunks` の順序が `chunk_index` 順でない場合。
   - 振る舞い:
     LLM に渡す本文は `chunk_index` 昇順で連結する。入力順のまま連結してはならない。
5. ロードマップ候補の任意利用:
   - 条件:
     分析可能チャンクが 1 件以上ある場合。
   - 振る舞い:
     まず `RoadmapItemReader` から候補一覧を取得し、候補が 1 件以上あるときだけ LLM に候補 `id` と `display_path` を渡す。候補が 0 件の場合は反映先通知セクションを生成せず、`roadmap_item_id` は必ず `null` にする。
6. 反映先ロードマップ項目は 0 件または 1 件:
   - 条件:
     LLM が反映先候補を返す場合。
   - 振る舞い:
     保存できる `roadmap_item_id` は 1 件までとし、`selected_roadmap_item_id` は `RoadmapItemReader` が返した候補 `id` のいずれか、または `null` のみを許可する。
7. 保存本文の決定的組み立て:
   - 条件:
     LLM 応答が妥当で、保存レコードを生成する場合。
   - 振る舞い:
     `title` は常に `"{source_path} の取り込みフィードバック"` とする。`body` は次の順序で組み立てる。
     1. `roadmap_item_id` が非 `null` の場合は `反映先ロードマップ: {display_path}` を先頭に置き、その直後に空行を 1 つ入れる
     2. `正確性チェック:`
     3. `accuracy_check`
     4. 空行
     5. `改善提案:`
     6. `improvement_suggestions` を 1 行 1 件の `- ` 箇条書き
8. 新規保存のみで旧レコードを残す:
   - 条件:
     同じ `source_path` のフィードバックが過去に存在する状態で、新しい取り込み結果を処理する場合。
   - 振る舞い:
     既存フィードバックの更新・削除は行わず、新規レコードを 1 件追加保存する。
9. 保存時の既読初期値:
   - 条件:
     フィードバックを保存する場合。
   - 振る舞い:
     `is_read=false`、`read_at=null` で保存する。呼び出し元が既読状態を指定することはできない。
10. Protocol DI による外部依存分離:
    - 条件:
      LLM 呼び出し、ロードマップ取得、DB 保存を行う場合。
    - 振る舞い:
      実装は concrete class に依存せず、`IngestionFeedbackLlmClient`、`RoadmapItemReader`、`IngestionFeedbackWriter` の Protocol だけを参照する。
11. structlog による構造化ログ:
    - 条件:
      生成成功、スキップ、外部依存エラーのいずれかが発生した場合。
    - 振る舞い:
      `structlog` で構造化ログを出力する。イベント名は成功時 `ingestion_feedback_created`、スキップ時 `ingestion_feedback_skipped`、ロードマップ取得失敗時 `ingestion_feedback_roadmap_lookup_failed`、LLM 失敗時 `ingestion_feedback_llm_failed`、保存失敗時 `ingestion_feedback_persist_failed` とする。少なくとも `source_path`、`input_chunk_count`、`used_chunk_count`、`skipped_chunk_count`、`roadmap_candidate_count`、`feedback_id`、`error_type` を必要に応じて含める。

# 境界条件

- ケース:
  `chunks` が空リスト。
  - 振る舞い:
    `status="skipped"` を返す。`used_chunk_count=0`、`skipped_chunk_count=0`、`skip_reason="no_analyzable_chunks"` とする。
  - 理由:
    対象本文が存在しないため。
- ケース:
  一部のチャンクだけが文字数しきい値未満。
  - 振る舞い:
    短いチャンクだけ除外し、残りが 1 件以上あれば通常どおり 1 レコード生成する。
  - 理由:
    ファイル全体を失敗扱いにせず、分析可能な情報は活用するため。
- ケース:
  ロードマップ候補は存在するが、LLM が `selected_roadmap_item_id: null` を返す。
  - 振る舞い:
    `roadmap_item_id=null` で保存し、`body` に反映先ロードマップ行を含めない。
  - 理由:
    候補一覧が存在しても、どれにも当てはまらないノートはあり得るため。
- ケース:
  ロードマップ候補は存在するが、LLM が候補外の `selected_roadmap_item_id` を返す。
  - 振る舞い:
    `IngestionFeedbackResponseFormatError` を送出し、保存しない。
  - 理由:
    不正な FK 値や誤った通知を防ぐため。
- ケース:
  LLM が `improvement_suggestions` を空配列で返す。
  - 振る舞い:
    `IngestionFeedbackResponseFormatError` を送出し、保存しない。
  - 理由:
    本機能の契約に「改善提案を生成する」が含まれているため。
- ケース:
  同一入力内で `chunk_index` が重複する。
  - 振る舞い:
    `IngestionFeedbackInputError` を送出し、外部依存は呼び出さない。
  - 理由:
    連結順序が一意に定まらず、ファイル内容を再現できないため。
- ルール間の相互作用:
  1. 先に入力バリデーションを行い、失敗した場合は文字数判定や外部依存呼び出しに進まない。
  2. 文字数しきい値判定はロードマップ取得より先に行う。分析可能チャンクが 0 件ならロードマップ取得も LLM 呼び出しも不要だから。
  3. ロードマップ候補が 0 件のときは、LLM がどの値を返しても保存時の `roadmap_item_id` は `null` でなければならない。候補外 ID は応答形式エラーとして扱う。
  4. 再取り込み時でも、分析不能スキップが先に成立した場合は新規レコード追加は行わない。`source_path` が同じでも「新しいフィードバックを生成する」の条件は分析可能チャンクがある場合に限る。

# 非機能・制約

- 性能:
  1 ファイルにつきロードマップ取得は 1 回、LLM 呼び出しは最大 1 回、DB 保存は最大 1 回とする。チャンク前処理と連結は `chunks` 件数に対して線形時間で完了すること。
- 可観測性:
  成功・スキップ・失敗の各イベントで、少なくとも `source_path`、処理件数、スキップ件数、候補ロードマップ件数、例外型を追跡できること。ログメッセージ本文に依存せず、構造化フィールドで集計可能であること。
- 外部依存:
  依存先は `Protocol` で表現した LLM、ロードマップ取得、フィードバック保存ポートのみとする。ロードマップの具体的な保存先、RDB 実装、LLM モデル名、プロンプト文面はこの機能の契約に含めない。

# モジュール構成

design 時に、各モジュールが概ね 200-300 行に収まるかを責務単位で概算し、実装の切り方を先に決める。
厳密な計算式は不要だが、例外型・データ構造・主要ルール・バリデーション・ログなどの構成要素を踏まえて判断する。
単一ファイルで十分な場合も、その判断を明記する。

- 構成方針:
  `2モジュールに分割する`
- 概算メモ:
  型定義・Protocol・例外型を `ingestion_feedback_types.py` に分離し、オーケストレーションと純粋ロジック（チャンク選別、本文組み立て、LLM 応答検証）を `ingestion_feedback.py` にまとめる。合計約 490 行で、1 ファイルあたり 350 行以内に収まる。
- モジュール一覧:
  - `backend/ingestion/infrastructure/ingestion_feedback_types.py`
    - 責務:
      DTO、Protocol、例外型の定義
    - 含める要素:
      `IngestionFeedbackGenerateInput`、`IngestionFeedbackGenerateResult`、`RoadmapCandidate`、`IngestionFeedbackLlmResponse`、各例外型
  - `backend/ingestion/infrastructure/ingestion_feedback.py`
    - 責務:
      処理全体のオーケストレーション、入力検証、チャンク選別、本文組み立て、LLM 応答検証
    - 含める要素:
      `generate_for_file`、入力検証、ロードマップ取得、LLM 呼び出し、LLM 応答検証、body ビルダー、writer 保存、結果 DTO 生成、structlog 出力

# 技術判断

品質に直結する技術選定や実装方針がある場合は、その判断と理由を書く。

- 判断:
  フィードバック保存用 `title` は LLM に生成させず、`"{source_path} の取り込みフィードバック"` で固定する。
  - 理由:
    保存レコードの可読性を保ちながら、LLM の揺らぎを `body` の中身だけに閉じ込められるため。
- 判断:
  短いチャンクはファイル全体を失敗させず、チャンク単位で除外する。
  - 理由:
    1 ファイル 1 レコードの要件を守りつつ、「メモ断片が 1 つ混ざっただけで全体が無分析になる」挙動を避けられるため。
- 判断:
  保存本文は LLM の自由文全体をそのまま保存せず、構造化応答を受けて決定的に組み立てる。
  - 理由:
    ロードマップ通知の省略条件、正確性チェック、改善提案の各セクション有無をテストで明確に検証できるため。
- 判断:
  再取り込み時は insert-only とし、既存フィードバックを更新しない。
  - 理由:
    ノート改善の履歴を残し、「以前はどの内容に対して何が不足していたか」を後から追えるため。

# スコープ外

この機能では扱わないこと、別 issue / 別機能で扱うことを明示する。

- 対応しないこと:
  フィードバックの既読化、一覧取得、フィルタリング API
- 対応しないこと:
  フィードバックに基づくノート本文の自動修正
- 対応しないこと:
  複数ロードマップ項目への同時紐付け
- 対応しないこと:
  LLM プロンプト文面そのものの設計詳細やモデル選定

# 受け入れ基準

検証可能な条件をチェックリスト形式で書く。実装手段ではなく、満たされるべき事実を書く。

- [ ] 分析可能チャンクが 1 件以上あるファイルでは、フィードバックが 1 レコードだけ新規保存される
- [ ] 短すぎるチャンクは分析対象から除外され、全チャンクが短い場合のみ保存がスキップされる
- [ ] ロードマップ候補が 0 件のとき、保存レコードの `roadmap_item_id` は `null` で、本文に反映先ロードマップ行が含まれない
- [ ] ロードマップ候補があるとき、LLM が返した候補内 ID だけが `roadmap_item_id` として保存される
- [ ] 保存レコードは常に `is_read=false`、`read_at=null`、`created_at=generated_at` で作成される
- [ ] 同じ `source_path` の再取り込みでは旧フィードバックを残したまま新規レコードが追加される
- [ ] 成功・スキップ・失敗の各ケースで structlog のイベント名と主要フィールドが定義どおり出力される
- [ ] 具体例から期待される保存本文と戻り値を一意に判断できる

# テスト観点メモ

各主要ルールに対して最低1つ、各境界条件に対して最低1つの観点を列挙する。
受け入れ基準の各項目が少なくとも1つの観点でカバーされていることを確認する。

- 正常系:
  - ロードマップ候補ありで 1 件の候補 ID を選び、`title/body/roadmap_item_id/is_read/read_at` が期待どおり保存される
  - ロードマップ候補なしで `roadmap_item_id=null` かつ本文に反映先ロードマップ行が出ない
  - 短いチャンクを含んでも、分析可能チャンクが残る限り 1 レコード生成される
  - 同一 `source_path` の再取り込みで `writer.create(...)` が再度呼ばれ、旧レコードを更新しない
- 境界系:
  - `chunks=[]` で `status="skipped"` を返し、外部依存を呼ばない
  - 全チャンクが `minimum_chunk_characters` 未満でスキップされる
  - 入力チャンク順が乱れていても `chunk_index` 昇順で LLM へ渡される
  - ロードマップ候補ありだが `selected_roadmap_item_id=null` の場合に通知行なしで保存される
  - `minimum_chunk_characters` ちょうどの長さのチャンクは分析対象に含まれる
- 異常系:
  - `source_path=""`、負の `chunk_index`、重複 `chunk_index`、`minimum_chunk_characters=0` で `IngestionFeedbackInputError`
  - ロードマップ取得ポートの失敗で `IngestionFeedbackRoadmapLookupError`
  - LLM 呼び出し失敗で `IngestionFeedbackLlmCallError`
  - LLM が候補外 `selected_roadmap_item_id` または空の `improvement_suggestions` を返した場合に `IngestionFeedbackResponseFormatError`
  - writer 保存失敗で `IngestionFeedbackPersistenceError`
