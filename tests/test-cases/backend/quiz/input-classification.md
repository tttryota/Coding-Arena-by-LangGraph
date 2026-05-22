---
status: ready
---

# テストケース一覧

# 検証焦点

| テストの種類 | 検証焦点 |
|---|---|
| Phase 1（最小骨格） | `input_source` による経路分岐、`classify_input(...)` の公開戻り値契約、`current_question_text` / `user_input` の LLM への 1 対 1 マッピング |
| Phase 2（コアロジック） | `answer` / `question` / `explanation_request` の分類結果反映、曖昧入力の `answer` 優先を `InputClassificationLlmClient` を含む統合前提で確認 |
| Phase 3（エッジケース） | 空文字列、極端に短い入力（1-2文字）の `answer` 扱いを `InputClassificationLlmClient` の分類契約として確認 |
| Phase 4（外部連携） | `InputClassificationLlmClient` 正常連携、`InputClassificationError` の再送出、`__cause__` 保持、非再試行、失敗時の構造化ログのイベント名と件数制約 |

## Phase 1: 最小骨格

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-01 | `input_source="chat"` のとき `current_question_text` と `user_input` を LLM に渡し、分類結果を `input_type` として返す | `llm.classify_input()` の呼び出し引数を観測できる。`llm.classify_input()` は `"answer"` を返す | `state={"input_source":"chat","current_question_text":"TypeScript のジェネリクスが必要な理由を説明してください","user_input":"型安全を保ったまま共通化できるからです"}` を渡して `classify_input(state, llm=...)` を実行する | `llm.classify_input()` はちょうど1回呼ばれ、`question_text` は `state["current_question_text"]`、`user_input` は `state["user_input"]` と完全一致する。戻り値はキー `input_type` のみを持つ dict として存在し、`input_type` は `"answer"` と完全一致する | 受け入れ基準「LLM が `current_question_text` と `user_input` を使って分類する」「分類結果が `input_type` として設定される」に対応 |
| TC-02 | `input_source="form"` では分類処理に入らず `answer_evaluation` に直接遷移する | 分類処理の実行有無と遷移先を観測できるルーティング層のテストである | `input_source="form"` を含む入力イベントを受けて、回答評価までの分岐処理を実行する | 分類処理は実行されない。遷移先は `answer_evaluation` と完全一致する。`InputClassificationLlmClient` への呼び出しは 0 回である | 本仕様の基本動作の経路分岐を feature レベルで確認する。LangGraph の登録ノード名文字列は検証対象に含めない |

## Phase 2: コアロジック

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-10 | 出題内容の意味や前提に関する質問は `question` に分類される | `input_source="chat"` である。`llm.classify_input()` は `"question"` を返す | `state={"input_source":"chat","current_question_text":"ジェネリクスが必要な理由を説明してください","user_input":"ここでいう型安全って何を指していますか？"}` を渡して `classify_input(state, llm=...)` を実行する | 戻り値の `input_type` は `"question"` と完全一致する。後続ノード判定に必要な分類値として `question` が存在確認ではなく内容検証で設定される | 後続ノード `chat_response` に接続される分類 |
| TC-11 | 「わからない」「解説して」などの意思表示は `explanation_request` に分類される | `input_source="chat"` である。`llm.classify_input()` は `"explanation_request"` を返す | `state={"input_source":"chat","current_question_text":"ジェネリクスが必要な理由を説明してください","user_input":"わからないので解説してください"}` を渡して `classify_input(state, llm=...)` を実行する | 戻り値の `input_type` は `"explanation_request"` と完全一致する。後続ノード判定に必要な分類値として `explanation_request` が内容検証で設定される | 後続ノード `explanation_generation` に接続される分類 |
| TC-12 | 曖昧な入力は `answer` として扱う | `input_source="chat"` である。`InputClassificationLlmClient` を含む統合前提で分類処理を実行する。曖昧入力を `answer` と判定する責務は client 側にある | `state={"input_source":"chat","current_question_text":"ジェネリクスが必要な理由を説明してください","user_input":"たぶん型のため"}` を入力として分類処理を実行する | 分類結果は `input_type="answer"` と完全一致する。`question` や `explanation_request` へは分類されない。node 側の事前分岐有無は本ケースの検証対象に含めない | 受け入れ基準「曖昧な入力は answer として扱われる」に対応する統合ケース |

