# フロントエンド実装に必要なバックエンドAPI拡張

## 概要

フロントエンド画面 01～03 について、現行バックエンドAPIとの間のギャップを整理する。

### 画面別ギャップ状況

| 画面 | ルート | ギャップ |
|:-----|:-------|:---------|
| 01 Roadmap List | `/roadmaps` | なし — API契約完全一致 |
| 02 Roadmap Detail | `/roadmaps/:roadmapId` | なし — API契約完全一致 |
| 03 Quiz Session | `/sessions/:sessionId` | **あり** — 以下に詳述 |

---

## 03 Quiz Session のギャップ

`03-quiz-session.md` の仕様に基づくフロントエンド実装において、現行バックエンドAPIとの間にギャップが存在する。
以下に、フロントエンドが正常に動作するために必要なバックエンド側の変更をまとめる。

---

## Gap 1: `GET /sessions/{session_id}` — 初回ロード用データの不足

### 現状

```python
# backend/api/routers/quiz.py:99-108
@router.get("/{session_id}")
def get_session(session_id, request):
    session = c.quiz_session_store.find_session(session_id)
    return {"session_id": session_id, "session": session}
```

返却されるのはセッションメタデータのみ:
```json
{
  "session_id": "sess-xxx",
  "session": {
    "id": "sess-xxx",
    "roadmap_item_id": "item-xxx",
    "status": "in_progress",
    "completed_at": null
  }
}
```

### 必要な変更

フロントエンド仕様（`03-quiz-session.md` セッションヘッダー / 進捗サイドバー / 問題文表示）は、ページ初回ロード時に以下のフィールドを必要とする:

- `roadmap_item_title` — ヘッダーの項目名表示
- `roadmap_item_description` — ヘッダーの説明表示
- `roadmap_item_level` — メタ情報表示
- `confirmation_points` — 進捗サイドバーの確認ポイント数
- `current_point_index` — 進捗サイドバーの現在位置
- `current_question_text` — 出題中の問題文
- `current_answer_type` — 回答タイプ（textarea / code）
- `answers` — 過去の回答一覧（進捗表示に使用）
- `total_questions_asked` — 問題数表示
- `is_resumed` — 再開表示

### 推奨実装

`GET /sessions/{session_id}` のレスポンスに SessionState 相当のデータを含める。

方法A: LangGraph checkpointer から現在のグラフ state を読み出して返す

```python
@router.get("/{session_id}")
def get_session(session_id, request):
    session = c.quiz_session_store.find_session(session_id)
    # checkpointer からグラフの最新 state を取得
    graph_state = c.graph_runner.get_state(thread_id=session_id)
    return {
        "session_id": session_id,
        "session": session,
        **graph_state  # SessionState フィールドをマージ
    }
```

方法B: セッション情報 + ロードマップアイテム情報 + 回答履歴を組み合わせて返す

```python
@router.get("/{session_id}")
def get_session(session_id, request):
    session = c.quiz_session_store.find_session(session_id)
    item = c.roadmap_item_read_store.find_item(session.roadmap_item_id)
    answers = c.quiz_answer_store.find_by_session(session_id)
    graph_state = c.graph_runner.get_state(thread_id=session_id)
    return {
        "session_id": session_id,
        "session": session,
        "roadmap_item_title": item.title,
        "roadmap_item_description": item.description,
        "roadmap_item_level": item.level,
        "is_resumed": False,
        "answers": [to_answer_record(a) for a in answers],
        # checkpointer から取得
        "confirmation_points": graph_state.get("confirmation_points", []),
        "current_point_index": graph_state.get("current_point_index", 0),
        "current_question_text": graph_state.get("current_question_text", ""),
        "current_answer_type": graph_state.get("current_answer_type", "textarea"),
        "total_questions_asked": graph_state.get("total_questions_asked", 0),
    }
```

---

## Gap 2: `POST /sessions/{session_id}/input` — レスポンスがグラフ実行後の状態を含まない

### 現状

```python
# backend/quiz/application/session_lifecycle.py:162-218
def resume_session(input, **deps) -> SessionState:
    state = _build_session_state(...)  # 基本フィールド + answers のみ
    _resume_graph_or_raise(graph_runner, user_input_dict, ...)  # グラフ実行（返り値なし）
    return state  # ← グラフ実行前の state を返している
```

`resume_session()` は `_build_session_state()` で作成した**グラフ実行前の基本 state**（7キー程度）を返す。
グラフ実行後に更新されるフィールド（`current_question_text`, `next_action`, `input_type`, `answers` の新規追加分、スコア・フィードバック等）は checkpointer に保存されるが、レスポンスには含まれない。

### 必要な変更

フロントエンド仕様の状態遷移（出題中 → フィードバック → 次の問題）は、`POST /sessions/:id/input` のレスポンスから以下を読み取る:

- `input_type` — "answer" / "question" / "explanation_request" を判別してフェーズ遷移
- `next_action` — "next" / "deepdive" / "complete" でフィードバック後の遷移先決定
- `current_question_text` — 次の問題文
- `current_answer_type` — 次の回答タイプ
- `answers` — 直近の回答を含む全履歴（スコア・フィードバック表示に使用）
- `total_questions_asked` — 進捗更新
- `explanation_text` — 解説テキスト（input_type="explanation_request" 時）
- `chat_response_text` — チャット応答テキスト（input_type="question" 時）

