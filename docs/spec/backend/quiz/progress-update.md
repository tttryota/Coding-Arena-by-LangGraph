---
feature: progress-update
status: ready
reviewed_by:
approved_at:
---

## 機能概要

クイズセッション完了時に、全問答をLLMが総合的に評価し、scoreを算出する。detail 項目ではその結果を `RoadmapItem` に反映し、middle / major のまとめテストでは `SummaryTestResult` に記録する。scoreは定性的な総合コメントの後に導出される（ADR-004参照）。

## 振る舞い

### 基本動作

セッション完了時は、項目種別と `answers` 件数に応じて以下を行う。

1. **detail 項目かつ QuizAnswer が1件以上**
   LLM が全問答を総合評価し、以下を算出する:
   - **総合コメント**（テキスト）— 全問答を通じた理解度の総合評価。強み・弱みの指摘
   - **score**（0〜100）— 総合コメントに基づく数値化
   算出された `score` で `RoadmapItem.score` を更新し、同じ更新で `RoadmapItem.last_quiz_at` も更新する。

2. **middle / major のまとめテストかつ QuizAnswer が1件以上**
   LLM は detail 項目と同様に総合コメントと `score` を算出する。
   ただし `RoadmapItem.score` と `RoadmapItem.last_quiz_at` は更新しない。代わりに `SummaryTestResult` へ `session_id`、`item_id`、`score`、`comment` を保存する。

3. **QuizAnswer が0件**
   LLM は呼ばない。`RoadmapItem.score` と `RoadmapItem.last_quiz_at` は更新せず、セッション完了のみ行う。

### LLMに渡す情報

- `SessionState.roadmap_item_title`
- `SessionState.roadmap_item_description`
- `SessionState.confirmation_points[*].content`
- `SessionState.answers`

`SessionState` と `QuizAnswerRecord` の authoritative contract は [`docs/spec/backend/quiz/session-state.md`](/Users/tsuryoryo/Desktop/repo/obsidian/docs/spec/backend/quiz/session-state.md) および [`backend/quiz/domain/session_state.py`](/Users/tsuryoryo/Desktop/repo/obsidian/backend/quiz/domain/session_state.py) とする。この仕様では別名 DTO を再定義しない。

`ProgressUpdateLlmClient` には `SessionState.roadmap_item_title`、`SessionState.roadmap_item_description`、`SessionState.confirmation_points[*].content` を順に抽出した `checkpoints`、および `SessionState.answers` を渡す。`answers` は shared schema の `list[QuizAnswerRecord]` をセッション中の入力順のままそのまま渡し、正規化や並べ替えは行わない。評価上意味を持つ共有フィールドは少なくとも `question_text` / `answer_text` / `score` / `feedback` とする。解説依頼の有無は専用引数では渡さず、この順序付き `answers` の内容から評価時に読み取る。

### 具体例

入力:
```
項目: ジェネリクスの基本構文と型パラメータ
QuizAnswer:
  問1（知識）: score 75 - 概念は理解、クラスへの適用が抜け
  問2（知識）: score 85 - 型パラメータの構文を正確に理解
  問3（知識）: score 90 - 型推論の説明が的確
  問4（実践）: score 70 - コードの意図は正しいが構文ミス
  問5（知識）: score 85 - anyとの比較を的確に説明
```

出力:
```
総合コメント: 「ジェネリクスの概念と必要性は十分に理解しています。
型推論やanyとの違いも的確に説明できています。
ただし、コードに落とす際に関数定義の構文で躓きがあり、
アウトプット力に課題が見られます。
関数定義の基礎練習を併せて行うとより効果的です。」

score: 78
```

→ RoadmapItem.score = 78 に更新

## 技術判断

- 単純平均ではなくLLMが総合判断する理由: 解説を聞いた後の高得点、深掘りで追加された問題の重み、概念とコードの乖離など、単純平均では文脈を反映できない
- 総合コメントを先に出す理由: scoreは判断の出力であって入力ではない（ADR-004参照）

## 境界条件

- QuizAnswerが0件（セッション開始直後に完了） → LLM は呼ばない。`RoadmapItem.score` と `RoadmapItem.last_quiz_at` は更新せず、`complete_session` のみ実行する
- 前回のscoreより今回のscoreが低い場合 → 上書きする（最新の評価を正とする）
- まとめテスト（中枠・大枠）の場合 → `RoadmapItem.score` と `RoadmapItem.last_quiz_at` は更新しない。`SummaryTestResult` に `session_id`、`item_id`、`score`、`comment` を記録する

