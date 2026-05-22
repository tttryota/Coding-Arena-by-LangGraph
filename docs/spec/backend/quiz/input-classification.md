---
feature: input-classification
status: ready
reviewed_by:
approved_at:
---

## 機能概要

チャット欄からのユーザー入力を answer / question / explanation_request の3種類に分類し、後続ノードを決定する。分類はLLMが `current_question_text` と `user_input` のコンテキストから判断する。

## 振る舞い

### 基本動作

- 本 feature が保証するのは `input_source="chat"` / `input_source="form"` の経路振る舞いと `classify_input(...)` ノード関数の入出力契約であり、LangGraph 上の登録ノード名文字列そのものは契約対象外とする
- `input_source="chat"` の場合のみ分類処理を行う。`input_source="form"` は分類処理を経由せず `answer_evaluation` に直接遷移する
- `classify_input(...)` ノードは `state["current_question_text"]` と `state["user_input"]` を `InputClassificationLlmClient` にちょうど1回渡して分類を委譲し、返却された分類結果をそのまま `input_type` に設定する
- ノードは `answer` / `question` / `explanation_request` の手動補正、事前分岐、short-circuit を行わない

| 分類 | 判定基準 | 後続ノード |
|---|---|---|
| answer | 出題に対する回答と判断できる | answer_evaluation |
| question | 出題内容の意味や前提についての質問 | chat_response |
| explanation_request | 「わからない」「解説して」等、解説を求める意思表示 | explanation_generation |

### 曖昧な入力

分類が曖昧な場合は answer として扱う（ユーザーが意図的に解説を求めない限り問答を進める）。
この判定ポリシーは `InputClassificationLlmClient` の分類契約として満たし、`classify_input(...)` ノード側で事前判定は行わない。

## 境界条件

- 空文字列の入力 → `InputClassificationLlmClient` は answer として分類する
- 極端に短い入力（1-2文字） → `InputClassificationLlmClient` は answer として分類する

## スコープ外

- 分類結果の手動修正
- 分類履歴の保存
- 複数言語対応の分類ロジック
- LangGraph 上の登録ノード名文字列の固定化

## 受け入れ基準

- [ ] ユーザー入力が answer / question / explanation_request のいずれかに分類される
- [ ] 分類結果が `input_type` として設定される
- [ ] 曖昧な入力は answer として扱われる
- [ ] LLM が `current_question_text` と `user_input` を使って分類する
- [ ] `classify_input(...)` ノードは LLM client を1回だけ呼び出し、その返却値を `input_type` に反映する

## 異常系

- LLM呼び出し失敗時は `InputClassificationError` を送出し、`error_code: str` と `message: str` を属性として持ち、`__cause__` に元例外を保持する
- 自動再試行は行わない
- 失敗時は `structlog` の構造化ログをちょうど1件出力する
- ログ契約として保証するのはイベント名 `input_classification_failed` と出力件数のみであり、payload の詳細キー集合は本 feature の契約対象外とする
- 正常時に `input_classification_failed` が 0 件であることまでは本 feature の契約に含めない

| error_code | 発生条件 | message | ログイベント |
|---|---|---|---|
| `llm_request_failed` | LLM呼び出し自体が失敗 | `input classification llm request failed` | `input_classification_failed` |
| `llm_response_parse_failed` | LLM応答から分類結果の抽出に失敗 | `input classification llm response parse failed` | `input_classification_failed` |

## モジュール構成

- 構成方針: 2ファイル構成（types + logic）
- モジュール一覧:
  - `backend/quiz/application/input_classification_types.py`
    - `InputClassificationError(Exception)` — `error_code: str`, `message: str` を属性として持つ
    - `InputClassificationLlmClient(Protocol)` — `classify_input(question_text: str, user_input: str) -> Literal["answer", "question", "explanation_request"]`。正常時は分類結果を返し、失敗時は `InputClassificationError` を送出する。曖昧入力、空文字列入力、1-2文字入力を answer として分類する責務はこの client 側にある
  - `backend/quiz/application/input_classification.py`
    - `classify_input(state: SessionState, *, llm: InputClassificationLlmClient) -> dict[str, object]` — LangGraphノード関数。`state["current_question_text"]` と `state["user_input"]` を LLM client にちょうど1回渡して分類を委譲し、返却値をそのまま `{"input_type": "answer" | "question" | "explanation_request"}` として返す
    - `InputClassificationError` を受けたら `input_classification_failed` を1件だけ記録して再送出する
