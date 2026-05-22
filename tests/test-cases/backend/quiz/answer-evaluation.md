---
status: ready
---

# テストケース一覧

# 検証焦点

| テストの種類 | 検証焦点 |
|---|---|
| Phase 1（最小骨格） | `evaluate_answer` の公開戻り値契約、`AnswerEvaluationLlmClient.evaluate_answer(...)` への 1 対 1 マッピング、`QuizAnswerRecord` 追記、`input_type="answer"` 正規化、`next` / `complete` の基本遷移 |
| Phase 2（コアロジック） | `deepdive` 時の末尾追記と index 更新、既存未消化ポイント優先の順序保証、20問収束時の `total_questions_asked` 受け渡しと `next_action` passthrough |
| Phase 3（エッジケース） | 空回答、構文エラーを含むコード回答、出題意図と無関係な回答 |
| Phase 4（外部連携） | `AnswerEvaluationLlmClient` 正常連携、`AnswerEvaluationError` の再送出、非再試行、構造化ログちょうど1件 |

## Phase 1: 最小骨格

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-01 | `next` 判定で公開戻り値・回答追記・form 経路正規化が行われる | `confirmation_points` が2件あり、`current_point_index=0`、`answers` に既存履歴1件がある。`input_source="form"` で `input_type` は未設定である。`llm.evaluate_answer()` は `EvaluationOutput(next_action="next", score=81, feedback="型安全性と再利用性の両方に触れられています。型引数が呼び出し側で推論される点まで言えるとより良いです。", deepdive_points=[])` を返す | `state={"current_question_text":"同じ処理を複数の型で再利用するとき、ジェネリクスが必要になる理由を説明してください","current_answer_type":"textarea","user_input":"型ごとに関数を複製せずに、型安全を保ったまま共通化できるからです","input_source":"form","confirmation_points":[{"id":"cp_001","content":"ジェネリクスの必要性と型安全性を説明できる","format":"knowledge"},{"id":"cp_002","content":"ジェネリック関数を実装できる","format":"knowledge_and_practice"}],"current_point_index":0,"answers":[{"question_number":1,"confirmation_point_id":"cp_000","question_text":"前問","answer_type":"textarea","answer_text":"前回回答","score":60,"feedback":"前回FB"}],"total_questions_asked":1}` を渡して `evaluate_answer(state, llm=...)` を実行する | `llm.evaluate_answer()` がちょうど1回呼ばれ、引数 `question_text`, `confirmation_point_content`, `answer_text`, `answer_type`, `past_answers`, `total_questions_asked` はそれぞれ `state["current_question_text"]`, `confirmation_points[0]["content"]`, `state["user_input"]`, `state["current_answer_type"]`, `state["answers"]`, `state["total_questions_asked"]` と完全一致する。戻り値はキー `next_action`, `answers`, `current_point_index`, `confirmation_points`, `input_type` のちょうど5件を持つ dict である。`next_action` は `"next"`、`current_point_index` は `1`、`confirmation_points` は入力と完全一致し、`input_type` は `"answer"` と完全一致する。`answers` は既存1件を順序そのままで保持したうえで新規1件だけ追記される。追記レコードは `QuizAnswerRecord` schema を満たし、`confirmation_point_id="cp_001"`, `question_text=state["current_question_text"]`, `answer_type="textarea"`, `answer_text=state["user_input"]`, `score=81`, `feedback` は LLM 返却値と完全一致する。`question_number` は int として存在することだけを確認し、具体的な採番規則は本 TC の対象外とする | spec 例の再現ではなく独立 fixture |
| TC-02 | `complete` 判定で完了境界へ進み、score / feedback が回答記録へ反映される | `confirmation_points` が2件あり、`current_point_index=1` で最後の確認ポイントを評価中である。`llm.evaluate_answer()` は `EvaluationOutput(next_action="complete", score=92, feedback="要点を過不足なく説明できています。", deepdive_points=[])` を返す | `state={"current_question_text":"型推論で型引数を省略できる理由を説明してください","current_answer_type":"textarea","user_input":"引数や戻り値から型Tを推論できるためです","input_source":"chat","input_type":"answer","confirmation_points":[{"id":"cp_001","content":"ジェネリクスの概念と必要性を説明できる","format":"knowledge"},{"id":"cp_002","content":"型推論と明示的型指定の違いを説明できる","format":"knowledge"}],"current_point_index":1,"answers":[],"total_questions_asked":2}` を渡して `evaluate_answer(state, llm=...)` を実行する | 戻り値の `next_action` は `"complete"` と完全一致する。`current_point_index` は `len(confirmation_points)` と完全一致し、この入力では `2` になる。`confirmation_points` は入力と完全一致し、`input_type` は `"answer"` と完全一致する。`answers` には新規レコードがちょうど1件追加され、その最新レコードの `score=92` と `feedback="要点を過不足なく説明できています。"` が完全一致で記録される。理解度判断は `next_action` / `score` / `feedback` に反映されることを確認し、別 rationale 保存の有無は本 TC の対象外とする | 受け入れ基準「complete」「score」「feedback」に対応 |

