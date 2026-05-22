---
status: ready
---

# テストケース一覧

# 検証焦点

| テストの種類 | 検証焦点 |
|---|---|
| Phase 1（最小骨格） | `deliver_question` の公開戻り値契約、必須 state キーの参照、`llm.generate_question(...)` への 1 対 1 マッピング、`total_questions_asked` の初期化/加算 |
| Phase 2（コアロジック） | `knowledge` / `knowledge_and_practice` の形式情報と過去問答履歴を client へそのまま渡すこと、client が返した `QuestionOutput` を node がそのまま反映すること、セッション再開 |
| Phase 3（エッジケース） | 全確認ポイント消化時の停止、深掘りで追加された確認ポイントの出題 |
| Phase 4（外部連携） | mock/stub `QuestionDeliveryLlmClient` 経由での正常連携、`QuestionDeliveryError` の再送出、非再試行、構造化ログちょうど1件 |

## Phase 1: 最小骨格

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-01 | 最初の未確認ポイントを使って問題文・`answer_type`・出題数を返す | `state.confirmation_points` に2件の確認ポイントがあり、`current_point_index=0`、`answers=[]`、`total_questions_asked` は未設定である。`llm.generate_question()` は `QuestionOutput(question_text="ジェネリクスが必要な理由を説明してください。", answer_type="textarea")` を返す | `state={"roadmap_item_title":"TypeScript ジェネリクス","roadmap_item_description":"型パラメータと推論の理解を確認する","confirmation_points":[{"id":"cp_001","content":"ジェネリクスの必要性を説明できる","format":"knowledge"},{"id":"cp_002","content":"ジェネリック関数を実装できる","format":"knowledge_and_practice"}],"current_point_index":0,"answers":[]}` を渡して `deliver_question(state, llm=...)` を実行する | `llm.generate_question()` がちょうど1回呼ばれ、引数 `title`, `description`, `confirmation_point_content`, `confirmation_point_format`, `past_answers` はそれぞれ `state["roadmap_item_title"]`, `state["roadmap_item_description"]`, `confirmation_points[0]["content"]`, `confirmation_points[0]["format"]`, `state["answers"]` と完全一致する。戻り値はキー `current_question_text`, `current_answer_type`, `total_questions_asked` のちょうど3件を持つ dict である。`current_question_text` は LLM 返却文と完全一致し、`current_answer_type` は `"textarea"`、`total_questions_asked` は `1` と完全一致する | LangGraph ノードの最小公開契約 |
| TC-02 | `current_point_index` が指す確認ポイントを選び、既存の出題数に1を加算する | `state.confirmation_points` に3件の確認ポイントがあり、`current_point_index=1`、`answers` に1件の履歴、`total_questions_asked=4` が設定されている。`llm.generate_question()` は `QuestionOutput(question_text="filterBy を実装してください。", answer_type="code")` を返す | `state` の2件目確認ポイントだけが実践向け内容になるように構成して `deliver_question(state, llm=...)` を実行する | `llm.generate_question()` の `title`, `description`, `confirmation_point_content`, `confirmation_point_format`, `past_answers` はそれぞれ `state["roadmap_item_title"]`, `state["roadmap_item_description"]`, `confirmation_points[1]["content"]`, `confirmation_points[1]["format"]`, `state["answers"]` と完全一致する。戻り値の `current_question_text` は `"filterBy を実装してください。"`、`current_answer_type` は `"code"`、`total_questions_asked` は `5` と完全一致する | `current_point_index` による選択と加算の確認 |

