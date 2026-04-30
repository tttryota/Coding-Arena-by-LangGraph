## Python固有
- f-string推奨（.format() や % は使わない）
- dataclass or TypedDict で構造化（dictの直接操作を避ける）
- async関数とsync関数を混在させない

> 注: bare except は ruff BLE001、f-string は ruff FLY で機械チェック済み。
> ここでは構造化やasync/sync混在など機械で検出できない設計をレビューする。

## FastAPI固有
- エンドポイントは必ずレスポンスモデルを定義
- 依存注入（Depends）でDB接続等を渡す
- HTTPExceptionで適切なステータスコードを返す

## LangGraph/LangChain固有
- StateのフィールドはTypedDictで型定義
- プロンプトはハードコードせず定数or外部ファイル管理
- LLM呼び出し結果は構造化パース（JSON mode）
