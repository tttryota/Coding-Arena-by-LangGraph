---
feature: chunk-store
status: draft
reviewed_by:
approved_at:
---

## 機能概要

チャンク（テキスト + Embedding + メタデータ）をChromaDBに格納・取得・削除する。RAGパイプラインの永続化層として、取り込みパイプラインと検索機能の両方から利用される。

## 振る舞い

### 格納

チャンクのテキスト・ベクトル・メタデータをChromaDBに格納する。

- id: `{source_path}_{chunk_index}`（ナチュラルキー）
- メタデータ: source_path, chunk_index, headers, tags, created_at, updated_at

### 削除

指定したsource_pathに該当する全チャンクを削除する。ファイル更新時に旧チャンクを消すために使用する。

### ファイル更新時の差し替え

1. source_pathで既存チャンクを全削除
2. 新しいチャンクを格納

### source_pathによるフィルタ取得

指定したsource_pathに該当するチャンクを全て取得する。

### 具体例

格納:
```
id: "study/typescript/generics.md_0"
content: "TypeScriptのジェネリクスは..."
embedding: [0.012, -0.034, ...]
metadata:
  source_path: "study/typescript/generics.md"
  chunk_index: 0
  headers: "TypeScript入門 > ジェネリクス"
  tags: ["TypeScript"]
  created_at: "2026-05-17T10:00:00"
  updated_at: "2026-05-17T10:00:00"
```

削除:
```
source_path: "study/typescript/generics.md"
→ 該当する全チャンク（_0, _1, _2, ...）が削除される
```

## 技術判断

- ナチュラルキー（source_path + chunk_index）を採用する理由: ファイル更新時の差し替えで同一IDが再利用され、管理がシンプルになる
- source_pathによる一括削除: ファイル単位での差し替えが基本操作であり、チャンク個別の削除は不要

## 境界条件

- 同一idで格納（upsert）→ 上書きされる
- 存在しないsource_pathで削除 → エラーにはならず、0件削除として扱う
- ChromaDBが未起動 → 接続エラーを返す

## スコープ外

- ベクトル類似度検索（`core/rag/` が担当）
- タグによるフィルタ検索（`core/rag/` が担当）
- チャンクの部分更新（常に全削除→再挿入）

## 受け入れ基準

- [ ] チャンク（テキスト + ベクトル + メタデータ）がChromaDBに格納される
- [ ] source_pathで該当チャンクが全件削除される
- [ ] 格納したチャンクがsource_pathで取得できる
- [ ] idが `{source_path}_{chunk_index}` 形式で生成される
- [ ] 存在しないsource_pathでの削除がエラーにならない
