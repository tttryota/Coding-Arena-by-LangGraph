---
status: ready
---

# テストケース一覧

# 検証焦点

| テストの種類 | 検証焦点 |
|---|---|
| Phase 1（最小骨格） | detail 完了時の総合評価反映、summary test 完了時の SummaryTestResult 保存と非更新分岐 |
| Phase 2（コアロジック） | LLM へ渡す評価コンテキストと順序契約、最新 score による上書き、comment と score の同一評価結果としての取り扱い |
| Phase 3（エッジケース） | `answers=0` の短絡完了、score / `last_quiz_at` の非更新条件 |
| Phase 4（外部連携） | 非再試行、`ProgressUpdateError` の再送出、構造化ログ `progress_update_failed` の件数と内容 |

## Phase 1: 最小骨格

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-01 | detail セッション完了で総合評価に基づき `RoadmapItem.score` と `last_quiz_at` が更新される | `SessionState` に detail 項目 `item_id="detail_001"`、`roadmap_item_title="Union型の narrowing とガード条件"`、`roadmap_item_description="TypeScript の型 narrowing を理解する"`、確認ポイント群、shared schema の `QuizAnswerRecord` を要素に持つ `answers` 5件が格納されている。対象 `RoadmapItem` の事前値は `score=64`、`last_quiz_at="2026-05-01T10:00:00+09:00"`。`llm.evaluate_session(...)` は `ProgressOutput(score=81, comment="条件分岐ごとの型の絞り込みは概ね安定している。一方で user-defined type guard の戻り値設計には曖昧さが残る。")` を返す | `update_progress(state, llm=..., store=...)` を実行する | `llm.evaluate_session(...)` がちょうど1回呼ばれる。`RoadmapItem.score` は `81` に完全一致で更新される。`RoadmapItem.last_quiz_at` は非NULLへ更新され、事前値 `"2026-05-01T10:00:00+09:00"` から変化していることを確認する。`store.complete_session(session_id)` はちょうど1回実行され、対象セッションは完了状態として観測できる。失敗ログ `event="progress_update_failed"` は0件である | 受け入れ基準「detail 項目で `answers` が1件以上ある場合、RoadmapItem.score と RoadmapItem.last_quiz_at が更新される」に対応 |
| TC-02 | middle / major のまとめテスト完了時は `RoadmapItem.score` と `last_quiz_at` を更新せず、SummaryTestResult に保存する | この TC は `roadmap_item_level in {"middle", "major"}` の 2 値を同一期待結果で回すパラメタライズケースとする。各試行で `SessionState` はまとめテスト用項目を指し、`answers` は1件以上ある。対象 `RoadmapItem` の事前値は `score=88`、`last_quiz_at="2026-05-10T09:00:00+09:00"`。`llm.evaluate_session(...)` は `ProgressOutput(score=73, comment="関連項目を横断した理解はあるが、説明の一貫性に揺れがある。")` を返す | `update_progress(state, llm=..., store=...)` を `roadmap_item_level="middle"` と `roadmap_item_level="major"` の各値で実行する | 各試行で `llm.evaluate_session(...)` はちょうど1回呼ばれる。`RoadmapItem.score` は `88` のままで更新されない。`RoadmapItem.last_quiz_at` も `"2026-05-10T09:00:00+09:00"` のままで更新されない。`store.save_summary_test_result(session_id, item_id, 73, "関連項目を横断した理解はあるが、説明の一貫性に揺れがある。")` はちょうど1回実行される。`store.complete_session(session_id)` はちょうど1回実行される。失敗ログ `event="progress_update_failed"` は0件である | 受け入れ基準「まとめテストで `answers` が1件以上ある場合、RoadmapItem.score と RoadmapItem.last_quiz_at は更新されず、SummaryTestResult に `session_id`、`item_id`、`score`、`comment` が保存される」に対応 |

