## 命名規則
- 変数名は省略しない（usr → user, msg → message）
- 定数は UPPER_SNAKE_CASE
- 関数名は動詞始まり（get_, create_, update_, delete_, is_, has_）
- bool変数は is_/has_/can_ プレフィクス
- クラス名は PascalCase、名詞

## マジックナンバー/ストリング禁止
- 数値リテラルは定数に切り出す
- 文字列リテラルも繰り返し使う場合は定数化
- OK: WEAKNESS_THRESHOLD = 60
- NG: if score < 60

## 関数設計
- 30行以内
- 引数4つ以内（超える場合は構造体に）
- 1関数1責務（関数名にandが要るなら分割）

## エラーハンドリング
- エラーメッセージに具体的文脈を含める
- 握り潰し禁止

## テスト品質
- 1テスト1関心事（関連するassertはまとめてよい）
- テスト名は何を検証しているかわかる命名
- test_{対象}_{条件}_{期待結果} 形式
- setupの重複はfixture/helper化
- モックは外部依存のみ
