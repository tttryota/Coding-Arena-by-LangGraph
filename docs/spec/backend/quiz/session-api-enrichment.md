---
feature: session-api-enrichment
status: ready
---

## 機能概要

フロントエンドが必要とするデータを API レスポンスに含めるため、`resume_session()` と `GET /sessions/{session_id}` を拡張する。

## 背景

- `resume_session()` はグラフ実行前の seed state（7キー程度）を返しており、グラフ実行後に更新されるフィールド（`current_question_text`, `next_action`, `input_type` 等）が欠落している。
- `GET /sessions/{session_id}` は `{"session_id": ..., "session": ...}` のみを返し、グラフの state 情報を含まない。

## 公開契約

### resume_session の戻り値変更

`resume_session()` はグラフ実行後の state を返す。

- `_resume_graph_or_raise()` 成功後、同じ `thread_id` で `graph_runner.get_state()` を呼び出す。
- `get_state()` の返り値を authoritative な `SessionState` として返す。
- `_build_session_state()` による seed state 構築は不要となり削除する。`resume_graph()` は `user_input_dict` のみを受け取るため seed state は入力に使用されない。

### GET /sessions/{session_id} のレスポンス拡充

`GET /sessions/{session_id}` はセッションメタデータに加え、グラフの最新 state を含むレスポンスを返す。

- `graph_runner` が利用可能な場合、`get_state(thread_id=session_id)` で最新 state を取得しレスポンスに含める。
- `graph_runner` が None（embedder 未設定）の場合、または `get_state` が `LookupError` を送出した場合、state フィールドなしでメタデータのみ返す。

## 振る舞い

### resume_session

```
1. session, roadmap_item, answers を取得
2. _build_session_state() で seed state 構築
3. _resume_graph_or_raise() でグラフ実行
4. graph_runner.get_state(thread_id=session_id) で最新 state 取得  ← 変更点
5. 最新 state を返す                                                 ← 変更点
```

### GET /sessions/{session_id}

```
1. session = quiz_session_store.find_session(session_id)
2. graph_state = graph_runner.get_state(thread_id=session_id)  ← 追加
3. レスポンスに session + graph_state を含める                   ← 追加
```

## モジュール構成

- `backend/quiz/application/session_lifecycle.py`
  - `resume_session()` の戻り値を `get_state()` ベースに変更
- `backend/api/routers/quiz.py`
  - `get_session()` に graph state 取得ロジックを追加

## 境界条件

- `get_state()` が `LookupError` を送出した場合（checkpoint 未作成）、`GET /sessions/{session_id}` は graph_state なしでメタデータのみ返す。
- `graph_runner` が None の場合、`GET /sessions/{session_id}` は従来通りメタデータのみ返す。

## スコープ外

- パンくず用の topic 情報取得（Gap 5）は本仕様に含めない。
