前回の実装でもテストが失敗しました。別のアプローチで修正してください。

## テスト実行結果
{{testOutput}}

## 対象ファイル
- 実装ファイル: {{targetImplementationFile}}
- 参照テストファイル: {{targetTestFile}}

## 仕様書
{{spec}}

## 制約
- テストケースの範囲外の機能は実装しない
- 仕様書に記載のインターフェースに従う
- GREEN に加えて lint/type でも通る実装を書く
- 既存の成功系を壊さず、変更範囲を target scope に限定する
- 例外を握り潰さない。失敗を扱うなら契約に沿った形で明示的に扱う
- `try`-`except`-`pass` や広すぎる例外捕捉で場当たりにテストを通さない

{{mswInstructions}}

{{artifactInstructions}}
