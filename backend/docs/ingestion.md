# Ingestion

## 目的

`ingestion` は Vault 配下の markdown を取り込み、Chroma にチャンクを保存し、必要に応じて roadmap と関連づく feedback を生成する機能です。

この機能は一括処理型で、1 回の trigger ごとに差分を見て対象ファイルだけ処理します。

## API の責務

| API | 役割 |
| --- | --- |
| `POST /ingestion/trigger` | 1 回分の取り込み処理を開始する |
| `GET /ingestion/feedbacks` | feedback 一覧取得 |
| `PUT /ingestion/feedbacks/{feedback_id}/read` | feedback を既読化 |

## API 契約

### `POST /ingestion/trigger`

- 役割
  - 1 回分の取り込み処理を走らせる
- 主要入力
  - `target_path`
  - `trigger`
    - `startup`
    - `interval`
- 主要出力
  - 実行結果の集計
  - 主な項目は `status`, `new_count`, `updated_count`, `deleted_count`, `failed_file_count`, `stored_chunk_count`
- 主な失敗
  - `422`
    - `target_path` が不正
    - `trigger` が不正
  - `503`
    - `VAULT_PATH` 未設定
    - 埋め込みモデル未設定

### `GET /ingestion/feedbacks`

- 役割
  - 保存済み feedback を条件付きで一覧取得する
- 主要入力
  - `date_from`
  - `date_to`
  - `read_status`
    - `all`
    - `read`
    - `unread`
- 主要出力
  - `items`
  - `total_count`
- 主な失敗
  - `422`
    - 日付形式や `read_status` が不正

### `PUT /ingestion/feedbacks/{feedback_id}/read`

- 役割
  - feedback を既読にする
- 主要出力
  - 既読化後の feedback 1 件
- 主な失敗
  - `404`
    - feedback が見つからない

## 可用性条件

### `POST /ingestion/trigger`

以下の両方が必要です。

- `VAULT_PATH` が設定されている
- 埋め込みモデルが設定されている

`VAULT_PATH` 未設定時は、常に `503` で停止します。  
メッセージは `Ingestion service unavailable: VAULT_PATH not configured` です。

### feedback 系 API

- `GET /ingestion/feedbacks`
- `PUT /ingestion/feedbacks/{id}/read`

これらは `VAULT_PATH` 未設定でも利用できます。  
つまり「新規取り込みは止めるが、保存済み feedback の閲覧は止めない」が設計です。

## バッチ実行の流れ

1. target path の差分を検出する
2. deleted files を chunk store から削除する
3. new files を取り込む
4. updated files を取り込み直す
5. 各ファイルで以下を順に行う
   - markdown load
   - チャンク分割
   - タグ付け
   - ベクトル化
   - upsert
   - 取り込み後の追加処理
6. 成功件数・失敗件数を集計して summary を返す

## ファイル単位の責務

| 段階 | 役割 |
| --- | --- |
| 差分検出 | 前回 snapshot と比較して new / updated / deleted を決める |
| markdown loader | Vault から source file を読む |
| chunk splitter | markdown を検索単位へ分割する |
| chunk tagger | chunk にタグを付ける |
| embedder | chunk をベクトル化する |
| chunk store | Chroma に upsert / delete する |
| 取り込み後の追加処理 | roadmap と関連づく feedback を生成・保存する |

この doc の主眼は、どの順に何を行うかです。  
トークン数の計算方法やタグ付け用プロンプトの詳細はここでは固定しません。

## trigger の約束事

`POST /ingestion/trigger` は次の入力を扱います。

- `target_path`
  - 取り込み対象のルート
- `trigger`
  - `startup` または `interval`

無効な trigger は `422` です。  
空の `target_path` も設定エラー扱いです。

## summary の見方

batch 実行結果は概ね次を返します。

- 対象件数
  - `new_count`, `updated_count`, `deleted_count`
- 実成功件数
  - `deleted_success_count`, `ingested_success_count`
- 失敗件数
  - `failed_file_count`
- 保存チャンク数
  - `stored_chunk_count`
- 全体 status
  - `completed`, `completed_with_errors`, `failed`, `skipped_no_diff`

`completed_with_errors` は一部ファイル失敗を許容して batch 全体を継続したことを意味します。

## feedback の位置づけ

feedback は chunk 保存の副作用ではなく、取り込み後の追加処理の成果物です。  
このため、feedback 一覧 API は Chroma ではなく SQLite 上の `ingestion_feedbacks` を読みます。

roadmap との関係もここにあります。

- roadmap item が解決できれば関連 feedback として保存する
- roadmap item がなくても feedback 自体は保存されうる

## 永続化境界

| データ | 保存先 |
| --- | --- |
| chunks | Chroma |
| file diff snapshot | SQLite |
| ingestion feedback | SQLite |
| 一括処理の途中計算状態 | プロセス内のみ |

## docs を更新すべき変更

- batch の主段階追加/削除
- `trigger` 入力契約の変更
- feedback API の可用性条件変更
- Vault 未設定時の扱い変更
