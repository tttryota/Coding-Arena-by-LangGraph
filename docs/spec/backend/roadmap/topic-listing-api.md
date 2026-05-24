---
feature: topic-listing-api
status: ready
reviewed_by:
approved_at:
---

## 機能概要

トピック候補の一覧取得と自由入力トピックの登録を行うHTTPエンドポイントを提供する。presentation層の責務として、application層の `list_topic_candidates` / `register_manual_topic` をHTTP経由で公開する。

呼び出し元はフロントエンドのロードマップ生成ダイアログ。ユーザーがトピック候補を閲覧し、選択または自由入力でロードマップ生成のトピックを決定する。

## 公開契約

### `GET /roadmaps/topics`

トピック候補一覧を返す。プリセット・ノート由来タグ・自由入力登録済みトピックを統合した結果を `note_count` 降順で返す。

- 呼び出し先: `list_topic_candidates()` (`backend/roadmap/application/topic_listing.py`)
- リクエストボディ: なし
- レスポンス（200）:

```json
{
  "candidates": [
    { "name": "TypeScript", "source": "preset", "note_count": 12 },
    { "name": "LangGraph", "source": "note", "note_count": 5 },
    { "name": "Docker", "source": "preset", "note_count": 3 },
    { "name": "React", "source": "preset", "note_count": 0 },
    { "name": "Terraform", "source": "manual", "note_count": 0 }
  ]
}
```

- `candidates` は `TopicCandidate` のシリアライズ済みリスト
- ソート順は application 層の返却順をそのまま使う（`note_count` 降順、同値時 `canonical_name` 昇順）
- 候補が0件の場合は `{"candidates": []}` を返す

### `POST /roadmaps/topics`

自由入力トピックを登録する。既に同名（`canonical_name` 一致）のトピックが存在する場合は新規登録せず既存トピックを返す。

- 呼び出し先: `register_manual_topic()` (`backend/roadmap/application/topic_listing.py`)
- リクエストボディ:

```json
{ "name": "GraphRAG" }
```

- `name`: 必須、string
- レスポンス（201 Created）:

```json
{ "name": "GraphRAG", "source": "manual", "note_count": 0 }
```

- 既存重複時も201を返す（冪等操作として扱う）
- レスポンスは `TopicCandidate` 1件のシリアライズ

## エラー

| 条件 | HTTPステータス | detail |
|---|---|---|
| `name` が空文字または空白のみ（`TopicListingEmptyTopicNameError`） | 422 | `"Topic name must not be empty"` |
| Container未初期化 | 503 | `"Service not initialized"` |

## DI配線

Containerに以下を追加:

| 属性 | 具象クラス | 初期化タイミング |
|---|---|---|
| `preset_reader` | `PresetTopicFileReader(self._preset_topics_path)` | `_init_roadmap_stores` |

- `note_topic_reader`（`ChromaNoteTopicReader`）は既存。`NoteTopicReader` と `TopicNoteCountReader` を兼務
- `topic_store`（`SqlTopicStore`）は既存
- `preset_topics_path` は `Container` のコンストラクタパラメータ（デフォルト: `"data/preset_topics.json"`）。`Settings` は使用しない（Containerは設計上Settingsに依存しない）

## シリアライズ

`TopicCandidate` → dict の変換:

```python
def _serialize_candidate(candidate: TopicCandidate) -> dict:
    return {
        "name": candidate.name,
        "source": candidate.source,
        "note_count": candidate.note_count,
    }
```

## ルート定義の注意

`GET /roadmaps/topics` は `GET /roadmaps/{roadmap_id}` より前に定義する。`roadmap_id` は `UUID` 型なので `"topics"` はマッチしないが、定義順を明示的に制御する。

## モジュール構成

- `backend/api/routers/roadmap.py` — エンドポイント追加（2関数 + 1 Pydanticモデル + 1 シリアライザ）
- `backend/api/dependencies.py` — `preset_reader` 追加
- `backend/api/dependencies.py` 内の `Container.__init__` に `preset_topics_path` パラメータ追加

## スコープ外

- プリセットJSONファイルの中身の作成（別タスク）
- フロントエンドの実装
- トピック名のバリデーション強化（長さ制限等）

## 受け入れ基準

- [ ] `GET /roadmaps/topics` が `TopicCandidate` リストを返す
- [ ] `POST /roadmaps/topics` が自由入力トピックを登録して `TopicCandidate` を返す
- [ ] 空トピック名で `POST` すると 422 が返る
- [ ] Container に `preset_reader` が追加され、DI 経由で注入される
- [ ] `Container` に `preset_topics_path` パラメータが追加される（デフォルト値あり）
- [ ] 既存のルーターテストが壊れない
