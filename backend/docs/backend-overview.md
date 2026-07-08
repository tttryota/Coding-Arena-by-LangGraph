# Backend Overview

## 何を提供するか

backend は次の 3 つの能力を提供します。

1. ロードマップ生成と取得
2. 学習用クイズセッション
3. 競プロ形式のアルゴリズムクイズ

フロントエンドはこれらを HTTP API として利用します。  
各機能は SQLite 上の学習データを共有しますが、対話フロー自体は独立しています。

## 起動時に組み立てるもの

`backend/src/dev_server.py` は、起動時に以下を束ねて `FastAPI` アプリを構築します。

| 役割 | 使い道 | 永続性 |
| --- | --- | --- |
| SQLite | roadmap / quiz / competitive の業務データ保存 | プロセス外に永続 |
| Codex transport | LLM 呼び出しの共通経路 | 永続しない |
| LangGraph 実行器 | quiz / coding / competitive の対話状態進行 | チェックポイントはプロセス内のみ |
| スレッドプール実行器 | roadmap 生成ジョブの非同期実行 | プロセス再起動で失われる |

重要なのは、backend が「全機能の共通実行基盤」を先に組み立て、その上に API ルータを載せていることです。  
DI の細かな初期化順よりも、どの機能がどの依存に乗っているかを理解した方が保守しやすいです。

## 機能と依存の対応

| 機能 | 主依存 | 補足 |
| --- | --- | --- |
| roadmap | SQLite, Codex transport, スレッドプール | ジョブ状態はメモリ上のみ |
| quiz | SQLite, Codex transport, LangGraph | explanation generation も LLM 単独で処理する |
| competitive | SQLite, Codex transport, LangGraph | quiz とは別グラフで進行する |

## 機能の無効化条件

backend は一部機能だけを止めた状態で起動できます。

| 条件 | 使えなくなるもの | 使えるもの |
| --- | --- | --- |
| container 未初期化 | 全 API | なし |
| quiz runner 未初期化 | 通常 quiz フロー | roadmap, coding session, competitive |
| coding runner 未初期化 | coding session | roadmap, 通常 quiz, competitive |
| competitive runner 未初期化 | competitive | roadmap, quiz |

## どこまで保存されるか

backend の保守で一番重要なのは、どこまでが再起動後も残り、どこからがその場限りかを見失わないことです。

| データ | 保存先 | 再起動後も残るか |
| --- | --- | --- |
| roadmap / roadmap items | SQLite | 残る |
| quiz sessions / answers / summary results | SQLite | 残る |
| competitive sessions / answers | SQLite | 残る |
| LangGraph の一時停止チェックポイント | `MemorySaver` | 残らない |
| roadmap generation job status | `InMemoryJobStatusStore` | 残らない |

このため、ユーザー向けに「必ず再開できる」と言えるのは DB に保存された情報までです。  
LangGraph の停止中の状態は、そのとき動いている backend プロセスに依存します。

## ルータの責務分割

FastAPI の責務は薄く保たれています。

- `api/routers/*`
  - HTTP 入出力、`HTTPException` への変換、サービス可用性チェック
- `application/*`
  - ユースケース進行、状態遷移、ジョブ制御
- `domain/*`
  - 型、エラー、純粋なルール
- `infrastructure/*`
  - SQLite, Codex など外部依存への接続

docs を更新すべきなのは、主に API 契約、状態遷移、保存境界、可用性条件が変わったときです。  
接続用の小さな部品や DI の配線だけが変わった場合は、原則として overview の更新は不要です。
