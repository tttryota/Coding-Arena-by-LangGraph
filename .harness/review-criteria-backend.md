## Python固有
- bare except 禁止（except Exception as e を使う）
- f-string推奨（.format() や % は使わない）
- dataclass or TypedDict で構造化（dictの直接操作を避ける）
- async関数とsync関数を混在させない

## FastAPI固有
- エンドポイントは必ずレスポンスモデルを定義
- 依存注入（Depends）でDB接続等を渡す
- HTTPExceptionで適切なステータスコードを返す

## LangGraph/LangChain固有
- StateのフィールドはTypedDictで型定義
- プロンプトはハードコードせず定数or外部ファイル管理
- LLM呼び出し結果は構造化パース（JSON mode）
