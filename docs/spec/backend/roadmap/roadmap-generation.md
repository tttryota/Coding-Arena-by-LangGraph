---
feature: roadmap-generation
status: ready
---

## 機能概要

ユーザーが選択したトピックに対して、LLM がコーディング実践ロードマップを一括生成する。`major`（学習段階）→ `middle`（実装カテゴリ）→ `detail`（演習ユニット）の 3 階層で、各 `detail` は1つの実装目標を持ち、段階的なコーディング演習に分解可能な粒度とする。全枝が必ず 3 層に到達することまでは要求せず、`major.children=[]` と `middle.children=[]` は許容する。生成は非同期ジョブとして受け付け、完了後はジョブ状態取得 API で `roadmap_id` を確認し、既存 B5 の retrieval で生成結果を参照する。

## モジュール構成

- 公開 API と必須の内部 worker entry は `backend/roadmap/infrastructure/roadmap_generation.py` に置く。
- DTO / Protocol / 例外 / 状態型は `backend/roadmap/infrastructure/roadmap_generation_types.py` に置く。
- `backend/roadmap/infrastructure/roadmap_generation.py` には、公開 API に加えて次の内部関数を必ず定義する。
  ```python
  _run_roadmap_generation_job(
      job_id: UUID,
      topic: str,
      *,
      llm_client: RoadmapGenerationLlmClient,
      persistence: RoadmapGenerationPersistencePort,
      job_store: RoadmapGenerationJobStatusStore,
      clock: RoadmapGenerationClock,
  ) -> None
  ```
- この関数は internal worker entry であり、外部公開 API ではない。存在、正確な関数名、引数順、依存注入を keyword-only にすること、戻り値 `None` は本仕様の必須契約とする。
- 別ファイルへの分割、scheduler からの起動方法、composition root の配線、ジョブキュー製品固有の adapter 構成、HTTP endpoint への露出方法は本仕様の対象外とする。

## 公開 DTO / 失敗コード

- `backend/roadmap/infrastructure/roadmap_generation_types.py` には、公開 API と `RoadmapGenerationJobStatusStore` がやり取りする公開 DTO を `TypedDict`、失敗コード型を `Literal[...]` として定義する。公開 DTO を `dataclass` や属性アクセス前提のオブジェクトとして定義してはならない。
- 呼び出し側、job store 実装、test double は公開 DTO を辞書互換値として扱い、`result["status"]`、`result["roadmap_id"]`、`result["error_code"]` のようにキー参照で読む前提に固定する。`result.status` のような属性アクセスは公開契約に含めない。
- `RoadmapGenerationFailureCode` は次の `Literal[...]` で一意に定義し、`RoadmapGenerationFailedStatus.error_code` と `RoadmapGenerationJobStatusStore.mark_failed()` の両方で同じ型を共有する。
  ```python
  RoadmapGenerationFailureCode = Literal[
      "schedule_failed",
      "llm_request_failed",
      "llm_json_parse_failed",
      "llm_schema_validation_failed",
      "persistence_failed",
  ]
  ```
- `RoadmapGenerationAccepted` は受付 API 専用の `TypedDict` とし、`job_id: UUID` と `status: Literal["queued"]` だけを持つ。
- ジョブ状態 DTO は状態別 `TypedDict` の判別 union として定義し、`RoadmapGenerationJobStatus` は次の 4 型の union に固定する。
  - `RoadmapGenerationQueuedStatus(TypedDict)`: `status: Literal["queued"]`
  - `RoadmapGenerationRunningStatus(TypedDict)`: `status: Literal["running"]`
  - `RoadmapGenerationCompletedStatus(TypedDict)`: `status: Literal["completed"]`、`roadmap_id: UUID`
  - `RoadmapGenerationFailedStatus(TypedDict)`: `status: Literal["failed"]`、`error_code: RoadmapGenerationFailureCode`、`error_message: str`
- `RoadmapGenerationJobStatus` は `RoadmapGenerationQueuedStatus | RoadmapGenerationRunningStatus | RoadmapGenerationCompletedStatus | RoadmapGenerationFailedStatus` とし、`RoadmapGenerationJobStatusStore.get_job()` もこの union のいずれかを返す。

## 公開 API

- モジュールレベル関数を 2 つ公開する。依存は keyword-only 引数で注入する。
  ```python
  request_roadmap_generation(
      topic: str,
      *,
      job_id_generator: RoadmapGenerationJobIdGenerator,
      scheduler: RoadmapGenerationJobScheduler,
      job_store: RoadmapGenerationJobStatusStore,
  ) -> RoadmapGenerationAccepted

  get_roadmap_generation_job(
      job_id: UUID,
      *,
      job_store: RoadmapGenerationJobStatusStore,
  ) -> RoadmapGenerationJobStatus
  ```
