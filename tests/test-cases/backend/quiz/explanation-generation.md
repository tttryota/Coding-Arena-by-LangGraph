---
status: ready
---

# テストケース一覧

# 検証焦点

| テストの種類 | 検証焦点 |
|---|---|
| Phase 1（最小骨格） | `generate_explanation` の公開戻り値契約、必須 read-only state の参照、RAG→LLM の基本呼び出し順、現在の確認ポイントを変えずに downstream へ引き渡す非破壊性 |
| Phase 2（コアロジック） | 関連ノートチャンクの受け渡し、ノート内容と汎用知識を組み合わせた解説文の返却、関連チャンク0件時の継続 |
| Phase 3（エッジケース） | 同一確認ポイントでの複数回解説依頼、別角度再出題文を `current_question_text` として受け取る再解説依頼、会話履歴依存の差分生成やscore制御を要求しないこと |
| Phase 4（外部連携） | `ExplanationGenerationError` の再送出、非再試行、`structlog` 構造化ログちょうど1件、正常時の非エラーログ確認、RAG/LLM の失敗契約の順守 |

## Phase 1: 最小骨格

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-01 | 解説依頼に対して、RAG検索と解説生成を1回ずつ実行して `{"explanation_text": str}` を返す | `rag.search_related_chunks()` は関連チャンク2件を返す。`llm.generate_explanation()` は `"あなたのノートには『型パラメータは関数に型の柔軟性を持たせる』とあります。補足すると、呼び出しごとに具体型を変えても型安全を保てます。"` を返す | `state={"current_question_text":"ジェネリクスの型パラメータとは何か説明してください","confirmation_points":[{"id":"cp_001","content":"ジェネリクスの型パラメータの役割を説明できる","format":"knowledge"}],"current_point_index":0}` を渡して `generate_explanation(state, rag=..., llm=...)` を実行する | `rag.search_related_chunks()` がちょうど1回呼ばれ、その引数 `query` は `ジェネリクスの型パラメータとは何か説明してください\nジェネリクスの型パラメータの役割を説明できる` と完全一致する。その後に `llm.generate_explanation()` がちょうど1回呼ばれる。`llm.generate_explanation()` の `question_text` は `state["current_question_text"]`、`confirmation_point_content` は `confirmation_points[0]["content"]`、`note_chunks` は RAG 返却値2件と完全一致する。戻り値はキー `explanation_text` のちょうど1件を持つ dict であり、値は LLM 返却文と完全一致する。`input_type` の有無や値には依存しない | 受け入れ基準「ユーザーが出題後に解説を依頼できる」「RAGで関連チャンクが検索される」に対応 |
| TC-02 | 解説生成は現在の確認ポイントを進めず、同一確認ポイントを保持したまま downstream に制御を返せる | `rag.search_related_chunks()` と `llm.generate_explanation()` は正常完了する。`current_point_index=1` を指す `confirmation_points` が2件ある | `confirmation_points` が2件あり `current_point_index=1` の `SessionState` を渡して `generate_explanation` を実行する | 戻り値は `{"explanation_text": str}` と完全一致し、`current_point_index`、`confirmation_points`、`answers`、`total_questions_asked`、`score` を返さない。呼び出し後も入力 `state["current_point_index"]` は `1` のままで、`confirmation_points` の内容も変化しない。したがって、graph は同一確認ポイントを参照できる状態のまま downstream へ制御を返せる。`question_delivery` 自体の分岐や再出題実行は本TCの検証対象に含めない | 受け入れ基準「解説後に同じ確認ポイントを別の角度から再出題」に対する本ノードの責務を検証する |

