---
feature: explanation-generation
status: ready
reviewed_by:
approved_at:
---

## 機能概要

ユーザーが問題に対して「わからない」と解説を依頼した場合に、RAGでユーザーのノートを参照しつつLLMが解説を生成する。本ノードは `{"explanation_text": str}` を返し、`current_point_index` と `confirmation_points` を壊さないことまでを保証する。解説後に同じ確認ポイントを別の角度から再出題すること自体は、graph の `explanation_generation -> question_delivery` ルートと downstream 実装が担う。

## 振る舞い

### 解説依頼の受付

出題後、ユーザーは回答する代わりに解説を依頼できる。セッション中いつでも可能。

### 解説の生成

1. RAGでユーザーのノートから関連チャンクを検索
   - `ExplanationRagClient.search_related_chunks(query)` に渡す `query` は `state["current_question_text"] + "\n" + confirmation_points[current_point_index]["content"]` と完全一致する
   - 連結順は「現在の問題文 → 改行1文字 → 現在の確認ポイント内容」に固定する
   - 追加の `SessionState` フィールド、履歴、派生文字列は `query` の構成に使わない
2. LLMが以下を組み合わせて解説を生成:
   - ユーザーのノート内容（「あなたのノートにはこう書いてあります」）
   - LLMの汎用知識による補足説明
3. 解説をユーザーに提示

### 解説後の再出題

解説後、graph は `explanation_generation -> question_delivery` のルートで同じ確認ポイントのまま downstream に制御を戻し、`question_delivery` が別角度の再出題を担う。

- 解説を聞いた直後に同じ問題を出しても意味がない（答えを覚えているだけ）
- 本ノード単体の公開契約は `{"explanation_text": str}` を返し、`current_point_index` と `confirmation_points` を変更しないことまでとする
- 別角度の問題文生成と、再出題への回答を通常通り `answer_evaluation` で評価することは downstream の責務とする

### 具体例

```
出題: 「ジェネリクスの型パラメータとは何か説明してください」
ユーザー: 「わからないので解説してほしい」

解説生成:
  → RAG検索: ユーザーのノート「TypeScript入門.md」に関連チャンクあり
  → 解説: 「あなたのノートでは『型パラメータは関数に型の柔軟性を持たせる』と
     書いていますね。もう少し具体的に言うと...（LLMの汎用知識で補足）」

別角度で再出題:
  → 「では、<T>を使わずにany型で書いた場合と比べて、型パラメータを使うメリットは何でしょうか？」
```

## 技術判断

- RAGでノートを参照する理由: ユーザー自身の言葉で書いた記述を活用することで、個別化された解説が可能になる。このサービス独自の価値（ADR-001参照）
- 別角度で再出題する理由: 同じ問題の再出題は解説の暗記テストになってしまう。LLMが異なる切り口で出題することで真の理解を確認できる

## 境界条件

- ノートに関連チャンクがない → LLMの汎用知識のみで解説する
- 1つの確認ポイントで複数回解説依頼 → 許容する。毎回非エラーで解説を返せることを保証する。解説内容が前回と異なることや、会話履歴を踏まえた表現は本ノードの保証外とする
- 解説後の再出題でも再度解説依頼 → 許容する。scoreの低下判定や downstream への伝播は本ノードの責務外とする

## スコープ外

- 解説内容の保存（QuizAnswerに記録しない。解説は一時的なもの）
- 前回解説の保存・参照に依存した差分解説保証
- 再解説依頼の事実に基づくscore制御や、そのためのdownstream連携
- ノートの修正提案（解説時にノートの誤りを指摘する機能はingestion-feedbackが担当）
- 外部リソースへのリンク提示

## 入力契約