- `request_roadmap_generation` はトピック入力を検証し、ジョブを `queued` として登録してから非同期実行を依頼する受付 API とする。
- `request_roadmap_generation` の戻り値は前節で定義した `TypedDict` の `RoadmapGenerationAccepted` とし、必須フィールドは `job_id: UUID` と `status: Literal["queued"]` のみとする。受付時点では `roadmap_id` は返さない。
- `get_roadmap_generation_job` はジョブ状態観測 API とする。`RoadmapGenerationJobStatus` は前節で定義した `TypedDict` union であり、返却形状は以下に固定する。
  - `queued`: `status: Literal["queued"]` のみを返す。
  - `running`: `status: Literal["running"]` のみを返す。
  - `completed`: `status: Literal["completed"]` と `roadmap_id: UUID` を必須で返す。
  - `failed`: `status: Literal["failed"]` と `error_code: RoadmapGenerationFailureCode` と `error_message: str` を必須で返す。
- `queued` / `running` / `completed` では `error_code` / `error_message` を返してはならない。`queued` / `running` / `failed` では `roadmap_id` を返してはならない。
- 呼び出し元は `completed` で返却された `roadmap_id` を使い、既存 B5 の retrieval 仕様でロードマップ本体を取得する。ジョブ状態 DTO にロードマップ本体は含めない。
- `get_roadmap_generation_job` が未知の `job_id` を受け取った場合は `RoadmapGenerationJobNotFoundError` を送出する。
- HTTP endpoint、UI 表示方式、通知方式、キャンセル、進捗率表示、ジョブキュー製品名は本仕様の対象外とする。

## 例外定義

- `roadmap_generation_types.py` に以下の例外階層を定義する。
- `RoadmapGenerationError(Exception)` — 全 generation 例外の基底クラス。
  - `RoadmapGenerationInputError(RoadmapGenerationError)` — `topic` の入力不正。
  - `RoadmapGenerationScheduleError(RoadmapGenerationError)` — `scheduler.enqueue_roadmap_generation()` の失敗。
  - `RoadmapGenerationLlmError(RoadmapGenerationError)` — LLM 呼び出し自体の失敗（通信・タイムアウト等）。
  - `RoadmapGenerationJobStoreError(RoadmapGenerationError)` — `job_store` メソッドの永続化・取得失敗。
  - `RoadmapGenerationJobNotFoundError(RoadmapGenerationError)` — 未知の `job_id`。
  - `RoadmapGenerationLlmResponseError(RoadmapGenerationError)` — worker 内部で使う LLM 応答不正の基底。
    - `RoadmapGenerationJsonParseError(RoadmapGenerationLlmResponseError)` — JSON パース失敗。
    - `RoadmapGenerationSchemaValidationError(RoadmapGenerationLlmResponseError)` — スキーマバリデーション失敗。
- worker の retry ループは `RoadmapGenerationLlmResponseError` を catch して retry し、予算を使い切ったら最後にキャッチした例外の型で `error_code` を決定する（`RoadmapGenerationJsonParseError` → `"llm_json_parse_failed"`、`RoadmapGenerationSchemaValidationError` → `"llm_schema_validation_failed"`）。

## ログ定義

- `roadmap_generation.py` は `logger = structlog.get_logger(__name__)` でロガーを取得する。
- イベント名定数は `EVENT_*` パターンでモジュールレベルに定義する。
- 定義するイベントと必須フィールド:
  - `EVENT_ACCEPTED = "roadmap_generation_accepted"` — info。受付成功時。必須: `job_id`, `topic`。
  - `EVENT_INPUT_REJECTED = "roadmap_generation_input_rejected"` — warning。入力不正時。必須: `error_type`。
  - `EVENT_SCHEDULE_FAILED = "roadmap_generation_schedule_failed"` — error。enqueue 失敗時。`logger.exception()` でスタックトレース記録。必須: `job_id`, `error_type`。
  - `EVENT_JOB_STARTED = "roadmap_generation_job_started"` — info。worker 開始時（`mark_running` 成功後）。必須: `job_id`, `topic`。
  - `EVENT_LLM_RETRY = "roadmap_generation_llm_retry"` — warning。LLM 応答不正で retry する時。必須: `job_id`, `attempt`, `error_type`。
  - `EVENT_JOB_COMPLETED = "roadmap_generation_job_completed"` — info。worker 成功時。必須: `job_id`, `roadmap_id`。
  - `EVENT_JOB_FAILED = "roadmap_generation_job_failed"` — error。worker 失敗終端時（`mark_failed` 成功後）。`logger.exception()` でスタックトレース記録。必須: `job_id`, `error_code`, `error_type`。

## 依存 Protocol

- `RoadmapGenerationJobIdGenerator`
  `generate() -> UUID` を提供する Protocol。`request_roadmap_generation` が受付用 `job_id` を生成するために 1 回呼ぶ。
