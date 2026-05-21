---
type: impl
profile: backend
scope: roadmap/roadmap-generation
spec: docs/spec/backend/roadmap/roadmap-generation.md
test_cases: tests/test-cases/backend/roadmap/roadmap-generation.md
---

## 今回やること
roadmap-generation を TDD で実装する

## 対象テストケース
- TC-01: roadmap_generation_types.py の公開 DTO / 失敗コード / 例外階層 / 内部 DTO 契約を静的に検証する
- TC-02: request_roadmap_generation 正常系で受付 DTO 形状、呼び出し順、topic 原値保持、ログを検証する
- TC-03: get_roadmap_generation_job が 4 状態をそのまま返し、状態ごとの返却形状を固定する
- TC-04: worker 成功系で mark_running、LLM 生成、検証済み DTO 化、clock.now()、B3 保存、mark_completed 連携とログを検証する
- TC-10: topic.strip() が空文字なら受付前に RoadmapGenerationInputError を送出し、ログを記録する
- TC-11: JSON パース失敗とスキーマ違反が単一の retry 予算 3 回を共有し、3 回目成功なら継続する
- TC-12: retry 予算を使い切り、最後の失敗が JSON パース失敗なら llm_json_parse_failed で failed 化する
- TC-13: スキーマ違反パターン 13 種がすべて retry 対象であり、最後がスキーマ違反なら llm_schema_validation_failed で failed 化する
- TC-14: 妥当 JSON から B3 保存入力へ変換するとき、topic 原値・許可階層・必須学習項目情報・空枝許容を保持する
- TC-20: create_queued_job() 失敗はラップせず送出し、enqueue しない
- TC-21: create_queued_job() 成功後に enqueue が失敗したとき、schedule_failed を記録できた場合だけ元の RoadmapGenerationScheduleError を再送出する
- TC-22: enqueue 失敗後の mark_failed() が store 例外なら、その store 例外を優先送出する
- TC-23: worker 開始時の mark_running() 失敗では後続処理を一切行わない
- TC-24: 保存成功後の mark_completed() 失敗はそのまま送出し、巻き戻しや failed 化を行わない
- TC-25: 同一 topic を 2 回受け付けても別ジョブとして扱う
- TC-30: get_roadmap_generation_job() の get_job() 例外をラップせず送出する
- TC-31: RoadmapGenerationLlmError は retry せず llm_request_failed で failed 化し、mark_failed() 成功時は元例外を再送出しない
- TC-32: persistence 失敗は persistence_failed で failed 化し、mark_failed() 成功時は元例外を再送出しない

## やらないこと
- HTTP endpoint、UI 表示仕様、push 通知
- ジョブキャンセル、進捗率表示、優先度制御
- ジョブキュー製品固有の再試行設定
- generation モジュールによる persistence 失敗の追加再試行
- topic 自動補正、LLM 出力の意味的再解釈
- B3 RoadmapSaveInput.items の厳密 serialization 形状の固定

## 完了条件
- 対象テストケースが全て GREEN
- ruff + mypy がパス
- レビュー通過

## 設計判断
- 公開 DTO は TypedDict（辞書互換）、内部 DTO は frozen dataclass
- RoadmapSaveInput / RoadmapItemInput は roadmap.infrastructure.roadmap_persistence_types から import
- ValidatedRoadmapGenerationItem → RoadmapItemInput は title/description/level/children の 1:1 マッピング
- 例外は RoadmapGenerationError 基底で統一、内部バリデーション例外は RoadmapGenerationLlmResponseError の子
- ログは structlog、EVENT_* 定数パターン、logger = structlog.get_logger(__name__)
- worker retry ループは RoadmapGenerationLlmResponseError を catch して retry、最後の例外型で error_code 決定
- 全ファイルを backend/roadmap/infrastructure/ に配置（harness sourceLayout 準拠）
- 2 モジュール構成: roadmap_generation_types.py, roadmap_generation.py
