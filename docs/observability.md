# LangGraphの評価とLangfuse監視

## 起動

LangfuseはMITライセンスのOSS機能だけを使用し、完全にローカルで動作します。

```bash
scripts/init-langfuse-env.sh
docker compose --profile observability up --build
```

- アプリ: <http://localhost:3080>
- Langfuse: <http://localhost:3000>
- ログイン情報: `.env`の`LANGFUSE_INIT_USER_EMAIL`と
  `LANGFUSE_INIT_USER_PASSWORD`

`LANGFUSE_TRACING_ENABLED=false`にすると、アプリはNo-op observerを使い、
Langfuseへの通信を行いません。Langfuseが停止している場合も、トレース送信の
失敗によってクイズ処理は失敗しません。

## 人間がデータを確認する方法

### Tracing

1回の`start`、`resume`、`retry`が1つのtraceです。名前は
`quiz.start`、`coding.resume`、`competitive.start`の形式です。

traceを開くと、次をツリーで確認できます。

```text
quiz.resume
└── LangGraph
    ├── answer_evaluation
    │   └── quiz.answer_evaluation
    │       ├── codex.attempt
    │       └── input / output / model / latency
    └── progress_update
        └── quiz.progress_update
```

確認の優先順は、`ERROR`のtrace、p95より遅いtrace、再試行を含むtraceです。
generation詳細にはprompt、回答、model、応答文字数、子プロセスRSS、recycle理由を
保存します。Codex app-serverがtoken usageを返した場合だけtoken数も表示します。

### Sessions

LangGraphの`thread_id`をLangfuseの`session_id`として使用します。同じ学習
セッションのstart/resume/retryが時系列にまとまるため、「最初の出題から完了まで」
を横断して確認できます。

### Scores

評価CLIを`--publish`付きで実行すると、以下のscoreがtraceへ追加されます。

- `score_band_match`: 人手で定義した期待スコア帯に入ったか
- `route_match`: 必須ノードを通り、禁止ノードを通らなかったか
- `semantic_correctness`: judgeによる1〜5の正確性評価

### Datasets / Experiments

評価ケースは`obsidian-langgraph-v1` datasetへケースIDを保ったまま登録されます。
リポジトリのJSONLが正本で、Langfuseは結果の閲覧と比較に使用します。
プロンプト、モデル、コードを変更したらquality評価を再実行し、ケース単位の
score差分を確認します。

## Dashboard

Langfuseの`Dashboards`でローカル用dashboardを作り、次のwidgetを追加します。

| Widget | Data source | 表示 |
| --- | --- | --- |
| Flow別実行数 | Observations | count、`flow`でgroup |
| エラー率 | Observations | ERROR / count |
| p95応答時間 | Observations | p95 latency、operationでgroup |
| LLM呼び出し数 | Observations | type=generationのcount |
| 再試行率 | Observations | name=`codex.attempt`のcount |
| Parse失敗 | Observations | error typeまたは`llm_response_parse_failed` |
| 品質推移 | Scores | `semantic_correctness`の平均 |

`environment=local`をアプリ利用、`environment=evaluation`を評価実行に使用し、
dashboard上で混在させないでください。

## Monitors

ローカル通知先は必須にせず、Langfuse UIで次の条件を登録します。

| 名前 | 期間 | 条件 |
| --- | --- | --- |
| Graph error rate | 15分 | エラー率が10%を超える |
| Graph p95 latency | 15分 | p95 latencyが120秒を超える |
| Response parse failure | 15分 | parse失敗が1件以上 |
| Quality regression | 評価実行 | semantic correctness平均が3未満 |

## 評価スイート

```bash
cd backend
uv run python -m evaluation.cli contract
uv run python -m evaluation.cli quality --repeat 3 --publish
uv run python -m evaluation.cli benchmark --repeat 5 --publish
```

- `contract`: 36件のdataset schema、ケースID、期待経路、状態キーを決定的に検証
- `quality`: 実際のquiz/coding/competitive採点アダプタと独立judgeを実行
- `benchmark`: warm-up後のp50/p95を測定し、ローカルベースライン比125%超を警告

live評価は時間とLLM呼び出しを消費するため、Git hookには含めません。

## 永続化とバックアップ

通常の停止ではLangfuseデータは残ります。

```bash
docker compose --profile observability down
```

名前付きvolumeの一覧:

```bash
docker volume ls --filter name=obsidian_langfuse
```

バックアップはLangfuse停止後にDocker volumeをバックアップするか、PostgreSQLと
ClickHouseをそれぞれダンプします。`docker compose down -v`はLangfuseの
PostgreSQL、ClickHouse、Redis、MinIOデータを削除するため、意図的な初期化以外では
実行しないでください。