- `RoadmapGenerationJobScheduler`
  `enqueue_roadmap_generation(job_id: UUID, topic: str) -> None` を提供する Protocol。
  - `request_roadmap_generation` から呼ばれる。
  - 送出例外は `RoadmapGenerationScheduleError`。
  - 非同期実行基盤の内部実装、再配信、ワーカー登録方法は本仕様の対象外とする。
- `RoadmapGenerationJobStatusStore`
  以下を提供する Protocol。
  - `create_queued_job(job_id: UUID, topic: str) -> None`
  - `mark_running(job_id: UUID) -> None`
  - `mark_completed(job_id: UUID, roadmap_id: UUID) -> None`
  - `mark_failed(job_id: UUID, error_code: RoadmapGenerationFailureCode, error_message: str) -> None`
  - `get_job(job_id: UUID) -> RoadmapGenerationJobStatus`
  - 永続化・取得失敗時は `RoadmapGenerationJobStoreError`、未知の `job_id` 取得時は `RoadmapGenerationJobNotFoundError` を送出する。
  - generation モジュールは各 store メソッドから受けた `RoadmapGenerationJobStoreError` をラップせず、そのまま送出する。
- `RoadmapGenerationLlmClient`
  `generate_roadmap_json(topic: str) -> str` を提供する Protocol。
  - 返り値は JSON 文字列そのものとし、JSON パースとスキーマ検証は generation worker 側で行う。
  - 通信失敗、タイムアウト、認証失敗などの LLM 呼び出し失敗時は `RoadmapGenerationLlmError` を送出する。
- `RoadmapGenerationPersistencePort`
  `save_roadmap(roadmap_input: RoadmapSaveInput) -> RoadmapSaveResult` を提供する Protocol。
  - B3 `roadmap-persistence.md` の保存入口を generation モジュールから呼ぶための境界とする。
  - `RoadmapPersistenceInputError` または `RoadmapPersistenceWriteError` を送出しうる。
- `RoadmapGenerationClock`
  `now() -> str` を提供する Protocol。
  - `RoadmapSaveInput.created_at` に変換なしでそのまま渡せる、UTC offset 必須の ISO 8601 文字列を返す。
  - UTC offset を含まない文字列はこの Protocol 契約に違反する値であり、generation worker が許容して persistence に渡すケースは本仕様に含めない。
  - generation worker は保存 1 回につき 1 回だけ呼ぶ。

## 入力契約

- `request_roadmap_generation` の `topic` は `strip()` 後に空文字となる値を不正入力とし、`RoadmapGenerationInputError` を送出する。この判定は `job_id_generator.generate()` より前に行う。
- 上記の不正入力時は受付を開始せず、`job_id_generator.generate()`、`job_store.create_queued_job()`、`scheduler.enqueue_roadmap_generation()` をいずれも 0 回呼び出す。
- 検証通過後の `topic` は入力文字列をそのまま保持する。trim / Unicode 正規化 / 大小文字変換 / 自動補正は行わない。
- LLM への入力、内部 DTO、B3 `RoadmapSaveInput.topic` には同一の元文字列を渡す。

## 振る舞い

### 基本動作

- `request_roadmap_generation` は最初に `topic` を入力検証し、検証成功時にのみ `job_id` を採番する。その後 `job_store.create_queued_job()` で状態を `queued` として記録し、`scheduler.enqueue_roadmap_generation(job_id, topic)` を呼んで受付を完了する。
- `request_roadmap_generation` が入力検証で `RoadmapGenerationInputError` を送出する場合、`job_id_generator.generate()`、`job_store.create_queued_job()`、`scheduler.enqueue_roadmap_generation()` はいずれも呼ばない。
- `request_roadmap_generation` で `job_store.create_queued_job()` が `RoadmapGenerationJobStoreError` を送出した場合、その例外をそのまま送出し、`scheduler.enqueue_roadmap_generation()` は呼ばない。
- `request_roadmap_generation` で `job_store.create_queued_job()` 成功後に `scheduler.enqueue_roadmap_generation(job_id, topic)` が `RoadmapGenerationScheduleError` を送出した場合、generation モジュールは `RoadmapGenerationFailureCode` の値 `schedule_failed` で `job_store.mark_failed(job_id, "schedule_failed", str(exc))` を試みる。
- 上記の enqueue 失敗時に `job_store.mark_failed()` が成功した場合、`request_roadmap_generation` は元の `RoadmapGenerationScheduleError` をそのまま再送出する。`job_store.mark_failed()` が `RoadmapGenerationJobStoreError` を送出した場合は、その store 例外を優先して送出し、元の `RoadmapGenerationScheduleError` は再送出しない。受付は成功扱いにしない。
- 上記の enqueue 失敗時にジョブ削除、キャンセル、再 enqueue、ジョブキュー製品固有の補償処理は行わない。これらは本仕様の対象外とする。
- `get_roadmap_generation_job` は `job_store.get_job(job_id)` を呼び、`RoadmapGenerationJobStoreError` と `RoadmapGenerationJobNotFoundError` をラップせずそのまま送出する。
- 非同期 worker entry `_run_roadmap_generation_job(job_id, topic, *, llm_client, persistence, job_store, clock)` は開始時に `job_store.mark_running(job_id)` を呼び、その後 LLM 生成、応答検証、B3 への保存、完了状態反映を行う。
- worker 開始時の `job_store.mark_running()` が `RoadmapGenerationJobStoreError` を送出した場合、worker はその例外をそのまま送出して終了し、LLM 呼び出し、永続化、`mark_failed()` は行わない。
- 生成されたロードマップは generation モジュールから B3 の永続化入口を経由して RDB（SQLite）に永続化される。generation モジュールが SQLite を直接操作してはならない。

