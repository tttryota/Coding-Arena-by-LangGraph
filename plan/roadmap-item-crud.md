---
type: impl
profile: backend
scope: roadmap/roadmap-item-crud
spec: docs/spec/backend/roadmap/roadmap-item-crud.md
test_cases: tests/test-cases/backend/roadmap/roadmap-item-crud.md
---

## 今回やること
roadmap-item-crud を TDD で実装する

## 対象テストケース
- TC-01: 公開 API と型定義が指定モジュールに存在し、依存が keyword-only DI で固定される
- TC-02: root 直下へ major を追加し、挿入位置の兄弟を後ろへシフトして保存する
- TC-03: 同一親内 move で「取り除いて詰める -> target_order へ挿入」の順で order を決定する
- TC-04: major の delete で部分木を pre-order DFS 順に連鎖削除し、残存 root major の order を詰める
- TC-10: parent_id=major では middle を自動決定し、order=None なら末尾追加する
- TC-11: parent_id=middle では detail を自動決定し、指定 index へ挿入して既存 detail を +1 シフトする
- TC-12: parent_id=None かつ order=None で root major を末尾へ追加できる
- TC-13: 別親への detail move で移動元・移動先の両 sibling 集合を再採番する
- TC-14: root major の move でも target_parent_id=None を許可し、root siblings を再採番する
- TC-15: middle の delete でも descendants を連鎖削除し、同一親配下の残存 middle の order を詰める
- TC-20: 存在しない roadmap_id は add / move / delete すべて RoadmapItemCrudNotFoundError にする
- TC-21: add の不正入力と参照解決を区別する
- TC-22: move の not found、階層違反、循環、範囲外 index を区別する
- TC-23: delete の not found と最後の major 削除禁止を区別する
- TC-30: add の入力検証通過後に id_generator.generate() が失敗したら RoadmapItemCrudStoreError にラップし、replace_items を呼ばない
- TC-31: store.find_roadmap と store.find_item の失敗は RoadmapItemCrudStoreError にラップされる
- TC-32: add / move / delete の成功経路で store.replace_items が失敗したら RoadmapItemCrudStoreError にラップし、cause を保持する

## やらないこと
- 項目の title / description の編集
- reorder 専用 API の追加
- level の手入力 API
- 4 階層目以降の追加
- 削除の取り消し（undo）
- 削除確認ダイアログや confirmed フラグの処理
- 既に壊れている永続データの修復・自動補正
- RDB 実装（store は Protocol で注入）

## 完了条件
- 対象テストケースが全て GREEN
- ruff + mypy がパス
- レビュー通過

## 設計判断
- 依存モジュールは Protocol DI で注入（RoadmapItemCrudStore, RoadmapItemIdGenerator）
- 全ファイルを backend/roadmap/infrastructure/ に配置（harness sourceLayout 準拠）
- 2 モジュール構成: roadmap_item_crud_types.py, roadmap_item_crud.py
- order は 0 始まり sibling index、挿入/詰めは list の insert/pop 相当
- move の index 解釈は「移動元から一度抜いて詰める -> 移動先へ挿入」の順
- snapshot と delete 結果の列挙順は root major から sibling を order 昇順でたどる pre-order DFS
- root 直下追加は parent_id=None で表現
- store への書き込みは replace_items 1 回の snapshot 置換に寄せる
- delete 確認は UI / presentation 層責務、backend は確認フラグを受け取らない
- id_generator.generate() 失敗時は RoadmapItemCrudStoreError で wrap し replace_items を呼ばない
