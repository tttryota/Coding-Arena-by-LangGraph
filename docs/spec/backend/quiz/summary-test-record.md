---
feature: summary-test-record
status: ready
reviewed_by:
approved_at:
---

## 機能概要

中枠・大枠レベルのまとめテスト完了時に、LLMが全問答を分析して定性的な弱点・傾向コメントを生成し、SummaryTestResultに保存する。

## 振る舞い

### 基本動作

`record_summary_test` は、呼び出し側がまとめテスト（中枠・大枠のロードマップ項目に対するクイズセッション）の完了を判定した後にだけ起動する記録ノードである。`SessionState` 単体から完了判定は行わない。

1. 全QuizAnswerをLLMに渡す
2. LLMが全体を分析し、以下を生成:
   - **score**（0〜100）— 総合的なスコア
   - **analysis**（テキスト）— 弱点・傾向の定性分析
3. SummaryTestResultに保存

### 入力契約

- `SessionState` の authoritative contract は `docs/spec/backend/quiz/session-state.md` と `docs/spec/backend/quiz/quiz-overview.md` を参照する。この feature spec では upstream 契約の再定義や追加は行わず、`record_summary_test` が利用する required input のみを列挙する
- `record_summary_test` を起動する呼び出し側は、upstream `SessionState` 契約に従ったうえで少なくとも次のキーを提供する
  - `session_id`
  - `roadmap_item_id`
  - `roadmap_item_level`
  - `roadmap_item_title`
  - `roadmap_item_description`
  - `answers`
- `record_summary_test` は上記キーを読み取り、`roadmap_item_level` が `middle` / `major` のときだけ LLM 分析と保存を行う。`detail` のときは early return する
- この feature では `SessionState` の新規フィールド追加、完了状態を表す追加キー定義、呼び出し前の完了判定ロジックは定義しない

### analysisの内容

個別のQuizAnswer.feedbackとは異なり、セッション全体を俯瞰した分析:
- 配下の具体項目間での理解度の偏り
- 知識問題と実践問題の差異
- 全体的な傾向や弱点の指摘
- 次に注力すべき分野の提案

### LLMコンテキストの扱い

- `roadmap_item_title` と `roadmap_item_description` は、対象ロードマップ項目を表す LLM コンテキストとして利用する
- この feature で契約化するのは「対象ロードマップ項目の値を LLM 分析に使う」粒度までとし、raw 文字列の完全一致、trim 禁止、空白正規化禁止、要約禁止、再整形禁止のような pass-through 契約は定義しない
- `answers` はセッション全体分析の入力として全件を LLM に渡す。DTO 表現の完全一致、順序固定、各フィールドの無変換まではこの feature の公開契約に含めない

### 具体例

まとめテスト: TypeScript > 基礎（中枠）
配下の具体項目を横断して出題した結果:

```
score: 65
analysis: 「型の基礎知識は十分ですが、ジェネリクスの実践的な使用に
課題があります。特に型パラメータを使った関数を自力で書く場面で
構文ミスが目立ちました。また、型推論の仕組みは理解していますが、
いつ明示的に型を指定すべきかの判断基準が曖昧です。
ジェネリクスの実践問題を重点的に復習することを推奨します。」
```

上記の `score` / `analysis` 文面は説明用の具体例であり、テストフィクスチャや厳密一致の規範ではない。

## 技術判断

- SummaryTestResultを独立テーブルとする理由: LLMによる定性分析（analysis）は単純なスコア集計では生成できない。この分析を保持することがこのテーブルの存在意義
- progress-updateとの違い: progress-updateはdetail項目のscoreを更新する。summary-test-recordは中枠・大枠のまとめテスト結果を記録するだけで、detail項目のscoreには影響しない

## 境界条件

- detail項目のセッション → SummaryTestResultは作成しない（progress-updateのみ）
- 同一ロードマップ項目でまとめテストを複数回実施 → 都度新しいレコードを作成（履歴として蓄積）

### 永続化契約の境界

- この feature が公開する store 契約は `SummaryTestStore.save_result(session_id: str, roadmap_item_id: str, score: int, analysis: str) -> None` のみとする
- 保存後の read-back 方法、観測可能フィールド、`SummaryTestResult` の取得契約はこの feature のスコープ外とし、取得系の責務は `summary-test-results` 側で扱う
- したがって、この feature spec では保存要求の発行までは定義するが、保存済み結果をこの場で読み戻して検証する契約までは定義しない

## スコープ外

- まとめテスト完了判定ロジックの定義
- 完了状態を表す `SessionState` の追加項目定義
- まとめテスト結果間の比較分析
- analysisに基づくロードマップの自動修正

## 受け入れ基準

- [ ] 呼び出し側がまとめテスト完了と判定して `record_summary_test` を起動した時にSummaryTestResultが作成される
- [ ] LLMによる定性分析（analysis）が生成される
- [ ] scoreが0〜100で算出される
- [ ] detail項目のセッションではSummaryTestResultが作成されない
- [ ] 同一項目の複数回テスト結果が履歴として蓄積される

## 異常系

- LLM client / store は、失敗時に `SummaryTestRecordError` を生成して送出し、`error_code: str` と `message: str` を属性として持ち、`__cause__` に元例外を保持する
- `record_summary_test` は、LLM client / store から受けた `SummaryTestRecordError` に対して `summary_test_record_failed` をちょうど1件だけ記録して再送出する
- 自動再試行は行わない
- raw の依存先例外を `record_summary_test` 内で独自に変換する契約は、この feature spec では定義しない

| error_code | 発生条件 | message | ログイベント |
|---|---|---|---|
| `llm_request_failed` | LLM client が LLM呼び出し失敗を `SummaryTestRecordError` に変換して送出 | `summary test record llm request failed` | `summary_test_record_failed` |
| `llm_response_parse_failed` | LLM client が LLM応答からscore/analysisの抽出失敗を `SummaryTestRecordError` に変換して送出 | `summary test record llm response parse failed` | `summary_test_record_failed` |
| `persistence_failed` | store が DB保存失敗を `SummaryTestRecordError` に変換して送出 | `summary test record persistence failed` | `summary_test_record_failed` |

## モジュール構成

- 構成方針: 2ファイル構成（types + logic）
- モジュール一覧:
  - `backend/quiz/application/summary_test_record_types.py`
    - `SummaryTestRecordError(Exception)` — `error_code: str`, `message: str` を属性として持つ
    - `SummaryTestLlmClient(Protocol)` — `analyze_session(title: str, description: str, answers: list[QuizAnswerRecord]) -> SummaryAnalysis`。全問答の定性分析。失敗時は `SummaryTestRecordError` を送出
    - `SummaryAnalysis` — frozen dataclass (`score: int`, `analysis: str`)
    - `SummaryTestStore(Protocol)` — `save_result(session_id: str, roadmap_item_id: str, score: int, analysis: str) -> None`。DB保存失敗時は `SummaryTestRecordError(error_code="persistence_failed", message="summary test record persistence failed")` を送出し、`__cause__` に元例外を保持する
  - `backend/quiz/application/summary_test_record.py`
    - `record_summary_test(state: SessionState, *, llm: SummaryTestLlmClient, store: SummaryTestStore) -> None` — LangGraphノード関数。呼び出し側がまとめテスト完了と判定した後の `SessionState` を受け取り、middle/major レベルなら LLM で定性分析 → SummaryTestResult に保存する。`SessionState` 単体から完了判定は行わず、detail レベルの場合は何もしない（early return）
    - LLM client / store が送出した `SummaryTestRecordError` を受けたら `summary_test_record_failed` を1件だけ記録して再送出する