### 大枠の構造（必須ルール）

大枠は全トピック共通で以下の 2 段階を固定し、LLM 応答 JSON のルート `items` にこの順序で必ず 2 件だけ含まれる:

- **基礎**: 基本的なコーディングスキルを身につけるための演習ユニット群
- **応用**: 実践的な実装パターンを習得するための演習ユニット群

### LLM に委ねる部分

- 中枠の分類（トピックの性質に応じて自由に構成）
- 演習ユニット(detail)の内容
- 何を基礎、何を応用に分類するか
- `major.children` 内の `middle` 同士、および `middle.children` 内の `detail` 同士の sibling 順序（前提知識の依存関係に従う）
- generation モジュールは、妥当と判定した LLM 応答の sibling 配列順を検証、内部 DTO 化、`RoadmapSaveInput` 変換までそのまま保持し、独自の並べ替えを行わない

### LLM へのプロンプト制約

- 大枠は「基礎」「応用」の 2 段階であること
- 前の項目が後の項目の前提知識になる順序であること
- 各演習ユニット(detail)は1つの実装目標を持ち、以下の5段階のコーディング演習に分解可能な粒度であること: rewrite(書き換え) → fill_blank(穴埋め) → bug_fix(バグ修正) → extend(機能追加) → implement(自力実装)
- 各項目には `title` と `description` を含めること。`detail` の `description` は「何を実装できるようになるか」を書く。`major` / `middle` の `description` は分類の説明で良い

### 演習ユニットの粒度（ワンショット例をプロンプトに含める）

```
悪い例:
  title: "ジェネリクス"
  → 5段階の演習に分解すると各段階の範囲が広すぎる（基本構文、型制約、ユースケース、条件型連携...）

良い例:
  title: "ジェネリクスの基本構文と型パラメータ"
  title: "ジェネリクスの型制約とextends"
  title: "ジェネリクスとユーティリティ型の組み合わせ"
  → それぞれ1つの実装目標に絞られ、rewrite〜implementの段階的演習に分解可能
```

## LLM 応答バリデーション

- LLM 応答不正に対する generation モジュール内の再試行回数は、総試行回数最大 3 回（初回 1 回 + 再試行 2 回）に固定する。
- LLM 応答は JSON 文字列として受け取り、worker 側で `json.loads` 相当のパースを行う。
- ルートオブジェクトの必須フィールドは `topic` と `items` のみとする。余剰フィールドはエラーとする。
- ルート `topic` は入力 `topic` と完全一致しなければならない。一致しない応答は不正応答としてリトライ対象にする。
- `items` は長さ 2 の配列でなければならず、1 件目が `title="基礎"`、2 件目が `title="応用"` の `major` 項目でなければならない。
- すべての項目オブジェクトの必須フィールドは `title` / `description` / `level` / `children` のみとする。余剰フィールドはエラーとする。
- 許可する `level` は `major` / `middle` / `detail` のみとする。未知の `level` はエラーとする。
- 本仕様における「3 階層」は、全枝で 3 層必須という意味ではなく、許可する `level` と親子関係が `major -> middle -> detail` に固定されることを指す。`major` 配下に `detail` を直接置くこと、`middle` 配下に `middle` を置くこと、`detail` が子を持つことはすべてエラーとする。
- `children` の扱いは以下の通り固定する。
  - `major` と `middle` は `children` フィールド必須。値は配列でなければならず、空配列は許容する。
  - `detail` は `children` フィールド必須。値は必ず `[]` でなければならず、未指定・`null`・非空配列はエラーとする。