## Phase 2: コアロジック

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-10 | ノート内容と LLM の汎用知識を組み合わせた解説文がそのまま返る | `rag.search_related_chunks()` は `["TypeScript入門.md: 型パラメータは関数に型の柔軟性を持たせる", "TypeScript入門.md: any ではなく具体型を保ったまま再利用できる"]` を返す。`llm.generate_explanation()` は `"あなたのノートには『型パラメータは関数に型の柔軟性を持たせる』『any ではなく具体型を保ったまま再利用できる』と書いてあります。補足すると、呼び出し側ごとに型推論が働くため、再利用性と型安全性を両立できます。"` を返す | `state={"current_question_text":"ジェネリクスの型パラメータとは何か説明してください","confirmation_points":[{"id":"cp_001","content":"ジェネリクスの型パラメータの役割を説明できる","format":"knowledge"}],"current_point_index":0}` を渡して `generate_explanation` を実行する | `llm.generate_explanation()` は `note_chunks` に上記2件を順序そのままで受け取る。戻り値の `explanation_text` は LLM 返却文と完全一致する。`explanation_text` には少なくとも1件のノート参照表現と、少なくとも1件の汎用知識による補足説明が含まれる | 受け入れ基準「ノート内容とLLMの汎用知識を組み合わせた解説」に対応 |
| TC-11 | ノートに関連チャンクがなくても、汎用知識のみで解説を生成する | `rag.search_related_chunks()` は空リスト `[]` を返す。`llm.generate_explanation()` は `"型パラメータは処理の形を保ったまま具体型だけ差し替えるために使います。"` を返す | `state={"current_question_text":"ジェネリクスの型パラメータとは何か説明してください","confirmation_points":[{"id":"cp_001","content":"ジェネリクスの型パラメータの役割を説明できる","format":"knowledge"}],"current_point_index":0}` を渡して `generate_explanation` を実行する | `rag.search_related_chunks()` がちょうど1回呼ばれ、`llm.generate_explanation()` は `note_chunks=[]` でちょうど1回呼ばれる。処理は非エラーで完了し、戻り値はキー `explanation_text` のちょうど1件を持つ dict であり、値は LLM 返却文と完全一致する | 境界条件「ノートに関連チャンクがない」に対応し、受け入れ基準「ない場合も解説が生成される」を満たす |

## Phase 3: エッジケース

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-20 | 1つの確認ポイントで複数回解説依頼しても、毎回非エラーで解説を返せる | 同一の `current_question_text` と `current_point_index` に対して `generate_explanation` を2回連続で呼ぶ。各回の `rag.search_related_chunks()` と `llm.generate_explanation()` は正常完了する | 同一 `SessionState` で `generate_explanation` を2回実行する | 1回目・2回目とも処理は非エラーで完了し、それぞれの戻り値はキー `explanation_text` のちょうど1件を持つ dict である。2回の呼び出しを通じて `current_point_index` と `confirmation_points` は変化せず、同一確認ポイントを維持する。解説文が前回と異なることや `"前回の解説ではこう説明しましたが"` のような会話履歴依存表現は期待しない | 境界条件「複数回解説依頼を許容」に対応 |
| TC-21 | 別角度再出題文が `current_question_text` に入っていても、再度解説依頼できる | `current_question_text` は spec 具体例の別角度再出題文 `"では、<T>を使わずにany型で書いた場合と比べて、型パラメータを使うメリットは何でしょうか？"` と完全一致する。`rag.search_related_chunks()` と `llm.generate_explanation()` は正常完了する | `state={"current_question_text":"では、<T>を使わずにany型で書いた場合と比べて、型パラメータを使うメリットは何でしょうか？","confirmation_points":[{"id":"cp_001","content":"ジェネリクスの型パラメータの役割を説明できる","format":"knowledge"}],"current_point_index":0}` を渡して `generate_explanation` を実行する | 処理は非エラーで完了し、戻り値は `{"explanation_text": str}` の形で返る。`current_point_index` は進まず、`confirmation_points` も変更されない。したがって、本ノードは別角度再出題文を受け取った場合でも、同一確認ポイントを維持したまま downstream に制御を返せる。`question_delivery` の分岐や再出題実行は本TCの検証対象に含めない | 境界条件「再出題でも再度解説依頼」を本ノード責務に限定して検証する |

