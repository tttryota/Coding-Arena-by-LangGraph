---
feature: answer-evaluation
status: ready
reviewed_by:
approved_at:
---

## 機能概要

ユーザーの回答をLLMが評価し、理解度判断にもとづく `next_action` の決定、`score` の算出、`feedback` の生成を1つのノードで行う。深掘り判断（ルーティング）もこのノードに統合されている。

`SessionState` / `ConfirmationPoint` / `QuizAnswerRecord` の共有契約は `session-state.md` と `backend/quiz/domain/session_state.py` を authoritative source とし、本仕様では `answer_evaluation` ノードがその共有契約をどう読むか、何を公開出力として返すかだけを定義する。

## 入力 state 契約

`evaluate_answer(state: SessionState, ...)` は少なくとも以下の共有 state keys を読む。

| キー | 用途 |
|---|---|
| `current_question_text` | LLM 引数 `question_text` と回答記録 `question_text` の元データ |
| `current_answer_type` | LLM 引数 `answer_type` と回答記録 `answer_type` の元データ |
| `user_input` | LLM 引数 `answer_text` と回答記録 `answer_text` の元データ |
| `confirmation_points` | 現在評価中の確認ポイントを引く元データ |
| `current_point_index` | 現在評価中の確認ポイント位置 |
| `answers` | LLM 引数 `past_answers` と追記先 |
| `total_questions_asked` | LLM 引数 `total_questions_asked` と 20問収束シグナル |
| `input_source` | `form` 経路の `input_type="answer"` 正規化判定 |

`input_type` は `input_source="chat"` では入力時点で `"answer"` が設定済みであることを前提とし、`input_source="form"` では未設定を許容する。ただし本ノード完了時には常に `input_type="answer"` を公開出力へ含める。

現在評価中の確認ポイントは以下の 1 対 1 マッピングで決定する。

```python
confirmation_point = state["confirmation_points"][state["current_point_index"]]
confirmation_point_content = confirmation_point["content"]
confirmation_point_id = confirmation_point["id"]
```

LLM への入力マッピングは以下に固定する。

```python
llm.evaluate_answer(
    question_text=state["current_question_text"],
    confirmation_point_content=confirmation_point_content,
    answer_text=state["user_input"],
    answer_type=state["current_answer_type"],
    past_answers=state["answers"],
    total_questions_asked=state["total_questions_asked"],
)
```

## 公開出力契約

本ノードの externally observable contract は、戻り値 dict と更新後 `answers` の内容で表す。

- 戻り値は `{"next_action": str, "answers": list[QuizAnswerRecord], "current_point_index": int, "confirmation_points": list[ConfirmationPoint], "input_type": "answer"}` を返す
- `next_action` は LLM の判断結果を返す
- `score` と `feedback` は、戻り値トップレベルではなく追記後 `answers` の最新 `QuizAnswerRecord` から観測する
- 理解度判断の定性的な根拠テキストを別 DTO や別 state key に保持することは公開契約に含めない。LLM の定性的判断は `next_action` / `score` / `feedback` に反映されるものとして扱い、別保存は本仕様のスコープ外とする

## 回答記録の更新

`answers` には共有契約 `QuizAnswerRecord` に従う新規レコードを 1 件だけ追記する。既存要素の順序変更・上書き・削除は行わない。

各フィールドの責務は以下に固定する。

| フィールド | 値の出所 |
|---|---|
| `question_number` | `QuizAnswerRecord` authoritative schema 上の必須 int フィールド。本ノード仕様では具体的な採番規則を責務化しない |
| `confirmation_point_id` | `confirmation_points[current_point_index]["id"]` |
| `question_text` | `state["current_question_text"]` |
| `answer_type` | `state["current_answer_type"]` |
| `answer_text` | `state["user_input"]` |
| `score` | LLM 出力 |
| `feedback` | LLM 出力 |

`question_number` は共有契約上の必須フィールドだが、具体的な採番規則は本仕様の検証対象外とする。したがって node 単体テストは、追記レコードが `QuizAnswerRecord` schema を満たすことまでは検証してよいが、未定義の採番規則までは固定しない。

## 次のアクション判断

score の閾値ではなく、回答内容に基づく LLM 判断を使う。

- `next`: 理解度が十分。回答済みの確認ポイントを消化し、`current_point_index` を 1 進めて次の未消化確認ポイントへ移る
- `deepdive`: 理解が曖昧または不足。追加の確認ポイントを `confirmation_points` の末尾へ追記しつつ、`current_point_index` は現在問を消化した次位置へ 1 進める。既存の未消化確認ポイントが残っていれば、それを先に出題する
- `complete`: 全確認ポイント完了。`current_point_index == len(confirmation_points)` を満たす完了境界へ進む

## 20問収束ルール

`total_questions_asked >= 20` を 20問収束シグナルとする。20問目の評価時点から、本ノードは LLM に収束判断のための文脈を渡し、追加 deepdive ではなく既存ポイント消化または完了へ向かう判断を期待する。

- node の観測可能な契約は `total_questions_asked` を LLM にそのまま渡すことと、LLM が返した `next_action` をノード側で上書きしないことに限る
- `total_questions_asked >= 20` の評価では、LLM は `next` または `complete` を返す前提とする
- `total_questions_asked >= 20` でも concrete client がこの前提に反して `deepdive` を返した場合、その挙動は本ノードの単体仕様および node 単体テストの対象外、すなわち out-of-contract とする
- したがってこの前提違反時に node 側で `confirmation_points` 追記・失敗化・`next_action` 強制上書きのいずれかを行うことは、本仕様では要求しない
- concrete client のプロンプト文面や、内部でどのように「収束に向かうこと」を指示するかは本ノード仕様および node 単体テストのスコープ外とする