- 妥当な応答として受理した後は、各 `children` 配列の要素順を入力 JSON の配列順のまま保持する。generation モジュール側で sibling を並べ替えてはならない。
- `title` と `description` は文字列型必須とする。`title` の空文字判定は B3 側の `RoadmapSaveInput` 検証に従うが、本仕様での LLM 応答バリデーションでも型不一致はエラーとする。
- JSON パース失敗とスキーマバリデーション失敗はカテゴリ別に回数を持たず、上記の総試行回数 3 回の単一 retry 予算を共有する。
- スキーマバリデーション失敗には、ルート `topic` 不一致、必須フィールド欠落、型不一致、未知 `level`、親子関係違反、`detail.children != []`、`items` 構造違反、余剰フィールドを含む。
- JSON パース失敗とスキーマバリデーション失敗はすべて retry 対象とする。共有 retry 予算を使い切った時点で最後に発生した失敗カテゴリに応じて、`RoadmapGenerationFailureCode` の値 `llm_json_parse_failed` または `llm_schema_validation_failed` を `error_code` に決定する。
- 共有 retry 予算を使い切った場合、worker は `job_store.mark_failed(job_id, error_code, error_message)` を試みる。`error_message` には最後の失敗理由を保存する。`mark_failed()` が成功した場合、worker は元のパース/検証失敗を再送出せず `None` を返して終了する。`mark_failed()` が `RoadmapGenerationJobStoreError` を送出した場合は、その store 例外を優先して送出し、元のパース/検証失敗は再送出しない。
- LLM 呼び出し自体の失敗 (`RoadmapGenerationLlmError`) は generation モジュール内では retry 対象外の即時終端失敗とする。worker は `RoadmapGenerationFailureCode` の値 `llm_request_failed` で `job_store.mark_failed(job_id, "llm_request_failed", str(exc))` を試みる。`mark_failed()` が成功した場合、worker は元の `RoadmapGenerationLlmError` を再送出せず `None` を返して終了する。`mark_failed()` が `RoadmapGenerationJobStoreError` を送出した場合は、その store 例外を優先して送出し、元の `RoadmapGenerationLlmError` は再送出しない。
- ジョブキュー基盤側の再試行設定は本仕様の対象外とする。generation モジュールが retry 対象として保証するのは JSON パース失敗とスキーマバリデーション失敗のみである。

### LLM の出力形式

JSON 形式で返させる:
```json
{
  "topic": "TypeScript",
  "items": [
    {
      "title": "基礎",
      "description": "TypeScriptの基本的な実装スキルを身につける",
      "level": "major",
      "children": [
        {
          "title": "変数と型",
          "description": "TypeScriptの基本的な型システムと変数宣言",
          "level": "middle",
          "children": [
            {
              "title": "プリミティブ型",
              "description": "string, number, booleanを使った変数宣言を書けるようになる",
              "level": "detail",
              "children": []
            }
          ]
        }
      ]
    },
    {
      "title": "応用",
      "description": "実践的なTypeScriptパターンを実装する",
      "level": "major",
      "children": []
    }
  ]
}
```

## 内部 DTO / 永続化連携

- generation モジュールは raw LLM JSON をそのまま保存しない。JSON パースとバリデーションを通過した内部 DTO から、B3 の `RoadmapSaveInput` に変換して `RoadmapGenerationPersistencePort.save_roadmap()` を呼ぶ。
- `RoadmapSaveInput` と `RoadmapItemInput` は `roadmap.infrastructure.roadmap_persistence_types` から import する。generation モジュールの `_types.py` でこれらを再定義してはならない。
- `ValidatedRoadmapGenerationItem` から `RoadmapItemInput` への変換は、`title` / `description` / `level` / `children` を対応するフィールドにそのまま渡す 1:1 マッピングとする。テストでは `persistence.save_roadmap()` に渡された `RoadmapSaveInput.items` を capture し、各 `RoadmapItemInput` の `title` / `description` / `level` と `children` の再帰構造を検証する。
- generation worker が保持する内部 DTO は、`roadmap_generation_types.py` に frozen dataclass として定義する。
  - `ValidatedRoadmapGeneration`
    - `topic: str`
    - `items: list[ValidatedRoadmapGenerationItem]`
  - `ValidatedRoadmapGenerationItem`
    - `title: str`
    - `description: str`
    - `level: Literal["major", "middle", "detail"]`
    - `children: list[ValidatedRoadmapGenerationItem]`
- 内部 DTO の `items` と各 `children` は、妥当と判定した LLM 応答 JSON の対応する配列順をそのまま保持する。internal DTO 化や `RoadmapSaveInput` 変換の過程で sibling の並べ替えを行ってはならない。
- 永続化連携の責務分担は以下に固定する。
  1. worker が LLM 応答を内部 DTO に変換する。
  2. worker が `clock.now()` を 1 回だけ呼び、返り値を変換せずそのまま `created_at` として保持する。
  3. worker が `ValidatedRoadmapGeneration` を B3 `RoadmapSaveInput(topic, items, created_at)` に変換する。
  4. worker が `persistence.save_roadmap(roadmap_input)` を呼ぶ。
  5. persistence から返った `RoadmapSaveResult.roadmap_id` を `job_store.mark_completed(job_id, roadmap_id)` に書き戻す。
