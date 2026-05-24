---
status: ready
---

# トピック候補API テストケース

## 検証焦点

| Phase | 検証焦点 |
|---|---|
| Phase 1 | 最小骨格 — エンドポイントが存在し、正しいステータスコードを返す |
| Phase 2 | 正常系 — application層との統合、レスポンス形状の検証 |
| Phase 3 | 異常系 — バリデーションエラー、Container未初期化 |

## Phase 1: 最小骨格

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-01 | GET /roadmaps/topics が200を返す | TestClient、全依存をモック（空リスト返却） | `GET /roadmaps/topics` | status_code=200、body=`{"candidates": []}` | |
| TC-02 | POST /roadmaps/topics が201を返す | TestClient、`register_manual_topic` をモック（TopicCandidate返却） | `POST /roadmaps/topics` body=`{"name": "Test"}` | status_code=201、body に `name`, `source`, `note_count` が含まれる | |

## Phase 2: 正常系

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-10 | GET で候補リストが返る | `list_topic_candidates` が `[TopicCandidate("TypeScript", "preset", 12), TopicCandidate("Docker", "note", 3)]` を返すモック | `GET /roadmaps/topics` | body=`{"candidates": [{"name": "TypeScript", "source": "preset", "note_count": 12}, {"name": "Docker", "source": "note", "note_count": 3}]}`、順序は application 層の返却順を維持 | |
| TC-11 | GET で候補0件の場合 | `list_topic_candidates` が空リストを返すモック | `GET /roadmaps/topics` | status_code=200、body=`{"candidates": []}` | |
| TC-12 | POST で新規トピック登録 | `register_manual_topic` が `TopicCandidate("GraphRAG", "manual", 0)` を返すモック | `POST /roadmaps/topics` body=`{"name": "GraphRAG"}` | status_code=201、body=`{"name": "GraphRAG", "source": "manual", "note_count": 0}` | |
| TC-13 | POST で既存重複時も201 | `register_manual_topic` が `TopicCandidate("TypeScript", "preset", 12)` を返すモック（既存重複時の挙動） | `POST /roadmaps/topics` body=`{"name": "typescript"}` | status_code=201、body=`{"name": "TypeScript", "source": "preset", "note_count": 12}` | application層が重複処理を担当 |
| TC-14 | POST のレスポンスに全フィールドが存在 | TC-12 と同条件 | `POST /roadmaps/topics` body=`{"name": "Test"}` | レスポンス dict のキーが `name`, `source`, `note_count` のちょうど3つ | 余分なフィールドが混入しないこと |

## Phase 3: 異常系

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-20 | POST 空文字で422 | `register_manual_topic` が `TopicListingEmptyTopicNameError` を送出するモック | `POST /roadmaps/topics` body=`{"name": ""}` | status_code=422、detail=`"Topic name must not be empty"` | |
| TC-21 | POST 空白のみで422 | `register_manual_topic` が `TopicListingEmptyTopicNameError` を送出するモック | `POST /roadmaps/topics` body=`{"name": "   "}` | status_code=422、detail=`"Topic name must not be empty"` | |
| TC-22 | POST body なしで422 | — | `POST /roadmaps/topics` body なし | status_code=422（Pydanticバリデーション） | FastAPI の自動バリデーション |
| TC-23 | Container未初期化で503 | `request.app.state.container = None` | `GET /roadmaps/topics` | status_code=503、detail=`"Service not initialized"` | 既存の `_container()` ヘルパーの挙動 |
| TC-24 | Container未初期化で503（POST） | `request.app.state.container = None` | `POST /roadmaps/topics` body=`{"name": "Test"}` | status_code=503、detail=`"Service not initialized"` | |

## 網羅性チェック

| 受け入れ基準 | 対応TC |
|---|---|
| GET /roadmaps/topics が TopicCandidate リストを返す | TC-01, TC-10, TC-11 |
| POST /roadmaps/topics が自由入力トピックを登録して TopicCandidate を返す | TC-02, TC-12, TC-13, TC-14 |
| 空トピック名で POST すると 422 が返る | TC-20, TC-21, TC-22 |
| Container に preset_reader が追加され DI 経由で注入される | TC-10（モック注入で間接検証） |
| 既存のルーターテストが壊れない | 全Phase実行後に既存テストも通ること |