## Phase 2: コアロジック

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-10 | LLM 評価には仕様書で列挙された全コンテキストが契約どおり渡される | detail 項目の `roadmap_item_title` / `roadmap_item_description`、確認ポイント3件、shared schema の `QuizAnswerRecord` を要素に持つ `answers` 4件が `SessionState` にある。検証対象の shared schema は [`docs/spec/backend/quiz/session-state.md`](/Users/tsuryoryo/Desktop/repo/obsidian/docs/spec/backend/quiz/session-state.md) と [`backend/quiz/domain/session_state.py`](/Users/tsuryoryo/Desktop/repo/obsidian/backend/quiz/domain/session_state.py) を authoritative contract とし、この TC では LLM 評価上意味を持つ `question_text` / `answer_text` / `score` / `feedback` を持つレコードを用意する。問答の中に「解説してください」と明示された流れが1回含まれる。LLM 呼び出し引数を観測できるテストダブルがある | `update_progress(state, llm=..., store=...)` を実行する | `llm.evaluate_session(roadmap_item_title, roadmap_item_description, checkpoints, answers)` がちょうど1回呼ばれる。`roadmap_item_title` と `roadmap_item_description` は `SessionState` の同名キーの値と完全一致する。`checkpoints` には `confirmation_points[*].content` 由来の3件が欠落0件で渡る。`answers` には shared schema の全4件が欠落0件で渡り、入力順が保持される。`answers` の検証対象は `question_text` / `answer_text` / `score` / `feedback` とし、問答中の「解説してください」を含む要素もこの順序付き `answers` に含まれる。解説依頼の有無を表す専用引数は追加で要求しない。`ProgressOutput` は `comment` と `score` を同一の評価結果として返し、`score` だけが独立入力として与えられることはない | 受け入れ基準「全QuizAnswerからLLMが総合コメントを生成」「総合コメントに基づいてscoreが算出」に対応 |
| TC-11 | 前回より低い `score` でも最新評価で上書きされる | detail 項目の対象 `RoadmapItem` の事前値が `score=92`、`last_quiz_at="2026-05-15T11:00:00+09:00"` である。`answers` は1件以上ある。`llm.evaluate_session(...)` は `ProgressOutput(score=61, comment="概念理解はあるが、実装時の再現性に大きな揺れがある。")` を返す | `update_progress(state, llm=..., store=...)` を実行する | `RoadmapItem.score` は `92` から `61` に完全一致で上書きされる。低下を理由に更新が抑止されることはない。`RoadmapItem.last_quiz_at` は非NULLの新しい値へ更新される。`store.complete_session(session_id)` はちょうど1回実行される | 境界条件「前回のscoreより今回のscoreが低い場合」に対応 |

## Phase 3: エッジケース

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-20 | `answers=0` の完了では LLM を呼ばず `score=0` と `last_quiz_at=None` のまま更新しない | detail 項目の `SessionState` で、`answers=[]` のまま完了処理に入る。対象 `RoadmapItem` の事前値は `score=0`、`last_quiz_at=None`。LLM 呼び出し回数と store 呼び出し回数を観測できる | `update_progress(state, llm=..., store=...)` を実行する | `llm.evaluate_session(...)` は0回呼ばれる。`RoadmapItem.score` は `0` のままで更新されない。`RoadmapItem.last_quiz_at` は `None` のままで更新されない。`store.update_roadmap_item_progress(...)` は0回、`store.save_summary_test_result(...)` は0回である。`store.complete_session(session_id)` はちょうど1回実行される | 境界条件「QuizAnswerが0件」に対応 |