- `created_at` は generation モジュール側で注入された `RoadmapGenerationClock` から取得した 1 つの値を用い、`RoadmapSaveInput.created_at` にそのまま渡す。generation worker による日時正規化、タイムゾーン補完、offset 付与は行わない。暗黙のシステム時刻取得も行わない。
- この spec が `RoadmapSaveInput.items` について保証するのは、検証済み内部 DTO から B3 保存入力へ変換し、`topic`、各項目の `level`、`title`、`description`、`children` に表現された必須学習項目情報、および sibling 順序を引き継ぐことまでとする。B3 に渡す `items` の厳密な serialization 形状や追加フィールドの有無は `docs/spec/backend/roadmap/roadmap-persistence.md` 側の責務であり、本 spec では固定しない。
- `job_store.mark_completed(job_id, roadmap_id)` が `RoadmapGenerationJobStoreError` を送出した場合、worker はその store 例外をそのまま送出する。保存済みロードマップの巻き戻しや追加の状態補償は行わない。
- job 完了 DTO はロードマップ本体を保持せず、persistence が返した `roadmap_id` のみをジョブ状態に反映する。
- job 失敗時の状態反映は以下に固定する。
  - enqueue 失敗 (`RoadmapGenerationScheduleError`) の場合: `status="failed"`、`error_code` は `RoadmapGenerationFailureCode` の値 `schedule_failed`、`error_message=str(exc)`
  - LLM 呼び出し失敗 (`RoadmapGenerationLlmError`) の場合: `status="failed"`、`error_code` は `RoadmapGenerationFailureCode` の値 `llm_request_failed`、`error_message=str(exc)`
  - JSON パース / スキーマバリデーションの共有 retry 予算を使い切った場合: `status="failed"`、`error_code` は最後の失敗カテゴリに応じた `RoadmapGenerationFailureCode` の値 `llm_json_parse_failed` または `llm_schema_validation_failed`、`error_message` は最後の失敗理由
  - B3 永続化失敗 (`RoadmapPersistenceWriteError`) の場合: `status="failed"`、`error_code` は `RoadmapGenerationFailureCode` の値 `persistence_failed`、`error_message=str(exc)`
  - B3 入力違反 (`RoadmapPersistenceInputError`) の場合: generation と persistence の契約不整合として `status="failed"`、`error_code` は `RoadmapGenerationFailureCode` の値 `persistence_failed`、`error_message=str(exc)` とする
- `RoadmapPersistenceWriteError` または `RoadmapPersistenceInputError` が起きた場合、worker は `job_store.mark_failed(job_id, "persistence_failed", str(exc))` を試みる。`mark_failed()` が成功した場合、worker は元の persistence 例外を再送出せず `None` を返して終了する。`mark_failed()` が `RoadmapGenerationJobStoreError` を送出した場合は、その store 例外を優先して送出し、元の persistence 例外は再送出しない。
- すべての failed 経路で `error_code` と `error_message` の両方を保存し、`get_roadmap_generation_job` の `RoadmapGenerationFailedStatus` でも同じ値を返す。
- generation モジュールが persistence 側失敗に対して追加再試行するかどうかは本仕様の対象外とする。retry 対象は LLM の JSON パース失敗とスキーマバリデーション失敗に限定する。
- generation モジュール内での SQLite 直接操作、raw JSON 保存、persistence Protocol の迂回は行わない。

### 非同期 worker entry

- `backend/roadmap/infrastructure/roadmap_generation.py` には、以下の内部関数を必ず定義する。
  ```python
  _run_roadmap_generation_job(
      job_id: UUID,
      topic: str,
      *,
      llm_client: RoadmapGenerationLlmClient,
      persistence: RoadmapGenerationPersistencePort,
      job_store: RoadmapGenerationJobStatusStore,
      clock: RoadmapGenerationClock,
  ) -> None
  ```
- 上記の関数名、位置、引数順、keyword-only の依存注入、戻り値 `None` はいずれも必須契約とする。別名関数、位置の変更、位置引数での依存注入、戻り値の変更は本仕様を満たさない。
- この worker entry は外部公開 API ではなく、内部実装契約である。呼び出し元に HTTP / UI 契約を増やしてはならない。
- scheduler からこの worker entry をどう起動するか、composition root でどう依存を束ねるか、ジョブキュー製品固有の配線や adapter をどう構成するかは引き続き本仕様の対象外とする。

### 具体例

入力: トピック名 `"TypeScript"`