## スコープ外

- スコアの履歴管理（前回との比較表示等）
- 複数セッションのスコア統合（最新セッションのscoreで上書き）

## 受け入れ基準

- [ ] 全QuizAnswerからLLMが総合コメントを生成する
- [ ] 総合コメントに基づいてscoreが算出される
- [ ] detail 項目で `answers` が1件以上ある場合、RoadmapItem.score と RoadmapItem.last_quiz_at が更新される
- [ ] まとめテストで `answers` が1件以上ある場合、RoadmapItem.score と RoadmapItem.last_quiz_at は更新されず、SummaryTestResult に `session_id`、`item_id`、`score`、`comment` が保存される
- [ ] `answers=0` の場合、LLM を呼ばず、RoadmapItem.score と RoadmapItem.last_quiz_at を更新せずにセッション完了のみ行う

## 異常系

- LLM呼び出し失敗時は `ProgressUpdateError` を送出し、`error_code: str` と `message: str` を属性として持ち、`__cause__` に元例外を保持する
- 自動再試行は行わない
- `update_progress(...)` が `ProgressUpdateError` を受けた場合は、`event="progress_update_failed"` を含む `structlog` の構造化ログをちょうど1件だけ出力して再送出する
- `progress_update_failed` のログ payload 必須キーは `event` / `error_code` / `message` とする
- `ProgressUpdateError` 発生後は `store.update_roadmap_item_progress(...)` / `store.save_summary_test_result(...)` / `store.complete_session(...)` を含む store 呼び出しを行わない

| error_code | 発生条件 | message | ログイベント |
|---|---|---|---|
| `llm_request_failed` | LLM呼び出し自体が失敗 | `progress update llm request failed` | `progress_update_failed` |
| `llm_response_parse_failed` | LLM応答からscore/コメントの抽出に失敗 | `progress update llm response parse failed` | `progress_update_failed` |

## モジュール構成

- 構成方針: 2ファイル構成（types + logic）
- モジュール一覧:
  - `backend/quiz/application/progress_update_types.py`
    - `ProgressUpdateError(Exception)` — `error_code: str`, `message: str` を属性として持つ
    - `ProgressUpdateLlmClient(Protocol)` — `evaluate_session(roadmap_item_title: str, roadmap_item_description: str, checkpoints: list[str], answers: list[QuizAnswerRecord]) -> ProgressOutput`。`roadmap_item_title` と `roadmap_item_description` は `SessionState` の同名キーから読み、`checkpoints` は `confirmation_points[*].content` を順に抽出して渡す。`answers` は shared schema の `QuizAnswerRecord` を入力順の `list` としてそのまま渡し、評価上意味を持つ共有フィールドは少なくとも `question_text` / `answer_text` / `score` / `feedback` とする。解説依頼の有無を表す専用引数は追加しない。失敗時は `ProgressUpdateError` を送出
    - `ProgressOutput` — frozen dataclass (`score: int`, `comment: str`)
    - `ProgressUpdateStore(Protocol)` — `update_roadmap_item_progress(item_id: str, score: int, last_quiz_at: datetime) -> None`, `save_summary_test_result(session_id: str, item_id: str, score: int, comment: str) -> None`, `complete_session(session_id: str) -> None`
  - `backend/quiz/application/progress_update.py`
    - `update_progress(state: SessionState, *, llm: ProgressUpdateLlmClient, store: ProgressUpdateStore) -> dict[str, object]` — LangGraphノード関数。`answers` が0件なら LLM を呼ばず、RoadmapItem.score と RoadmapItem.last_quiz_at を更新せずにセッション完了のみ行う。`answers` が1件以上ある場合は全問答を LLM で総合評価して score を算出し、detail 項目なら `update_roadmap_item_progress(...)` を実行してセッション完了、middle/major（まとめテスト）なら `save_summary_test_result(...)` を実行してセッション完了する
    - `ProgressUpdateError` を受けたら、必須キー `event` / `error_code` / `message` を含む `progress_update_failed` を1件だけ記録して再送出する。この経路では `store.update_roadmap_item_progress(...)` / `store.save_summary_test_result(...)` / `store.complete_session(...)` を含む store 呼び出しを行わない