## 技術判断

- 評価とルーティングを1ノードに統合する理由: score が判断の入力ではなく出力であるため（ADR-004）、別ノードに分離する意味がない。LLM が回答を読み、「理解度判断に基づく次のアクション → score → feedback」を一度に決める方が自然
- 深掘り判断をスコア閾値ではなく LLM 判断にする理由: 回答の文脈（概念はわかるがコードが書けない等）を反映した判断が可能
- 理解度判断の別保存先を設けない理由: 本仕様の公開契約は routing と回答記録更新に限定されており、別 DTO や永続化先を追加すると共有契約を増殖させるため

## 境界条件

- ユーザーが空回答: `score=0`、feedback で回答を促す、`deepdive` ではなく `next` に進む
- 実践問題で構文エラーのあるコード: コードの意図を汲んで評価する。構文の指摘は feedback に含める
- 回答が出題意図と無関係: feedback で出題意図を説明し直す。`score` は常に 0〜100 の範囲に収まるが、厳密な low-score band は公開契約に含めない

## スコープ外

- コードの実行による正誤判定（LLM の判断のみ）
- 複数回答の比較評価
- 回答の盗用検出
- 理解度判断の根拠テキストを別 DTO / 別 state key / 別永続化先へ保存すること
- 20問収束時の concrete client 内部プロンプト文面の固定
- `total_questions_asked >= 20` で concrete client が契約前提に反して `deepdive` を返した場合の node 挙動の固定。`confirmation_points` 追記・失敗化・`next_action` 強制上書きはいずれも要求しない

## 受け入れ基準

- [ ] `evaluate_answer(state, ...)` の required input state keys と LLM 引数への 1 対 1 マッピングが定義されている
- [ ] 次のアクション（next / deepdive / complete）が判断される
- [ ] score が 0〜100 で算出され、追記後 `answers` の最新 `QuizAnswerRecord` から観測できる
- [ ] ユーザー向けの feedback が生成され、追記後 `answers` の最新 `QuizAnswerRecord` から観測できる
- [ ] 深掘り時に追加の確認ポイントが含まれる
- [ ] 深掘り時の出力だけで、次問が既存ポイントか追記済み deepdive ポイントかを `confirmation_points` と `current_point_index` から一意に判断できる
- [ ] `total_questions_asked >= 20` の評価では、20問収束シグナルが LLM に渡され、in-contract な `next` / `complete` 返却に対して LLM の `next_action` を node 側で上書きしない
- [ ] 結果が shared contract `QuizAnswerRecord` に従って `answers` へ追記される
- [ ] `input_source="form"` の場合、評価完了時に `input_type="answer"` が設定される

## 異常系

- LLM 呼び出し失敗時は `AnswerEvaluationError` を送出し、`error_code: str` と `message: str` を属性として持ち、`__cause__` に元例外を保持する
- 自動再試行は行わない
- 失敗時は `structlog` の構造化ログをちょうど1件出力する

| error_code | 発生条件 | message | ログイベント |
|---|---|---|---|
| `llm_request_failed` | LLM 呼び出し自体が失敗 | `answer evaluation llm request failed` | `answer_evaluation_failed` |
| `llm_response_parse_failed` | LLM 応答から評価結果の抽出に失敗 | `answer evaluation llm response parse failed` | `answer_evaluation_failed` |

## モジュール構成

- 構成方針: 2ファイル構成（types + logic）
- モジュール一覧:
  - `backend/quiz/application/answer_evaluation_types.py`
    - `AnswerEvaluationError(Exception)` — `error_code: str`, `message: str` を属性として持つ
    - `AnswerEvaluationLlmClient(Protocol)` — `evaluate_answer(question_text: str, confirmation_point_content: str, answer_text: str, answer_type: str, past_answers: list[QuizAnswerRecord], total_questions_asked: int) -> EvaluationOutput`。正常時は `EvaluationOutput` を返し、失敗時は `AnswerEvaluationError` を送出する
    - `EvaluationOutput` — frozen dataclass (`next_action: Literal["next", "deepdive", "complete"]`, `score: int`, `feedback: str`, `deepdive_points: list[ConfirmationPoint]`)。`next_action="deepdive"` 時のみ `deepdive_points` が1件以上、それ以外は空リスト。理解度判断の別 rationale field は持たない
  - `backend/quiz/application/answer_evaluation.py`
    - `evaluate_answer(state: SessionState, *, llm: AnswerEvaluationLlmClient) -> dict[str, object]` — LangGraph ノード関数。ユーザー回答を評価し、`{"next_action": str, "answers": list[QuizAnswerRecord], "current_point_index": int, "confirmation_points": list[ConfirmationPoint], "input_type": "answer"}` を返す
    - `answers` に新しい `QuizAnswerRecord` を 1 件だけ追記する（既存要素は保持）
    - `next_action="next"`: `current_point_index` を +1
    - `next_action="deepdive"`: `confirmation_points` 末尾に `deepdive_points` を追記し、`current_point_index` を +1
    - `next_action="complete"`: `current_point_index` を `len(confirmation_points)` に設定
    - 20問収束ルール: `total_questions_asked >= 20` の場合、LLM に収束判断用の文脈を渡す。LLM が返した `next_action` をそのまま使い、node 側で上書きしない
    - `input_type` を常に `"answer"` に設定する（form 経路の正規化を含む）
