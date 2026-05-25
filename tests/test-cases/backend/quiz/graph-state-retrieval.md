---
status: ready
---

# テストケース一覧

# 検証焦点

| テストの種類 | 検証焦点 |
|---|---|
| Phase 1（SessionState 拡張） | `SessionState` が 18 フィールドになり、`explanation_text` と `chat_response_text` が追加されていること |
| Phase 2（GraphRunner Protocol） | `GraphRunner` Protocol に `get_state` メソッドが追加されていること |
| Phase 3（QuizGraphRunner 実装） | `QuizGraphRunner.get_state` が checkpointer から state を取得できること |

## Phase 1: SessionState 拡張

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-01 | `SessionState` が 18 フィールドを持ち `explanation_text` と `chat_response_text` が含まれる | `quiz.domain.session_state` を import できる | `SessionState.__annotations__` を取得する | `SessionState.__annotations__` にちょうど 18 個のキーが存在する。既存 16 キーに加え `explanation_text` と `chat_response_text` が含まれる | 既存の session-state TC-01 のフィールド数更新も必要 |
| TC-02 | `explanation_text` の型が `str` である | `typing.get_type_hints()` を使用できる | `SessionState` の `explanation_text` の型ヒントを取得する | 型が `str` と一致する | |
| TC-03 | `chat_response_text` の型が `str` である | `typing.get_type_hints()` を使用できる | `SessionState` の `chat_response_text` の型ヒントを取得する | 型が `str` と一致する | |
| TC-04 | 追加フィールドが optional（`total=False`）である | `SessionState.__optional_keys__` を取得できる | `SessionState.__optional_keys__` を確認する | `explanation_text` と `chat_response_text` が `__optional_keys__` に含まれる。`__optional_keys__` のサイズはちょうど 18 である | |
| TC-05 | `explanation_text` のみ設定した部分状態が構築できる | partial TypedDict で部分状態を作成する | `explanation_text="解説テキスト"` を含む SessionState を作成する | 代入が成功し `state["explanation_text"]` が `"解説テキスト"` と一致する。`chat_response_text` は dict に含まれない | explanation_generation パス |
| TC-06 | `chat_response_text` のみ設定した部分状態が構築できる | partial TypedDict で部分状態を作成する | `chat_response_text="チャット応答"` を含む SessionState を作成する | 代入が成功し `state["chat_response_text"]` が `"チャット応答"` と一致する。`explanation_text` は dict に含まれない | chat_response パス |

## Phase 2: GraphRunner Protocol

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-10 | `GraphRunner` Protocol に `get_state` メソッドが定義されている | `quiz.application.session_lifecycle_types` を import できる | `GraphRunner` の定義を確認する | `get_state` が Protocol のメンバーとして存在する。シグネチャは `(*, thread_id: str) -> SessionState` である | keyword-only 引数 |
| TC-11 | `QuizGraphRunner` が `GraphRunner` Protocol を満たす | `QuizGraphRunner` インスタンスを構築できる | `QuizGraphRunner` が `get_state` メソッドを持つことを確認する | `hasattr(runner, "get_state")` が `True` であり、`get_state` が callable である | |

## Phase 3: QuizGraphRunner.get_state 実装

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-20 | `get_state` がグラフ実行後の state を返す | MemorySaver checkpointer 付きの CompiledStateGraph で `invoke()` を実行済み | `get_state(thread_id=<実行済みthread_id>)` を呼び出す | 返り値が `dict` であり、グラフ実行で設定された `SessionState` のフィールドが含まれる | LangGraph の `get_state().values` を使用 |
| TC-21 | `get_state` の返り値に `explanation_text` が含まれる（explanation パス実行後） | explanation_generation ノードを含むグラフで、explanation パスを実行済み | `get_state(thread_id=<実行済みthread_id>)` を呼び出す | 返り値の dict に `explanation_text` キーが存在し、値が空文字列ではない | ノードの実際の LLM 呼び出しはモックする |

# 網羅性チェック

| 仕様の要件 | 対応テストケース |
|---|---|
| SessionState に `explanation_text` と `chat_response_text` が追加されている | TC-01, TC-02, TC-03, TC-05, TC-06 |
| 追加フィールドが optional である | TC-04 |
| GraphRunner Protocol に `get_state` メソッドがある | TC-10 |
| QuizGraphRunner が Protocol を満たす | TC-11 |
| `get_state` が checkpointer から state を取得できる | TC-20, TC-21 |
