# Roadmap

## 目的

`roadmap` は、学習テーマを階層構造の roadmap として生成・保存・取得・編集する機能です。  
生成だけは非同期ジョブで行い、それ以外の一覧・詳細・CRUD は同期 API で扱います。

## API の責務

| API | 役割 |
| --- | --- |
| `GET /roadmaps` | 全 roadmap の一覧を返す |
| `GET /roadmaps/{roadmap_id}` | 階層ツリーを返す |
| `POST /roadmaps/generate` | 生成ジョブを受け付ける |
| `GET /roadmaps/generate/{job_id}` | ジョブ状態を返す |
| `GET /roadmaps/topics` | 生成候補トピックの一覧を返す |
| `POST /roadmaps/topics` | 手動トピックを登録する |
| `POST /roadmaps/{roadmap_id}/items` | 項目追加 |
| `PUT /roadmaps/{roadmap_id}/items/{item_id}/move` | 項目移動 |
| `DELETE /roadmaps/{roadmap_id}/items/{item_id}` | 項目削除 |

## API 契約

### `GET /roadmaps`

- 役割
  - roadmap の一覧を返す
- 主要出力
  - `items`
  - `total_count`
  - 各 item には `roadmap_id`, `topic`, `overall_score` が含まれる
- 主な失敗
  - 読み取り基盤が壊れている場合はサーバーエラー

### `GET /roadmaps/{roadmap_id}`

- 役割
  - 1 つの roadmap をツリー構造で返す
- 主要出力
  - `roadmap_id`
  - `topic`
  - `overall_score`
  - `items`
- 主な失敗
  - `404`
    - roadmap が見つからない

### `POST /roadmaps/generate`

- 役割
  - 生成ジョブを受け付ける
- 主要入力
  - `topic`
- 主要出力
  - `job_id`
  - `status`
- 主な失敗
  - `422`
    - topic が空
  - `503`
    - ジョブ登録に失敗

### `GET /roadmaps/generate/{job_id}`

- 役割
  - 生成ジョブの現在状態を返す
- 主要出力
  - `status`
  - 完了時は `roadmap_id`
  - 失敗時は `error_code`, `error_message`
- 主な失敗
  - `404`
    - job が見つからない

### `GET /roadmaps/topics`

- 役割
  - 生成候補トピックを返す
- 主要出力
  - `candidates`
  - 各候補には `name`, `source` が含まれる

### `POST /roadmaps/topics`

- 役割
  - 手動で topic を登録する
- 主要入力
  - `name`
- 主要出力
  - 登録された topic 候補
- 主な失敗
  - `422`
    - topic 名が空

### `POST /roadmaps/{roadmap_id}/items`

- 役割
  - roadmap 配下に item を追加する
- 主要入力
  - `parent_id`
  - `title`
  - `description`
  - `order`
- 主要出力
  - `created_item`
- 主な失敗
  - `404`
    - roadmap または parent が見つからない
  - `422`
    - level や order が不正

### `PUT /roadmaps/{roadmap_id}/items/{item_id}/move`

- 役割
  - item の親と順序を変更する
- 主要入力
  - `target_parent_id`
  - `target_order`
- 主要出力
  - `moved_item`
- 主な失敗
  - `404`
    - roadmap または item が見つからない
  - `422`
    - 移動先が不正

### `DELETE /roadmaps/{roadmap_id}/items/{item_id}`

- 役割
  - item とその配下を削除する
- 主要出力
  - `deleted_item_ids`
  - `deleted_count`
- 主な失敗
  - `404`
    - roadmap または item が見つからない
  - `422`
    - 削除条件が不正

## 生成フロー

1. `POST /roadmaps/generate` が topic を受け取る
2. topic が空でなければ job id を発行し、job store に `queued` を保存する
3. スレッドプール実行器がバックグラウンド job を登録する
4. job は LLM に roadmap JSON を要求する
5. 返却 JSON を schema と階層ルールで検証する
6. 妥当なら SQLite に roadmap と items を保存する
7. job store を `completed` または `failed` に更新する

## 非同期ジョブの約束事

### job の状態

| status | 意味 |
| --- | --- |
| `queued` | 受付済み、未実行 |
| `running` | 生成処理中 |
| `completed` | 永続化まで完了 |
| `failed` | 入力不正、LLM 応答不正、永続化失敗などで停止 |

### 重要な制約

- job の状態保存は `InMemoryJobStatusStore`
- プロセス再起動で job 状態は失われる
- roadmap 本体は SQLite に保存されるので、保存済みの成果物は残る

このため、job の状態は「進行表示用の一時状態」であって、監査ログではありません。

## 生成結果の構造ルール

LLM から期待する roadmap は、概ね次の性質を満たします。

- root は `topic` と `items` を持つ object
- major は 2 本で、タイトルは `基礎` と `応用`
- 階層は `major -> middle -> detail`
- 各 item は `title`, `description`, `level`, `children` を持つ

docs ではプロンプト文面ではなく、保存前に守らせたい構造制約を重視します。  
これが変わると frontend 表示と CRUD ルールにも影響します。

## 一覧・詳細取得の振る舞い

### 一覧

- `GET /roadmaps` はツリー全体を返さない
- 各 roadmap の `overall_score` だけを集約して返す

### 詳細

- `GET /roadmaps/{id}` は DB 上の平坦な item 群からツリーを再構築する
- sibling は `order` で整列する
- `detail` の score はその item 自身の score
- `middle` / `major` の score は子の floor average
- `last_quiz_at` は `detail` にだけ直接乗る

取得系の本質は「DB の正規化された表現を、画面に必要なツリーへ再構成すること」です。

## CRUD の振る舞い

- add
  - `roadmap_id` 配下に item を追加する
  - `parent_id` により level が決まる
- move
  - `target_parent_id` と `target_order` を受け取る
  - roadmap をまたぐ移動は許可しない
- delete
  - 指定 item とその配下をまとめて削除する

この doc では SQL の詳細ではなく、「どの単位を整合性境界として扱うか」だけを残します。

## 失敗時の扱い

- topic が空なら `422`
- enqueue に失敗したら `503`
- job id が存在しなければ `404`
- 保存時エラーや LLM 応答不正は job status が `failed` になる

## docs を更新すべき変更

- 生成ジョブの state 遷移変更
- roadmap 階層ルール変更
- `GET /roadmaps` と `GET /roadmaps/{id}` の責務変更
- job status の永続化戦略変更