## Phase 3: エッジケース

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-20 | 空文字列は `answer` として扱う | `input_source="chat"` である。`InputClassificationLlmClient` を含む統合前提で分類処理を実行する。空文字列を `answer` と判定する責務は client 側にある | `state={"input_source":"chat","current_question_text":"ジェネリクスが必要な理由を説明してください","user_input":""}` を入力として分類処理を実行する | 分類結果は `input_type="answer"` と完全一致する。空入力であっても `question` や `explanation_request` には分類されない。node 側の short-circuit 有無は本ケースの検証対象に含めない | 境界条件「空文字列の入力」に対応する統合ケース |
| TC-21 | 1-2文字の極端に短い入力は `answer` として扱う | `input_source="chat"` である。`InputClassificationLlmClient` を含む統合前提で分類処理を実行する。1-2文字入力を `answer` と判定する責務は client 側にある | `state={"input_source":"chat","current_question_text":"ジェネリクスが必要な理由を説明してください","user_input":"？"}` および `state["user_input"]="うー"` の 2 パターンで分類処理を実行する | いずれの入力でも分類結果は `input_type="answer"` と完全一致する。1文字ケース、2文字ケースの両方で `question` や `explanation_request` に分類されない。node 側の short-circuit 有無は本ケースの検証対象に含めない | 境界条件「極端に短い入力（1-2文字）」に対応する統合ケース |

## Phase 4: 外部連携

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-30 | LLM 正常系では 1 回の呼び出しで分類が完了する | `llm.classify_input()` が正常に `"question"` を返す | 任意の `input_source="chat"` の `SessionState` を渡して `classify_input(state, llm=...)` を実行する | `llm.classify_input()` はちょうど1回呼ばれ、自動再試行は行われない。処理は非エラーで完了する | node の委譲契約と正常経路確認。失敗時ログのイベント名と件数は TC-31 / TC-32 で確認する |
| TC-31 | LLM 呼び出し自体の失敗時は `InputClassificationError` を 1 件ログ出力して再送出する | `llm.classify_input()` が `InputClassificationError(error_code="llm_request_failed", message="input classification llm request failed")` を送出し、`__cause__` に元例外が設定されている。`structlog` 出力を観測できる | 任意の `input_source="chat"` の `SessionState` で `classify_input(state, llm=...)` を実行する | `InputClassificationError` が送出される。`error_code` は `llm_request_failed`、`message` は `input classification llm request failed` と完全一致し、`__cause__` は元例外を保持する。`llm.classify_input()` はちょうど1回呼ばれ、自動再試行は行われない。構造化ログは `event="input_classification_failed"` を持つログがちょうど1件出力される。ログ payload の追加キーや詳細キー集合は検証対象に含めない | 異常系 `llm_request_failed` |
| TC-32 | LLM 応答から分類結果を抽出できないときは `InputClassificationError` を 1 件ログ出力して再送出する | `llm.classify_input()` が `InputClassificationError(error_code="llm_response_parse_failed", message="input classification llm response parse failed")` を送出し、`__cause__` にパース元例外が設定されている。`structlog` 出力を観測できる | 任意の `input_source="chat"` の `SessionState` で `classify_input(state, llm=...)` を実行する | `InputClassificationError` が送出される。`error_code` は `llm_response_parse_failed`、`message` は `input classification llm response parse failed` と完全一致し、`__cause__` は元例外を保持する。`llm.classify_input()` はちょうど1回呼ばれ、自動再試行は行われない。構造化ログは `event="input_classification_failed"` を持つログがちょうど1件出力される。ログ payload の追加キーや詳細キー集合は検証対象に含めない | 異常系 `llm_response_parse_failed` |

# 網羅性チェック

仕様書の受け入れ基準の各項目に対応するテストケース ID を記載する。
全項目が少なくとも1つのテストケースでカバーされていることを確認する。

| 受け入れ基準 | 対応テストケース |
|---|---|
| ユーザー入力が answer / question / explanation_request のいずれかに分類される | TC-01, TC-10, TC-11 |
| 分類結果が `input_type` として設定される | TC-01, TC-10, TC-11, TC-12 |
| 曖昧な入力は answer として扱われる | TC-12 |
| LLM が `current_question_text` と `user_input` を使って分類する | TC-01 |
| `classify_input(...)` ノードは LLM client を1回だけ呼び出し、その返却値を `input_type` に反映する | TC-01, TC-30 |

# 記述ルール

- 仕様書に明記された振る舞いだけを前提にする
- 仕様未記載の振る舞いを期待結果に置く場合は `[要仕様追記]` タグを付ける
- 正常系・境界系・異常系が重複なく網羅されていることを確認する
- 仕様書の受け入れ基準の各項目に対応するテストケースが最低1つあることを確認する
- 期待結果に「含まれる」「完全一致」「少なくとも1件」「ちょうど1件」などの検証粒度を明示する
- ログ検証を含む場合は、少なくとも検証対象イベント名と件数制約を明示し、payload の必須キーや追加キー許容は仕様で契約されている場合に限って記載する
- 正常系 testcase では、仕様に明記されていない失敗ログ抑止を期待結果に含めない
- 例外検証を含む場合は、例外型、message、cause chain、ログ記録有無のうち何を確認するかを明示する
- テストが「存在確認」なのか「内容検証」なのかを期待結果で区別して書く
- テストケース文書に書いていない検証を impl レビューで追加要求しなくて済む粒度まで、期待結果を具体化する