- `generate_explanation(state, ...)` が `SessionState` から読む必須フィールドは `current_question_text`、`confirmation_points`、`current_point_index` のみとする
- 各キーの型・値定義は [session-state.md](/Users/tsuryoryo/Desktop/repo/obsidian/docs/spec/backend/quiz/session-state.md) と `backend/quiz/domain/session_state.py` を authoritative source として参照する
- `current_point_index` は `confirmation_points` 内の既存要素を指していなければならず、本ノードは `confirmation_points[current_point_index]["content"]` を read-only で参照する
- `ExplanationRagClient.search_related_chunks(query)` に渡す `query` は `state["current_question_text"] + "\n" + confirmation_points[current_point_index]["content"]` と完全一致し、この2要素以外を含めない
- 本ノードは `state` を変更せず、解説テキストだけをレスポンスとして返す。特に `current_point_index` と `confirmation_points` は入力値を保持したまま downstream に引き渡される
- `input_type` は本ノードへ到達する前のルーティング条件であり、本ノードの必須入力ではない。`SessionState` 上に保持されていても本ノードは読まず、不正入力判定の対象にも含めない

## 受け入れ基準

- [ ] ユーザーが出題後に解説を依頼できる
- [ ] RAGでユーザーのノートから関連チャンクが検索される
- [ ] ノート内容とLLMの汎用知識を組み合わせた解説が生成される
- [ ] 解説後も `current_point_index` と `confirmation_points` を維持したまま、graph の `explanation_generation -> question_delivery` ルートで同じ確認ポイントの別角度再出題へ接続できる
- [ ] ノートに関連チャンクがない場合も解説が生成される

## 異常系

- LLM/RAG呼び出し失敗時は `ExplanationGenerationError` を送出し、`error_code: str` と `message: str` を属性として持ち、`__cause__` に元例外を保持する
- 自動再試行は行わない
- 失敗時は `structlog` の構造化ログをちょうど1件出力する

| error_code | 発生条件 | message | ログイベント |
|---|---|---|---|
| `rag_search_failed` | RAG検索が失敗 | `explanation generation rag search failed` | `explanation_generation_failed` |
| `llm_request_failed` | LLM呼び出し自体が失敗 | `explanation generation llm request failed` | `explanation_generation_failed` |
| `llm_response_parse_failed` | LLM応答から解説テキストの抽出に失敗 | `explanation generation llm response parse failed` | `explanation_generation_failed` |

## モジュール構成

- 構成方針: 2ファイル構成（types + logic）
- モジュール一覧:
  - `backend/quiz/application/explanation_generation_types.py`
    - `ExplanationGenerationError(Exception)` — `error_code: str`, `message: str` を属性として持つ
    - `ExplanationRagClient(Protocol)` — `search_related_chunks(query: str) -> list[str]`。`query` は `state["current_question_text"] + "\n" + confirmation_points[current_point_index]["content"]` と完全一致する。ユーザーノートから関連チャンクを検索し、結果が0件の場合は空リストを返す。失敗時は `ExplanationGenerationError(error_code="rag_search_failed", message="explanation generation rag search failed")` を `__cause__` 付きで送出する
    - `ExplanationLlmClient(Protocol)` — `generate_explanation(question_text: str, confirmation_point_content: str, note_chunks: list[str]) -> str`。解説テキストを生成。失敗時は `ExplanationGenerationError` を送出
  - `backend/quiz/application/explanation_generation.py`
    - `generate_explanation(state: SessionState, *, rag: ExplanationRagClient, llm: ExplanationLlmClient) -> dict[str, object]` — LangGraphノード関数。`state["current_question_text"] + "\n" + confirmation_points[current_point_index]["content"]` をそのまま RAG 検索に使い、RAG検索 → LLM解説生成 → 解説テキストを返す。ステート変更なし（解説はレスポンスとして返すのみ）。戻り値は `{"explanation_text": str}` とし、同一確認ポイントを保持したまま downstream の `question_delivery` へ戻す
    - `ExplanationGenerationError` を受けたら `explanation_generation_failed` を1件だけ記録して再送出する
