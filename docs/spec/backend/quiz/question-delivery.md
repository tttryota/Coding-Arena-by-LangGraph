---
feature: question-delivery
status: ready
reviewed_by:
approved_at:
---

## 機能概要

確認ポイントリストと過去の問答履歴を踏まえて、具体的な問題文を都度生成し、ユーザーに提示する。

この feature の対象は `quiz/application/` の C3 問題文生成ノード `deliver_question(...)` と、その依存先である `QuestionDeliveryLlmClient(Protocol)` との公開契約に限定する。

## 振る舞い

### 基本動作

次に確認すべきポイントと過去の問答を受け取り、文脈に沿った問題文を生成する。

- 問題セット設計ノードの確認ポイントリストから、次の未確認ポイントを選択する
- 過去の問答の文脈を踏まえた問題文生成は `QuestionDeliveryLlmClient.generate_question(...)` に委譲する
- 確認ポイントの形式に応じて知識問題または実践問題として出題する
- 問題文と一緒に回答形式（`answer_type`: `"textarea"` / `"code"`）を返す。フロント側はこの値で UI を自動切り替えする

### 入力契約

`deliver_question(state: SessionState, *, llm: QuestionDeliveryLlmClient)` は、少なくとも次の state キーを読む。

- 必須キー
  - `roadmap_item_title: str`
  - `roadmap_item_description: str`
  - `confirmation_points: list[ConfirmationPoint]`
  - `current_point_index: int`
  - `answers: list[QuizAnswerRecord]`
- 任意キー
  - `total_questions_asked: int`

`deliver_question(...)` が参照する確認ポイントは `confirmation_points[current_point_index]` である。

### LLM 呼び出し契約

`deliver_question(...)` は選択した確認ポイントと state の値を、`llm.generate_question(title, description, confirmation_point_content, confirmation_point_format, past_answers)` へ 1 対 1 で渡す。

`QuestionDeliveryLlmClient.generate_question(...)` は raw な LLM 応答の取得と `QuestionOutput` への整形を担当する。`deliver_question(...)` 自身は raw 応答を扱わず、`QuestionOutput` だけを受け取る。

- `title` ← `state["roadmap_item_title"]`
- `description` ← `state["roadmap_item_description"]`
- `confirmation_point_content` ← `state["confirmation_points"][state["current_point_index"]]["content"]`
- `confirmation_point_format` ← `state["confirmation_points"][state["current_point_index"]]["format"]`
- `past_answers` ← `state["answers"]`

このキー名とマッピングは `deliver_question(...)` の公開契約である。

### 確認ポイント形式と回答形式

`confirmation_point_format` の許容値は次の 2 つに限定する。

- `knowledge`
  - 本文中の「知識問題」に対応する
  - `answer_type` は常に `"textarea"` とする
- `knowledge_and_practice`
  - 本文中の「実践問題」に対応する
  - `answer_type` は常に `"code"` とする

### 問題文の生成ルール

以下は `QuestionDeliveryLlmClient` が返す `question_text` の期待品質であり、`deliver_question(...)` 自身が `question_text` を構文解析したり、禁止表現の有無を検査したりする責務は持たない。

- 前の問答で使った用語や話題を引き継ぐ
- `knowledge` の問題は、概念の説明や理由を問う
- `knowledge_and_practice` の問題は、実際に使う場面を想定した実装課題にする
  - 文章で要件を示す
  - 少なくとも 1 件の具体例を示す
  - 本質でない部分（関数名等）はあらかじめ提示してよい
  - シグネチャ（型定義）は提示しない

### セッション再開時

`answers` 履歴が渡された場合でも、出題対象の選択は `current_point_index` に従う。

`total_questions_asked` は state の明示値だけを用いて更新する。

- `total_questions_asked` が設定済みなら既存値に `1` を加算する
- `total_questions_asked` が未設定なら常に `1` を返す
- `answers` 履歴の件数や内容から `total_questions_asked` を逆算・推定しない

### 具体例

以下の具体例は説明用であり、同じ入力に対して同じ語句や同じ関数名を必須出力とする規範ではない。

知識問題の例:

確認ポイント: 「明示的型指定と型推論の違い」
過去の問答: 問2で `function identity<T>(arg: T): T` の `<T>` について回答済み

生成される問題文の例:
> 「先ほどのidentity関数について、`identity<string>("hello")` と型引数を省略して `identity("hello")` と書くこともできます。なぜ省略できるのか、またどちらの書き方が望ましいと思いますか？」

実践問題の例:

確認ポイント: 「ジェネリクスを使った関数定義」

生成される問題文の例:
> 「配列と判定関数を受け取り、条件に合う要素だけを返すジェネリック関数 filterBy を実装してください。
> 例: `filterBy([1, 2, 3, 4], n => n > 2)` → `[3, 4]`
> 　　 `filterBy(["a", "bb", "ccc"], s => s.length > 1)` → `["bb", "ccc"]`」