## Phase 4: 外部連携

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-30 | 正常系では LLM / store 連携が各1回で完了し、自動再試行も失敗ログもない | detail 項目の `SessionState` に `answers` が1件以上ある。`llm.evaluate_session(...)` は `ProgressOutput(score=80, comment="理解は概ね安定している。")` を返す。`store` は正常応答する。`structlog` 出力を観測できる | `update_progress(state, llm=..., store=...)` を実行する | `llm.evaluate_session(...)` はちょうど1回呼ばれる。`store.update_roadmap_item_progress(item_id, 80, last_quiz_at)` はちょうど1回呼ばれる。`store.save_summary_test_result(...)` は0回である。`store.complete_session(session_id)` はちょうど1回呼ばれる。自動再試行は0回である。構造化ログ `event="progress_update_failed"` は0件である | 外部連携の正常経路確認 |
| TC-31 | LLM 呼び出し失敗時は `ProgressUpdateError` をそのまま再送出し、失敗ログをちょうど1件出す | `llm.evaluate_session(...)` が依存先例外を `__cause__` に持つ `ProgressUpdateError(error_code="llm_request_failed", message="progress update llm request failed")` を送出する。`structlog` 出力を観測できる。`store` の呼び出し有無を観測できる | 任意の `answers` 1件以上を持つ `SessionState` で `update_progress(state, llm=..., store=...)` を実行する | `ProgressUpdateError` が送出される。`error_code` は `llm_request_failed`、`message` は `progress update llm request failed` と完全一致し、`__cause__` は元例外を保持する。`llm.evaluate_session(...)` はちょうど1回呼ばれ、自動再試行は0回である。spec 準拠で `store.update_roadmap_item_progress(...)`、`store.save_summary_test_result(...)`、`store.complete_session(...)` はいずれも0回である。構造化ログは `event="progress_update_failed"` がちょうど1件で、spec の必須キーとして `event`、`error_code="llm_request_failed"`、`message="progress update llm request failed"` を含む。追加キーは許容する | 異常系 `llm_request_failed` |
| TC-32 | LLM 応答パース失敗時は `ProgressUpdateError` をそのまま再送出し、失敗ログをちょうど1件出す | `llm.evaluate_session(...)` がパース例外を `__cause__` に持つ `ProgressUpdateError(error_code="llm_response_parse_failed", message="progress update llm response parse failed")` を送出する。`structlog` 出力を観測できる。`store` の呼び出し有無を観測できる | 任意の `answers` 1件以上を持つ `SessionState` で `update_progress(state, llm=..., store=...)` を実行する | `ProgressUpdateError` が送出される。`error_code` は `llm_response_parse_failed`、`message` は `progress update llm response parse failed` と完全一致し、`__cause__` は元例外を保持する。`llm.evaluate_session(...)` はちょうど1回呼ばれ、自動再試行は0回である。spec 準拠で `store.update_roadmap_item_progress(...)`、`store.save_summary_test_result(...)`、`store.complete_session(...)` はいずれも0回である。構造化ログは `event="progress_update_failed"` がちょうど1件で、spec の必須キーとして `event`、`error_code="llm_response_parse_failed"`、`message="progress update llm response parse failed"` を含む。追加キーは許容する | 異常系 `llm_response_parse_failed` |

# 網羅性チェック

仕様書の受け入れ基準の各項目に対応するテストケース ID を記載する。
全項目が少なくとも1つのテストケースでカバーされていることを確認する。

| 受け入れ基準 | 対応テストケース |
|---|---|
| 全QuizAnswerからLLMが総合コメントを生成する | TC-10 |
| 総合コメントに基づいてscoreが算出される | TC-10 |
| detail 項目で `answers` が1件以上ある場合、RoadmapItem.score と RoadmapItem.last_quiz_at が更新される | TC-01, TC-11, TC-30 |
| まとめテストで `answers` が1件以上ある場合、RoadmapItem.score と RoadmapItem.last_quiz_at は更新されず、SummaryTestResult に `session_id`、`item_id`、`score`、`comment` が保存される | TC-02 |
| `answers=0` の場合、LLM を呼ばず、RoadmapItem.score と RoadmapItem.last_quiz_at を更新せずにセッション完了のみ行う | TC-20 |

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