## Phase 4: 外部連携

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-30 | 正常系では RAG と LLM を各1回だけ呼び、失敗ログを出さない | `rag.search_related_chunks()` が正常に関連チャンクを返し、`llm.generate_explanation()` が正常に解説文を返す。`structlog` 出力を観測できる | 任意の未完了 `SessionState` を渡して `generate_explanation(state, rag=..., llm=...)` を実行する | `rag.search_related_chunks()` はちょうど1回、`llm.generate_explanation()` もちょうど1回呼ばれ、自動再試行は行われない。処理は非エラーで完了する。構造化ログ `event="explanation_generation_failed"` は0件である | 外部連携の正常経路確認 |
| TC-31 | RAG検索失敗時は `ExplanationGenerationError` を1件ログ出力して再送出する | `rag.search_related_chunks()` が、RAG client 契約どおり `__cause__` に依存先例外を持つ `ExplanationGenerationError(error_code="rag_search_failed", message="explanation generation rag search failed")` を送出し、`structlog` 出力を観測できる | 任意の未完了 `SessionState` で `generate_explanation(state, rag=..., llm=...)` を実行する | `ExplanationGenerationError` が送出される。`error_code` は `rag_search_failed`、`message` は `explanation generation rag search failed` と完全一致し、`__cause__` は元例外を保持する。`rag.search_related_chunks()` はちょうど1回呼ばれ、`llm.generate_explanation()` は0回である。自動再試行は行われない。構造化ログは `event="explanation_generation_failed"` を持つログがちょうど1件出力される。必須キーは `event` のみとし、追加キーは許容する | 異常系 `rag_search_failed` |
| TC-32 | LLM呼び出し失敗時は `ExplanationGenerationError` を1件ログ出力して再送出する | `rag.search_related_chunks()` は正常に関連チャンクを返す。`llm.generate_explanation()` が、`__cause__` に依存先例外を持つ `ExplanationGenerationError(error_code="llm_request_failed", message="explanation generation llm request failed")` を送出し、`structlog` 出力を観測できる | 任意の未完了 `SessionState` で `generate_explanation(state, rag=..., llm=...)` を実行する | `ExplanationGenerationError` が送出される。`error_code` は `llm_request_failed`、`message` は `explanation generation llm request failed` と完全一致し、`__cause__` は元例外を保持する。`rag.search_related_chunks()` はちょうど1回、`llm.generate_explanation()` も1回だけ呼ばれ、自動再試行は行われない。構造化ログは `event="explanation_generation_failed"` を持つログがちょうど1件出力される。必須キーは `event` のみとし、追加キーは許容する | 異常系 `llm_request_failed` |
| TC-33 | LLM応答から解説テキストを抽出できない場合は `ExplanationGenerationError` を1件ログ出力して再送出する | `rag.search_related_chunks()` は正常に関連チャンクを返す。`llm.generate_explanation()` が、`__cause__` にパース例外を持つ `ExplanationGenerationError(error_code="llm_response_parse_failed", message="explanation generation llm response parse failed")` を送出し、`structlog` 出力を観測できる | 任意の未完了 `SessionState` で `generate_explanation(state, rag=..., llm=...)` を実行する | `ExplanationGenerationError` が送出される。`error_code` は `llm_response_parse_failed`、`message` は `explanation generation llm response parse failed` と完全一致し、`__cause__` は元例外を保持する。`rag.search_related_chunks()` はちょうど1回、`llm.generate_explanation()` も1回だけ呼ばれ、自動再試行は行われない。構造化ログは `event="explanation_generation_failed"` を持つログがちょうど1件出力される。必須キーは `event` のみとし、追加キーは許容する | 異常系 `llm_response_parse_failed` |

# 網羅性チェック

仕様書の受け入れ基準の各項目に対応するテストケース ID を記載する。
全項目が少なくとも1つのテストケースでカバーされていることを確認する。

| 受け入れ基準 | 対応テストケース |
|---|---|
| ユーザーが出題後に解説を依頼できる | TC-01, TC-21 |
| RAGでユーザーのノートから関連チャンクが検索される | TC-01, TC-30, TC-31 |
| ノート内容とLLMの汎用知識を組み合わせた解説が生成される | TC-10 |
| 解説後も `current_point_index` と `confirmation_points` を維持したまま、graph の `explanation_generation -> question_delivery` ルートで同じ確認ポイントの別角度再出題へ接続できる | TC-02, TC-21 |
| ノートに関連チャンクがない場合も解説が生成される | TC-11 |

この対応付けでカバーするのは、`explanation_generation` ノード単体で観測可能な入力条件と非破壊性のみである。`question_delivery` による実際の分岐や別角度再出題の実行は、この TC 群の受け入れ対象に含めない。

# 記述ルール

- 仕様書に明記された振る舞いだけを前提にする
- 仕様未記載の振る舞いは期待結果に置かない
- 正常系・境界系・異常系が重複なく網羅されていることを確認する
- 仕様書の受け入れ基準の各項目に対応するテストケースが最低1つあることを確認する
- 期待結果に「含まれる」「完全一致」「少なくとも1件」「ちょうど1件」などの検証粒度を明示する
- ログ検証を含む場合は、検証対象イベント名、必須キー、期待値、件数制約、追加キー許容の有無を明示する
- 例外検証を含む場合は、例外型、message、cause chain、ログ記録有無のうち何を確認するかを明示する
- テストが「存在確認」なのか「内容検証」なのかを期待結果で区別して書く
- テストケース文書に書いていない検証を impl レビューで追加要求しなくて済む粒度まで、期待結果を具体化する