この例は `detail` まで到達する枝を含む代表例であり、全枝が必ず 3 層に到達することを示すものではない。`major.children=[]` および `middle.children=[]` も妥当な応答として許容する。

出力:
```
TypeScript
├── 基礎（大枠）
│   ├── 変数と型（中枠）
│   │   ├── プリミティブ型（具体）
│   │   ├── 配列とタプル（具体）
│   │   └── オブジェクト型（具体）
│   ├── 関数（中枠）
│   │   ├── 関数の型定義（具体）
│   │   ├── オプショナル引数とデフォルト値（具体）
│   │   └── オーバーロード（具体）
│   ├── ジェネリクス（中枠）
│   │   ├── 基本構文（具体）
│   │   └── 型制約（具体）
│   └── ...
├── 応用（大枠）
│   ├── 条件型（中枠）
│   │   ├── 基本的な条件型（具体）
│   │   └── infer キーワード（具体）
│   ├── デコレータ（中枠）
│   │   └── ...
│   └── ...
```

## 技術判断

- 大枠を基礎・応用の 2 段階に固定する理由: 全トピックでコーディング演習体験を統一する。何が基礎で何が応用かの判断は LLM に委ねる。
- トピック名のみを入力とする理由: LLM の学習データに主要 IT 分野の実装パターンは含まれている。ユーザーのノート内容はマッピング時に使用し、ロードマップ生成には不要。
- JSON 形式で出力させる理由: 構造化パースが容易であり、検証済み内部 DTO を経由して B3 の永続化入力へ変換しやすい。
- 非同期ジョブ受付と状態取得 API を分離する理由: LLM 生成時間を呼び出し元から切り離しつつ、完了後は `roadmap_id` を既存 retrieval に橋渡しできるため。

## 境界条件

- トピック名が曖昧（例: `"プログラミング"`） → LLM の判断に委ねる。結果が広すぎればユーザーが項目を削除・調整する。
- トピック名が空文字または空白のみ → `request_roadmap_generation` は `RoadmapGenerationInputError` を送出し、ジョブを受け付けない。このとき `job_id_generator.generate()`、`job_store.create_queued_job()`、`scheduler.enqueue_roadmap_generation()` はいずれも呼ばれない。
- `create_queued_job()` 自体が失敗する → `request_roadmap_generation` は `RoadmapGenerationJobStoreError` をそのまま送出し、enqueue は行わない。
- `create_queued_job()` 後に enqueue が失敗する → `request_roadmap_generation` は `RoadmapGenerationFailureCode` の値 `schedule_failed` で `job_store.mark_failed(job_id, "schedule_failed", str(exc))` を試みる。`mark_failed()` 成功時は `RoadmapGenerationScheduleError` を再送出し、`mark_failed()` 失敗時は `RoadmapGenerationJobStoreError` を優先送出する。ジョブ削除や再 enqueue は行わない。
- `get_roadmap_generation_job()` の `get_job()` が失敗する → `RoadmapGenerationJobStoreError` または `RoadmapGenerationJobNotFoundError` をそのまま送出する。
- worker 開始時の `mark_running()` が失敗する → `RoadmapGenerationJobStoreError` をそのまま送出し、以降の LLM 呼び出しや状態更新は行わない。
- LLM の JSON 出力がパースできない → スキーマバリデーション失敗と共有の retry 予算で、総試行回数最大 3 回（初回 1 回 + 再試行 2 回）まで再試行する。予算を使い切ったら、最後の失敗が JSON パース失敗なら `RoadmapGenerationFailureCode` の値 `llm_json_parse_failed` で `job_store.mark_failed()` を試みる。`mark_failed()` 成功時は worker が `None` を返して終了し、`mark_failed()` 失敗時は `RoadmapGenerationJobStoreError` を優先送出する。
- LLM 応答の `topic` 不一致、必須欠落、未知 `level`、余剰フィールド、`detail.children != []` を含むスキーマ違反 → JSON パース失敗と共有の retry 予算で、総試行回数最大 3 回（初回 1 回 + 再試行 2 回）まで再試行する。予算を使い切ったら、最後の失敗がスキーマバリデーション失敗なら `RoadmapGenerationFailureCode` の値 `llm_schema_validation_failed` で `job_store.mark_failed()` を試みる。`mark_failed()` 成功時は worker が `None` を返して終了し、`mark_failed()` 失敗時は `RoadmapGenerationJobStoreError` を優先送出する。
- `RoadmapGenerationLlmError` → generation モジュール内では再試行せず、`RoadmapGenerationFailureCode` の値 `llm_request_failed` で `job_store.mark_failed(job_id, "llm_request_failed", str(exc))` を試みる。`mark_failed()` 成功時は worker が `None` を返して終了し、`mark_failed()` 失敗時は `RoadmapGenerationJobStoreError` を優先送出する。
- B3 永続化失敗 (`RoadmapPersistenceWriteError` / `RoadmapPersistenceInputError`) → `RoadmapGenerationFailureCode` の値 `persistence_failed` で `job_store.mark_failed(job_id, "persistence_failed", str(exc))` を試みる。`mark_failed()` 成功時は worker が `None` を返して終了し、`mark_failed()` 失敗時は `RoadmapGenerationJobStoreError` を優先送出する。
- `mark_completed()` が失敗する → ロードマップ保存成功後でも `RoadmapGenerationJobStoreError` をそのまま送出し、追加の補償処理は行わない。
- 同一トピックで 2 回目の生成 → 新しいロードマップとして別途作成する（既存は残す）。
- `get_roadmap_generation_job` に未知の `job_id` を渡した場合 → `RoadmapGenerationJobNotFoundError` を送出する。