### 推奨実装

`resume_session()` をグラフ実行後の state を返すように変更:

```python
def resume_session(input, **deps) -> SessionState:
    state = _build_session_state(...)
    _resume_graph_or_raise(graph_runner, user_input_dict, ...)
    # checkpointer から最新の state を取得して返す
    updated_state = graph_runner.get_state(thread_id=session_id)
    return updated_state
```

---

## Gap 3: `explanation_text` / `chat_response_text` が SessionState に含まれない

### 現状

`backend/quiz/domain/session_state.py` の `SessionState` TypedDict は 16 キーで固定されており、`explanation_text` と `chat_response_text` は含まれない。

しかしバックエンドの解説生成ノード (`explanation-generation.md`) は `{"explanation_text": str}` を返す契約であり、チャット応答ノード (`chat_response.py`) も `chat_response_text` を返す。

### 必要な変更

以下のいずれかの方法で、これらのテキストをフロントエンドに伝達する:

方法A: `SessionState` に追加フィールドを定義

```python
class SessionState(TypedDict, total=False):
    # ... 既存16キー ...
    explanation_text: str      # 解説生成時のみ
    chat_response_text: str    # チャット応答時のみ
```

方法B: `POST /sessions/:id/input` のレスポンスを SessionState + 追加フィールドの union にする

```python
@router.post("/{session_id}/input")
def submit_input(session_id, body, request):
    result = resume_session(...)
    response = dict(result)
    # グラフ state からチャット/解説テキストがあれば含める
    graph_state = c.graph_runner.get_state(thread_id=session_id)
    if "explanation_text" in graph_state:
        response["explanation_text"] = graph_state["explanation_text"]
    if "chat_response_text" in graph_state:
        response["chat_response_text"] = graph_state["chat_response_text"]
    return response
```

---

## Gap 4: `GraphRunner` に `get_state()` メソッドがない

### 現状

```python
# backend/quiz/application/session_lifecycle_types.py:89-94
class GraphRunner(Protocol):
    def start_graph(self, state: SessionState, *, thread_id: str) -> None: ...
    def resume_graph(self, user_input: dict[str, object], *, thread_id: str) -> None: ...
    def retry_graph(self, *, thread_id: str) -> None: ...
```

`GraphRunner` Protocol にはグラフの現在 state を取得するメソッドがない。

### 必要な変更

```python
class GraphRunner(Protocol):
    def start_graph(self, state: SessionState, *, thread_id: str) -> None: ...
    def resume_graph(self, user_input: dict[str, object], *, thread_id: str) -> None: ...
    def retry_graph(self, *, thread_id: str) -> None: ...
    def get_state(self, *, thread_id: str) -> SessionState: ...  # 追加
```

`QuizGraphRunner` の concrete 実装:

```python
def get_state(self, *, thread_id: str) -> SessionState:
    state = self._graph.get_state(config={"configurable": {"thread_id": thread_id}})
    return state.values  # type: ignore
```

---

## Gap 5: パンくず用の `topic` が取得できない

### 現状

仕様のパンくずは `ロードマップ > {topic} > クイズ` だが、`GET /sessions/:id` は `session` メタデータのみを返し、`topic`（ロードマップのトピック名）を含まない。`SessionState` にも `topic` フィールドはない。

### 必要な変更

以下のいずれかの方法:

方法A: `GET /sessions/:id` のレスポンスにロードマップ情報を含める

```python
@router.get("/{session_id}")
def get_session(session_id, request):
    session = c.quiz_session_store.find_session(session_id)
    item = c.roadmap_item_read_store.find_item(session.roadmap_item_id)
    roadmap = c.roadmap_store.find_by_item(item.id)
    return {
        "session_id": session_id,
        "session": session,
        "roadmap_id": roadmap.id,
        "topic": roadmap.topic,
    }
```

方法B: `SessionState` に `topic` と `roadmap_id` を追加

```python
class SessionState(TypedDict, total=False):
    # ... 既存フィールド ...
    roadmap_id: str   # パンくず遷移先
    topic: str        # パンくず表示用
```

### フロントエンド暫定対応

ロードマップ詳細ページからの遷移時に React Router の `state` で `topic` と `roadmapId` を渡す。直接アクセス時は `topic` が取れないため、パンくずを省略表示する。

---

## 優先度

| Gap | 優先度 | 理由 |
|:----|:-------|:-----|
| Gap 2 | 最高 | フロントエンドの状態遷移が完全に依存。これなしでは出題→フィードバック遷移が動作しない |
| Gap 1 | 高 | ページ直接アクセス・リロード時に画面が表示できない |
| Gap 3 | 高 | 解説・チャット応答のテキストが取得できない |
| Gap 4 | 中 | Gap 1, 2, 3 の前提。LangGraph の `get_state` API を使えば実装は単純 |
| Gap 5 | 低 | パンくず表示。暫定的に React Router state で回避可能 |

---

## フロントエンド側の暫定対応

上記 Gap が解消されるまでの間、フロントエンドは以下の前提で実装する:

1. `POST /sessions/:id/input` が完全な SessionState を返すことを前提とした型定義（フィールドは optional）
2. `GET /sessions/:id` は `SessionDetailResponse` 型でメタデータのみ取得
3. `explanation_text` / `chat_response_text` は Zustand store で管理（SessionState 型には含めない）
4. バックエンド拡張後にフックの型アサーションを調整
