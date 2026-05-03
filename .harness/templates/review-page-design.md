以下の page 実装を Figma データと設計情報に照らしてレビューしてください。
該当する問題を全て一度に列挙してください。

## 対象ファイル
{{fileContents}}

## 仕様書
{{spec}}

## コンポーネント定義書
{{componentSpec}}

## Dependencies
{{dependencies}}

## Figma Slice
{{figmaSlice}}

## 観点
- 要素欠落がないか
- 依存コンポーネントの使い方が Figma Slice と整合しているか
- レイアウト構造、spacing、色、フォント指定が Figma と矛盾していないか
- ブラウザレンダリング差異ではなく、コードから判断可能な設計不整合のみ指摘する

## severity の判定基準
- critical: 主要 UI が欠落している、画面として成立しない
- major: Figma/仕様と明確に不整合な構造・スタイル・要素配置
- minor: 軽微な構造逸脱や調整不足

{{responseFormat}}