## Phase 2: コアロジック

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-10 | `knowledge` の確認ポイントと過去問答履歴を client へそのまま渡し、client 返却値を node がそのまま返す | stub `llm.generate_question()` が、確認ポイント `content="明示的型指定と型推論の違い"`、`format="knowledge"`、過去問答1件を受け取ったとき `QuestionOutput(question_text="先ほどの identity 関数では型引数を明示する書き方と省略する書き方がありました。なぜ省略できるのか説明してください。", answer_type="textarea")` を返す | `roadmap_item_title="TypeScript ジェネリクス"`, `roadmap_item_description="型パラメータと推論の理解を確認する"`, `confirmation_points=[{"id":"cp_002","content":"明示的型指定と型推論の違い","format":"knowledge"}]`, `current_point_index=0`, `answers=[{"question_number":1,"confirmation_point_id":"cp_001","question_text":"identity 関数の `<T>` は何を表しますか？","answer_type":"textarea","answer_text":"呼び出しごとに変わる型を表します。","score":80,"feedback":"概ね正しいです。"}]` を含む `SessionState` で `deliver_question` を実行する | `llm.generate_question()` はちょうど1回呼ばれ、`confirmation_point_content` は `confirmation_points[0]["content"]`、`confirmation_point_format` は `"knowledge"`、`past_answers` は `state["answers"]` と完全一致する。戻り値の `current_question_text` は stub が返した `question_text` と完全一致し、`current_answer_type` は `"textarea"` と完全一致する | 問い方の自然さや語彙選択そのものは client 側責務であり、この TC では node の受け渡し契約だけを検証する |
| TC-11 | `knowledge_and_practice` の形式情報を client へそのまま渡し、client 返却値を node がそのまま返す | stub `llm.generate_question()` が、確認ポイント `content="ジェネリクスを使った関数定義"`、`format="knowledge_and_practice"` を受け取ったとき `QuestionOutput(question_text="配列と判定関数を受け取り、条件に合う要素だけを返す `filterBy` を実装してください。例: `filterBy([1, 2, 3, 4], n => n > 2)` -> `[3, 4]`", answer_type="code")` を返す | `confirmation_points=[{"id":"cp_003","content":"ジェネリクスを使った関数定義","format":"knowledge_and_practice"}]`, `current_point_index=0`, `answers=[]` を含む `SessionState` で `deliver_question` を実行する | `llm.generate_question()` はちょうど1回呼ばれ、`confirmation_point_content` は `confirmation_points[0]["content"]`、`confirmation_point_format` は `"knowledge_and_practice"`、`past_answers` は `state["answers"]` と完全一致する。戻り値の `current_question_text` は stub が返した `question_text` と完全一致し、`current_answer_type` は `"code"` と完全一致する | TypeScript 構文のブラックリスト判定やシグネチャ非提示の内容検証は node の責務外であり、この TC では持ち込まない |
| TC-12 | セッション再開時に `QuizAnswer` 履歴をそのまま渡し、続きの確認ポイントから出題する | `state.answers` に `QuizAnswerRecord` 2件が保存済みで、`current_point_index=2`、`confirmation_points` は3件ある。`llm.generate_question()` は3件目確認ポイント向けの `QuestionOutput` を返す | 既存履歴2件を持つ `SessionState` を渡して `deliver_question(state, llm=...)` を実行する | `llm.generate_question()` は `title=state["roadmap_item_title"]`, `description=state["roadmap_item_description"]`, `confirmation_point_content=confirmation_points[2]["content"]`, `confirmation_point_format=confirmation_points[2]["format"]`, `past_answers=state["answers"]` でちょうど1回呼ばれる。戻り値は3件目に対する問題文を返す。`total_questions_asked` は既存値があれば `+1`、未設定なら `1` と完全一致する | 受け入れ基準「セッション再開時に続きから出題」「出題数更新ルール」に対応 |

## Phase 3: エッジケース

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-20 | 全確認ポイント消化済みなら出題せず停止する | `confirmation_points` が2件あり、`current_point_index=2` である。LLM 呼び出し回数を観測できる | `state={"roadmap_item_title":"TypeScript ジェネリクス","roadmap_item_description":"型パラメータと推論の理解を確認する","confirmation_points":[{"id":"cp_001","content":"ジェネリクスの必要性を説明できる","format":"knowledge"},{"id":"cp_002","content":"ジェネリック関数を実装できる","format":"knowledge_and_practice"}],"current_point_index":2,"answers":[...],"total_questions_asked":2}` を渡して `deliver_question(state, llm=...)` を実行する | 戻り値は空の dict `{}` と完全一致する。`llm.generate_question()` は0回呼ばれる。`current_question_text`、`current_answer_type`、`total_questions_asked` の更新は1件も返らない | 完了遷移自体は `answer_evaluation` の責務であるため、ここでは「出題停止」のみを検証する |
| TC-21 | 深掘りで追加された確認ポイントがあれば、その追加ポイントに基づいて出題する | ルーティング結果として `confirmation_points` の末尾に追加確認ポイント1件が追記済みで、`current_point_index` がその追加項目を指している。`llm.generate_question()` は追加ポイント向け `QuestionOutput` を返す | `confirmation_points=[既存2件, {"id":"cp_deep_001","content":"型推論が失敗するケースを説明できる","format":"knowledge"}]`, `current_point_index=2`, `answers` に既存履歴2件を持ち、`total_questions_asked=2` を明示した `SessionState` で `deliver_question(state, llm=...)` を実行する | `llm.generate_question()` の `confirmation_point_content` と `confirmation_point_format` は追加ポイント `cp_deep_001` の値と完全一致する。戻り値はその追加ポイントに対応する問題文を返し、`total_questions_asked` は `3` と完全一致する | 境界条件「深掘りが発生した場合」に対応 |