## Phase 2: コアロジック

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-10 | `deepdive` 判定で深掘りポイントを末尾追記しつつ現在問を消化する | `confirmation_points` が2件あり、`current_point_index=0`、`answers` に既存履歴1件がある。`llm.evaluate_answer()` は `EvaluationOutput(next_action="deepdive", score=45, feedback="概念説明はできていますが、型推論が崩れるケースの理解が曖昧です。", deepdive_points=[{"id":"cp_deep_001","content":"型推論が失敗するケースを説明できる","format":"knowledge"}])` を返す | `state={"current_question_text":"ジェネリクスの必要性を説明してください","current_answer_type":"textarea","user_input":"柔軟に型を扱えるからです","input_source":"chat","input_type":"answer","confirmation_points":[{"id":"cp_001","content":"ジェネリクスの必要性を説明できる","format":"knowledge"},{"id":"cp_002","content":"ジェネリック関数を実装できる","format":"knowledge_and_practice"}],"current_point_index":0,"answers":[{"question_number":1,"confirmation_point_id":"cp_000","question_text":"前問","answer_type":"textarea","answer_text":"前回回答","score":60,"feedback":"前回FB"}],"total_questions_asked":2}` を渡して `evaluate_answer(state, llm=...)` を実行する | 戻り値の `next_action` は `"deepdive"` と完全一致する。`current_point_index` は `1` と完全一致する。`confirmation_points` は既存2件を順序そのままで保持し、その末尾に `cp_deep_001` がちょうど1件追記された長さ3のリストになる。`answers` は既存1件を保持したうえで新規1件だけ追記され、追記レコードの `score=45`、`feedback` は LLM 返却値と完全一致する。`input_type` は `"answer"` と完全一致する | 深掘り追加と index 更新の基本 |
| TC-11 | `deepdive` でも既存の未消化ポイントがある場合は、それが追記済み deepdive ポイントより先に次問になる | mock `llm.evaluate_answer()` を使う node 単体テストである。`confirmation_points` が3件あり、`current_point_index=0` である。`llm.evaluate_answer()` は `EvaluationOutput(next_action="deepdive", score=46, feedback="必要性の説明はできていますが、境界条件で型推論が崩れるケースの理解が曖昧です。", deepdive_points=[{"id":"cp_deep_001","content":"境界条件で型推論が崩れる理由を説明できる","format":"knowledge"}])` を返す | `state={"current_question_text":"ジェネリクスの必要性を説明してください","current_answer_type":"textarea","user_input":"型を使い回せます","input_source":"chat","input_type":"answer","confirmation_points":[{"id":"cp_001","content":"ジェネリクスの必要性を説明できる","format":"knowledge"},{"id":"cp_002","content":"ジェネリック関数を実装できる","format":"knowledge_and_practice"},{"id":"cp_003","content":"型推論と明示的型指定の違いを説明できる","format":"knowledge"}],"current_point_index":0,"answers":[],"total_questions_asked":3}` を渡して `evaluate_answer(state, llm=...)` を実行する | 戻り値の `next_action` は `"deepdive"` と完全一致する。`current_point_index` は `1` と完全一致する。`confirmation_points[1]["id"]` は既存ポイント `cp_002` と完全一致し、末尾 `confirmation_points[3]["id"]` は追記済み deepdive ポイント `cp_deep_001` と完全一致する。追記された `answers` の最新レコードには `score=46` と `feedback` の LLM 返却値がそのまま記録される。したがって出力だけから、次問は `confirmation_points[current_point_index]` で一意に `cp_002` と判断でき、追記済み deepdive ポイントではないことを確認できる | mock `EvaluationOutput` を前提に、受け入れ基準「既存未消化ポイント優先」「出力だけで一意判断」に対応 |
| TC-12 | 20問収束条件では in-contract な `next` / `complete` に対する `total_questions_asked` 受け渡しと `next_action` passthrough のみを検証する | mock `llm.evaluate_answer()` を使う node 単体テストである。`llm.evaluate_answer()` の呼び出し引数を観測できる。`llm.evaluate_answer()` は `EvaluationOutput(next_action="complete", score=68, feedback="重要点は確認できたため収束します。", deepdive_points=[])` を返す | `state={"current_question_text":"型推論が失敗するケースを説明してください","current_answer_type":"textarea","user_input":"ユニオン型だと難しいです","input_source":"chat","input_type":"answer","confirmation_points":[{"id":"cp_001","content":"型推論が失敗するケースを説明できる","format":"knowledge"},{"id":"cp_002","content":"ジェネリック関数を実装できる","format":"knowledge_and_practice"}],"current_point_index":0,"answers":[],"total_questions_asked":20}` を渡して `evaluate_answer(state, llm=...)` を実行する | `llm.evaluate_answer()` は `total_questions_asked=20` でちょうど1回呼ばれる。戻り値の `next_action` は LLM 返却値どおり `"complete"` と完全一致し、node 側で `next` や `deepdive` へ上書きされない。`current_point_index` は `len(confirmation_points)` と完全一致する。`total_questions_asked >= 20` で concrete client が前提違反の `deepdive` を返すケースは spec 上 out-of-contract であり、本 TC 群の対象外とする。concrete client のプロンプト文面や内部の収束指示方法は本 TC の対象外とする | 20問収束ルールの node 契約 |

