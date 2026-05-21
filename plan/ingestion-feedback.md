---
type: impl
profile: backend
scope: ingestion/ingestion-feedback
spec: docs/spec/backend/ingestion/ingestion-feedback.md
test_cases: tests/test-cases/backend/ingestion/ingestion-feedback.md
---

## 今回やること
ingestion-feedback を TDD で実装する

## 対象テストケース
- TC-01: ロードマップ候補ありで1件のフィードバックを新規保存し、戻り値・保存本文・成功ログを完全検証する
- TC-02: ロードマップ候補0件でもフィードバックを作成でき、roadmap_item_id=nullと通知行省略を維持する
- TC-03: 分析可能チャンクが0件ならスキップし、外部依存を呼ばず、スキップログを出す
- TC-10: 文字数しきい値はstrip()後長さで判定し、しきい値ちょうどのチャンクを採用しつつ、LLMにはchunk_index昇順で渡す
- TC-11: ロードマップ候補は存在しても、LLMがselected_roadmap_item_id=nullを返した場合は通知行なしで保存する
- TC-12: 複数の分析可能チャンクがあっても、ファイル単位でLLM1回・保存1回・作成レコード1件だけに集約する
- TC-13: 同じsource_pathの再取り込みでは旧レコードを残したまま新規create(...)で追記する
- TC-20: chunks=[]はスキップし、件数0/外部依存未呼び出し/スキップログを返す
- TC-21: 入力契約違反はIngestionFeedbackInputErrorを送出し、外部依存呼び出しへ進まない
- TC-22: LLM応答の契約違反はIngestionFeedbackResponseFormatErrorとして扱い、保存しない
- TC-30: Protocolだけを満たす依存オブジェクトで生成処理を完結でき、concrete classへの依存がない
- TC-31: ロードマップ取得失敗時はIngestionFeedbackRoadmapLookupErrorを送出し、後続依存を呼ばず、失敗ログを出す
- TC-32: LLM呼び出し失敗時はIngestionFeedbackLlmCallErrorを送出し、保存せず、失敗ログを出す
- TC-33: 保存失敗時はIngestionFeedbackPersistenceErrorを送出し、失敗ログを出す

## やらないこと
- フィードバックの既読化・一覧取得・フィルタリングAPI
- フィードバックに基づくノート本文の自動修正
- 複数ロードマップ項目への同時紐付け
- LLMプロンプト文面そのものの設計詳細やモデル選定

## 完了条件
- 対象テストケースが全て GREEN
- ruff + mypy がパス
- レビュー通過

## 設計判断
- 依存モジュールはProtocol DIで注入（IngestionFeedbackLlmClient, RoadmapItemReader, IngestionFeedbackWriter）
- 全ファイルを backend/ingestion/infrastructure/ に配置（harness sourceLayout準拠）
- 3モジュール構成: ingestion_feedback_types.py, ingestion_feedback_domain.py, ingestion_feedback.py
- titleは固定文字列、bodyは決定的組み立て（LLMの揺らぎをbody内容だけに閉じ込める）
- 再取り込み時はinsert-only（旧レコード保持で履歴追跡可能）