## Phase 4: 外部連携

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-30 | `QuestionDeliveryLlmClient` 正常系では1回の LLM 呼び出しで問題文を返し、失敗ログを出さない | `llm.generate_question()` が正常に `QuestionOutput` を返し、`structlog` 出力を観測できる | 任意の未完了 `SessionState` を渡して `deliver_question(state, llm=...)` を実行する | `llm.generate_question()` はちょうど1回呼ばれ、自動再試行は行われない。処理は非エラーで完了する。構造化ログ `event="question_delivery_failed"` は0件である | 外部連携の正常経路確認 |
| TC-31 | LLM 呼び出し失敗時は `QuestionDeliveryError` を1件ログ出力して再送出する | `llm.generate_question()` が、`__cause__` に依存先例外を持つ `QuestionDeliveryError(error_code="llm_request_failed", message="question delivery llm request failed")` を送出し、`structlog` 出力を観測できる | 任意の未完了 `SessionState` で `deliver_question(state, llm=...)` を実行する | `QuestionDeliveryError` が送出される。`error_code` は `llm_request_failed`、`message` は `question delivery llm request failed` と完全一致し、`__cause__` は元例外を保持する。`llm.generate_question()` はちょうど1回呼ばれ、自動再試行は行われない。構造化ログは `event="question_delivery_failed"` を持つログがちょうど1件出力される。必須キーは `event` のみとし、追加キーは許容する | 異常系 `llm_request_failed` |
| TC-32 | client 側の LLM 応答パース失敗時は `QuestionDeliveryError` を1件ログ出力して再送出する | stub `llm.generate_question()` が、raw LLM 応答の整形失敗を表す `QuestionDeliveryError(error_code="llm_response_parse_failed", message="question delivery llm response parse failed")` を `__cause__` 付きで送出し、`structlog` 出力を観測できる | 任意の未完了 `SessionState` で `deliver_question(state, llm=...)` を実行する | `QuestionDeliveryError` が送出される。`error_code` は `llm_response_parse_failed`、`message` は `question delivery llm response parse failed` と完全一致し、`__cause__` は元例外を保持する。`llm.generate_question()` はちょうど1回呼ばれ、自動再試行は行われない。構造化ログは `event="question_delivery_failed"` を持つログがちょうど1件出力される。必須キーは `event` のみとし、追加キーは許容する | parse 自体は client 側責務であり、node では再送出・非再試行・ログ1件のみを検証する |

# 網羅性チェック

仕様書の受け入れ基準の各項目に対応するテストケース ID を記載する。
全項目が少なくとも1つのテストケースでカバーされていることを確認する。

| 受け入れ基準 | 対応テストケース |
|---|---|
| 確認ポイントに基づいた問題文が生成される | TC-01, TC-02, TC-21 |
| `deliver_question(...)` は過去の問答履歴を `QuestionDeliveryLlmClient` へそのまま渡し、返却された問題文を改変せずに返す | TC-10, TC-12 |
| `knowledge` と `knowledge_and_practice` の違いは `QuestionDeliveryLlmClient` へ渡す `confirmation_point_format` と、返却される `answer_type` に反映される | TC-10, TC-11 |
| 問題文と一緒に `answer_type`（`textarea` / `code`）が返される | TC-01, TC-02, TC-10, TC-11 |
| `knowledge` は `textarea`、`knowledge_and_practice` は `code` を返す | TC-01, TC-02, TC-10, TC-11 |
| `QuestionDeliveryLlmClient` が返す `knowledge_and_practice` の問題文は、要件が文章で示され、少なくとも1件の具体例があり、シグネチャはコードで提示されない | TC-11 |
| 全確認ポイント完了後に出題が停止する | TC-20 |
| セッション再開時に続きから出題される | TC-12 |
| `total_questions_asked` は明示 state 値だけで更新され、未設定時は `1` になる | TC-01, TC-02, TC-12, TC-21 |

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
- concrete な prompt 品質評価、raw LLM 応答の解析、TypeScript 構文ブラックリスト判定はこの node 契約テストの対象外とする