実践問題で提示するもの: 関数名、文章での要件説明、具体的な使用例
実践問題で提示しないもの: シグネチャ（型定義は自分で考える）、実装

## 技術判断

- 問題文を都度生成する理由: 事前に全問題文を作ると前の問答との文脈が断絶する。LLM が毎回文脈を踏まえて生成することで自然な対話になる

## 境界条件

- 全確認ポイントが確認済み → `deliver_question(...)` は出題せず空の更新を返す。完了遷移の判定は別 feature の責務である
- 深掘りが発生した場合 → ルーティングから追加の確認ポイントを受け取り、それに基づいて出題

## スコープ外

- チャット欄 UI
- 出題内容への質問応答（`chat_response`）
- チャット入力の分類（`input_classification`）
- 解説依頼への応答（`explanation_generation`）
- 問題の難易度調整
- 問題のテンプレート化
- 画像や図を含む問題の生成
- 出題数上限に基づく収束/完了判定
- raw LLM 応答の解析ロジックや prompt 品質評価など、`QuestionDeliveryLlmClient` の具体実装詳細

## 受け入れ基準

- [ ] 確認ポイントに基づいた問題文が生成される
- [ ] `deliver_question(...)` は過去の問答履歴を `QuestionDeliveryLlmClient` へそのまま渡し、返却された問題文を改変せずに返す
- [ ] `knowledge` と `knowledge_and_practice` の違いは `QuestionDeliveryLlmClient` へ渡す `confirmation_point_format` と、返却される `answer_type` に反映される
- [ ] 問題文と一緒に `answer_type`（`textarea` / `code`）が返される
- [ ] `knowledge` は `textarea`、`knowledge_and_practice` は `code` を返す
- [ ] `QuestionDeliveryLlmClient` が返す `knowledge_and_practice` の問題文は、要件が文章で示され、少なくとも 1 件の具体例があり、シグネチャはコードで提示されない
- [ ] 全確認ポイント完了後に出題が停止する
- [ ] セッション再開時に続きから出題される
- [ ] `total_questions_asked` は明示 state 値だけで更新され、未設定時は `1` になる

## 異常系

- LLM 呼び出し失敗時は `QuestionDeliveryError` を送出し、`error_code: str` と `message: str` を属性として持ち、`__cause__` に元例外を保持する
- 自動再試行は行わない
- 失敗時は `structlog` の構造化ログをちょうど 1 件出力する
- `deliver_question(...)` は `QuestionDeliveryLlmClient` から送出された `QuestionDeliveryError` をそのまま再送出し、自身では raw 応答の再解析を行わない

| error_code | 発生条件 | message | ログイベント |
|---|---|---|---|
| `llm_request_failed` | LLM 呼び出し自体が失敗 | `question delivery llm request failed` | `question_delivery_failed` |
| `llm_response_parse_failed` | `QuestionDeliveryLlmClient.generate_question(...)` が raw LLM 応答を `QuestionOutput` へ整形する過程で、問題文または `answer_type` の抽出に失敗 | `question delivery llm response parse failed` | `question_delivery_failed` |

## モジュール構成

- 構成方針: 2ファイル構成（types + logic）
- モジュール一覧:
  - `backend/quiz/application/question_delivery_types.py`
    - `QuestionDeliveryError(Exception)` — `error_code: str`, `message: str` を属性として持つ
    - `QuestionDeliveryLlmClient(Protocol)` — `generate_question(title: str, description: str, confirmation_point_content: str, confirmation_point_format: Literal["knowledge", "knowledge_and_practice"], past_answers: list[QuizAnswerRecord]) -> QuestionOutput`。過去の問答文脈を踏まえて問題文を生成し、raw LLM 応答を `QuestionOutput` へ整形する。正常時は `QuestionOutput` を返し、失敗時は `QuestionDeliveryError` を送出する
    - `QuestionOutput` — frozen dataclass (`question_text: str`, `answer_type: Literal["textarea", "code"]`)
  - `backend/quiz/application/question_delivery.py`
    - `deliver_question(state: SessionState, *, llm: QuestionDeliveryLlmClient) -> dict[str, object]` — LangGraph ノード関数。`confirmation_points[current_point_index]` から次の確認ポイントを取得し、LLM で問題文を生成する。`{"current_question_text": str, "current_answer_type": "textarea" | "code", "total_questions_asked": int}` を返す。`total_questions_asked` は既存値 + 1（未設定時は 1）であり、`answers` 履歴からは逆算しない
    - 全確認ポイント消化済み（`current_point_index >= len(confirmation_points)`）の場合は LLM を呼ばず空の更新を返す（完了遷移は `answer_evaluation` の責務）
    - `QuestionDeliveryError` を受けたら `question_delivery_failed` を 1 件だけ記録して再送出する。`deliver_question(...)` 自身は raw LLM 応答を受け取らず、`question_text` の構文検査や禁止表現チェックも行わない
- スコープ外: `chat_response`、`input_classification`、`explanation_generation` は別モジュール