## Phase 3: エッジケース

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-20 | 空回答は `score=0`・回答促し feedback・`next` で処理される | `llm.evaluate_answer()` は空文字回答に対して `EvaluationOutput(next_action="next", score=0, feedback="回答が空です。まずは分かる範囲で回答してください。", deepdive_points=[])` を返す | `state={"current_question_text":"ジェネリクスの必要性を説明してください","current_answer_type":"textarea","user_input":"","input_source":"form","confirmation_points":[{"id":"cp_001","content":"ジェネリクスの必要性を説明できる","format":"knowledge"},{"id":"cp_002","content":"ジェネリック関数を実装できる","format":"knowledge_and_practice"}],"current_point_index":0,"answers":[],"total_questions_asked":1}` を渡して `evaluate_answer(state, llm=...)` を実行する | `llm.evaluate_answer()` は `answer_text=""` でちょうど1回呼ばれる。戻り値の `next_action` は `"next"`、`current_point_index` は `1`、`input_type` は `"answer"` と完全一致する。追記された `answers` の新規レコードは `answer_text=""`, `score=0`, `feedback="回答が空です。まずは分かる範囲で回答してください。"` と完全一致する。`deepdive` は発生せず、`confirmation_points` 追記は0件である | 境界条件「空回答」に対応 |
| TC-21 | 実践問題で構文エラーのあるコードでも、意図を汲んだ `EvaluationOutput` がそのまま公開契約へ反映される | mock `llm.evaluate_answer()` を使う node 単体テストである。現在問は `current_answer_type="code"` の実践問題である。入力コードは構文エラーを含むが、フィルタ処理を実装しようとした意図は読み取れる。`llm.evaluate_answer()` は `EvaluationOutput(next_action="deepdive", score=58, feedback="`items.filter(pred)` を使おうとしている点から、条件に合う要素を返す意図は正しく捉えられています。一方で `items.filter(pred` の閉じ括弧と関数終端が欠けており構文エラーになっています。構文を修正したうえで、ジェネリック関数として最後まで書き切れるとより良いです。", deepdive_points=[{"id":"cp_deep_001","content":"構文を修正したジェネリック filter 関数を完成できる","format":"knowledge_and_practice"}])` を返す | `state={"current_question_text":"配列と判定関数を受け取り、条件に合う要素だけを返す `filterBy` を実装してください","current_answer_type":"code","user_input":"function filterBy<T>(items: T[], pred: (item: T) => boolean) { return items.filter(pred }","input_source":"chat","input_type":"answer","confirmation_points":[{"id":"cp_001","content":"ジェネリック関数を実装できる","format":"knowledge_and_practice"}],"current_point_index":0,"answers":[],"total_questions_asked":4}` を渡して `evaluate_answer(state, llm=...)` を実行する | 処理は非エラーで完了する。戻り値の `next_action` は `"deepdive"` と完全一致する。追記された `answers` の新規レコードには `score=58` と上記 `feedback` が完全一致で記録される。`feedback` には少なくとも1件の構文指摘と、少なくとも1件の実装意図を汲んだ評価コメントが含まれる。`confirmation_points` 末尾には `cp_deep_001` が追記される。コード実行による正誤判定や concrete client の生成品質は本 TC の対象外とする | 境界条件「構文エラーのあるコード」を mock 返却値の伝播として検証 |
| TC-22 | 出題意図と無関係な回答でも、出題意図を説明し直す `EvaluationOutput` がそのまま公開契約へ反映される | mock `llm.evaluate_answer()` を使う node 単体テストである。現在問はジェネリクスに関する知識問題である。入力回答は非同期処理の説明であり出題意図と無関係である。`llm.evaluate_answer()` は `EvaluationOutput(next_action="deepdive", score=12, feedback="この質問が確認したいのは Promise ではなく、ジェネリクスの概念と、なぜ複数の型で再利用しながら型安全を保つために必要なのかという点です。その観点で説明し直してください。", deepdive_points=[{"id":"cp_deep_001","content":"ジェネリクスの概念と必要性を自分の言葉で説明できる","format":"knowledge"}])` を返す | `state={"current_question_text":"ジェネリクスとは何か、なぜ必要か説明してください","current_answer_type":"textarea","user_input":"Promiseは非同期処理を扱うための仕組みです","input_source":"chat","input_type":"answer","confirmation_points":[{"id":"cp_001","content":"ジェネリクスの概念と必要性を説明できる","format":"knowledge"}],"current_point_index":0,"answers":[],"total_questions_asked":5}` を渡して `evaluate_answer(state, llm=...)` を実行する | 処理は非エラーで完了する。戻り値の `next_action` は `"deepdive"` と完全一致する。追記された `answers` の新規レコードには `score=12` と上記 `feedback` が完全一致で記録される。`feedback` には少なくとも1件の「質問はジェネリクスの概念と必要性を確認している」旨の説明し直しが含まれる。`confirmation_points` 末尾には `cp_deep_001` が追記される。公開契約に厳密な low-score band は含まれず、LLM の hidden reasoning や concrete client の生成品質は本 TC の対象外とする | 境界条件「無関係回答」を mock 返却値の伝播として検証 |

## Phase 4: 外部連携

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-30 | `AnswerEvaluationLlmClient` 正常系では1回の LLM 呼び出しで完了し、失敗ログを出さない | `llm.evaluate_answer()` が正常に `EvaluationOutput(next_action="next", score=80, feedback="概ね理解できています。", deepdive_points=[])` を返し、`structlog` 出力を観測できる | 任意の未完了 `SessionState` を渡して `evaluate_answer(state, llm=...)` を実行する | `llm.evaluate_answer()` はちょうど1回呼ばれ、自動再試行は行われない。処理は非エラーで完了する。構造化ログ `event="answer_evaluation_failed"` は0件である | 外部連携の正常経路確認 |
| TC-31 | LLM 呼び出し自体の失敗時は `AnswerEvaluationError` を1件ログ出力して再送出する | `llm.evaluate_answer()` が、`__cause__` に依存先例外を持つ `AnswerEvaluationError(error_code="llm_request_failed", message="answer evaluation llm request failed")` を送出し、`structlog` 出力を観測できる | 任意の未完了 `SessionState` で `evaluate_answer(state, llm=...)` を実行する | `AnswerEvaluationError` が送出される。`error_code` は `llm_request_failed`、`message` は `answer evaluation llm request failed` と完全一致し、`__cause__` は元例外を保持する。`llm.evaluate_answer()` はちょうど1回呼ばれ、自動再試行は行われない。構造化ログは `event="answer_evaluation_failed"` を持つログがちょうど1件出力される。必須キーは `event` のみとし、追加キーは許容する | 異常系 `llm_request_failed` |
| TC-32 | LLM 応答の評価結果抽出失敗時は `AnswerEvaluationError` を1件ログ出力して再送出する | `llm.evaluate_answer()` が、`__cause__` にパース例外を持つ `AnswerEvaluationError(error_code="llm_response_parse_failed", message="answer evaluation llm response parse failed")` を送出し、`structlog` 出力を観測できる | 任意の未完了 `SessionState` で `evaluate_answer(state, llm=...)` を実行する | `AnswerEvaluationError` が送出される。`error_code` は `llm_response_parse_failed`、`message` は `answer evaluation llm response parse failed` と完全一致し、`__cause__` は元例外を保持する。`llm.evaluate_answer()` はちょうど1回呼ばれ、自動再試行は行われない。構造化ログは `event="answer_evaluation_failed"` を持つログがちょうど1件出力される。必須キーは `event` のみとし、追加キーは許容する | 異常系 `llm_response_parse_failed` |

# 網羅性チェック

仕様書の受け入れ基準の各項目に対応するテストケース ID を記載する。
全項目が少なくとも1つのテストケースでカバーされていることを確認する。

| 受け入れ基準 | 対応テストケース |
|---|---|
| `evaluate_answer(state, ...)` の required input state keys と LLM 引数への 1 対 1 マッピングが定義されている | TC-01 |
| 次のアクション（next / deepdive / complete）が判断される | TC-01, TC-02, TC-10 |
| score が 0〜100 で算出され、追記後 `answers` の最新 `QuizAnswerRecord` から観測できる | TC-01, TC-02, TC-20, TC-21, TC-22 |
| ユーザー向けの feedback が生成され、追記後 `answers` の最新 `QuizAnswerRecord` から観測できる | TC-01, TC-02, TC-20, TC-21, TC-22 |
| 深掘り時に追加の確認ポイントが含まれる | TC-10 |
| 深掘り時の出力だけで、次問が既存ポイントか追記済み deepdive ポイントかを `confirmation_points` と `current_point_index` から一意に判断できる | TC-11 |
| `total_questions_asked >= 20` の評価では、20問収束シグナルが LLM に渡され、in-contract な `next` / `complete` 返却に対して LLM の `next_action` を node 側で上書きしない | TC-12 |
| 結果が shared contract `QuizAnswerRecord` に従って `answers` へ追記される | TC-01, TC-02, TC-10, TC-20 |
| `input_source="form"` の場合、評価完了時に `input_type="answer"` が設定される | TC-01, TC-20 |

補足:
- 理解度判断の別 rationale 保存は仕様上スコープ外のため、TC では検証しない
- 無関係回答時の厳密な low-score band も仕様上の公開契約ではないため、TC-22 は feedback と非エラー完了を主に検証する

# 記述ルール

- 仕様書に明記された振る舞いだけを前提にする
- 公開契約に含まれない prompt 文言、hidden reasoning、内部採番規則は期待結果に置かない
- 正常系・境界系・異常系が重複なく網羅されていることを確認する
- 仕様書の受け入れ基準の各項目に対応するテストケースが最低1つあることを確認する
- 期待結果に「含まれる」「完全一致」「少なくとも1件」「ちょうど1件」などの検証粒度を明示する
- ログ検証を含む場合は、検証対象イベント名、必須キー、期待値、件数制約、追加キー許容の有無を明示する
- 例外検証を含む場合は、例外型、message、cause chain、ログ記録有無のうち何を確認するかを明示する
- テストが「存在確認」なのか「内容検証」なのかを期待結果で区別して書く
- テストケース文書に書いていない検証を impl レビューで追加要求しなくて済む粒度まで、期待結果を具体化する
