---
feature: roadmap-persistence
status: draft
reviewed_by:
approved_at:
---

## 機能概要

LLMが生成したロードマップのJSON構造をRDB（SQLite）のRoadmapItemテーブルにフラットなレコードとして永続化する。

## 振る舞い

### 基本動作

ロードマップのJSON構造（階層的）を受け取り、各項目をRoadmapItemレコードとしてSQLiteに保存する。

- 階層構造はparent_id方式で表現（ADR-002参照）
- 各項目にUUIDを生成し、親子関係をparent_idで紐付ける
- 同階層内の表示順をorderで保持する
- 初期scoreは0（未着手）

### 具体例

入力（LLM生成のJSON）:
```json
{
  "topic": "TypeScript",
  "items": [
    {
      "title": "基礎",
      "description": "...",
      "level": "major",
      "children": [
        {
          "title": "変数と型",
          "description": "...",
          "level": "middle",
          "children": [
            { "title": "プリミティブ型", "description": "...", "level": "detail" }
          ]
        }
      ]
    }
  ]
}
```

保存されるレコード:
```
roadmap_id=aaa, id=001, parent_id=null, level=major, title="基礎", order=0, score=0
roadmap_id=aaa, id=002, parent_id=001,  level=middle, title="変数と型", order=0, score=0
roadmap_id=aaa, id=003, parent_id=002,  level=detail, title="プリミティブ型", order=0, score=0
```

## 技術判断

- parent_id方式を採用する理由: 固定3段の階層で項目数も小規模のため、シンプルな隣接リストで十分（ADR-002参照）
- roadmap_idを設ける理由: トピックごとに別ロードマップを持ち、複数ロードマップを管理可能にする

## 境界条件

- 空のロードマップ（項目0件） → roadmap_idのみ生成し、項目なしで保存
- 同一トピックで複数ロードマップ → 別のroadmap_idで共存する

## スコープ外

- ロードマップの削除
- ロードマップ間のマージ

## 受け入れ基準

- [ ] JSON構造がRoadmapItemレコードに変換される
- [ ] 親子関係がparent_idで正しく表現される
- [ ] 同階層内の順序がorderで保持される
- [ ] 初期scoreが0で設定される
- [ ] roadmap_idでロードマップ単位の管理ができる