## スコープ外

- ロードマップの手動作成（LLM 生成のみ）
- 生成時のユーザーとの対話的なやり取り（一括生成して後から修正）
- ロードマップ間の依存関係管理
- HTTP endpoint、UI 表示仕様、push 通知、メール通知
- ジョブキャンセル、進捗率表示、優先度制御、ジョブキュー製品固有の再試行設定
- generation モジュールによる persistence 失敗の追加再試行方針
- topic 自動補正、LLM 出力の意味的再解釈、余剰フィールドの自動無視
- B3 `RoadmapSaveInput.items` の厳密な serialization 形状、generation モジュールから見えない追加フィールド、保存時の最終的な record 展開方法の固定

## 受け入れ基準

- [ ] `request_roadmap_generation` が `job_id` を含む `RoadmapGenerationAccepted` を返す
- [ ] `RoadmapGenerationAccepted` / `RoadmapGenerationJobStatus` は `backend/roadmap/infrastructure/roadmap_generation_types.py` 上の `TypedDict` 公開 DTO として定義され、呼び出し側は `result["status"]` のようにキー参照で扱う
- [ ] `RoadmapGenerationFailureCode` は `Literal["schedule_failed", "llm_request_failed", "llm_json_parse_failed", "llm_schema_validation_failed", "persistence_failed"]` に固定され、failed DTO と `job_store.mark_failed()` が同じ型を共有する
- [ ] `get_roadmap_generation_job` で `queued` / `running` / `completed` / `failed` を取得できる
- [ ] `completed` 状態でのみ `roadmap_id` が返り、`failed` 状態でのみ `error_code` / `error_message` が返り、ロードマップ本体の取得は既存 B5 retrieval に委譲される
- [ ] トピック名から LLM がロードマップを生成する
- [ ] 大枠が「基礎」「応用」の 2 段階で生成される
- [ ] 許可する階層と親子関係は `major -> middle -> detail` に固定され、`major.children=[]` と `middle.children=[]` を許容する
- [ ] 各項目に `title` と `description` が含まれる
- [ ] `major.children` と `middle.children` の sibling 順序は LLM 応答配列順のまま保持され、generation モジュール側で並べ替えない
- [ ] `create_queued_job()` 失敗は `RoadmapGenerationJobStoreError` をそのまま送出し、`create_queued_job()` 後の enqueue 失敗は `schedule_failed` を記録できたときだけ `RoadmapGenerationScheduleError` を再送出し、`mark_failed()` 失敗時は `RoadmapGenerationJobStoreError` を優先送出する
- [ ] LLM 応答の JSON パース失敗とスキーマ違反は総試行回数最大 3 回（初回 1 回 + 再試行 2 回）の単一 retry 予算を共有し、失敗時は最後の失敗カテゴリに応じた `error_code` で job が `failed` になる
- [ ] `RoadmapGenerationLlmError` と persistence 失敗は generation モジュール内で再試行されず、対応する `mark_failed()` 成功時は worker が元例外を再送出せず終了し、`mark_failed()` 失敗時は `RoadmapGenerationJobStoreError` を優先送出する
- [ ] `get_job()` / `mark_running()` / `mark_completed()` の `RoadmapGenerationJobStoreError` は generation モジュールでラップされずそのまま送出される
- [ ] generation モジュールが検証済み内部 DTO を B3 `RoadmapSaveInput` に変換して RDB 永続化を呼び、`topic`・階層・必須学習項目情報・sibling 順序を引き継ぐ
- [ ] 例外階層が `RoadmapGenerationError` 基底で統一され、内部バリデーション例外 `RoadmapGenerationJsonParseError` / `RoadmapGenerationSchemaValidationError` が `RoadmapGenerationLlmResponseError` の子として定義される
- [ ] `structlog` によるログが `EVENT_*` 定数で定義され、受付成功・入力拒否・enqueue 失敗・worker 開始・retry・完了・失敗の各経路で所定のイベントが記録される
