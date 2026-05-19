---
status: draft
---

# テストケース一覧

# 検証焦点

| テストの種類 | 検証焦点 |
|---|---|
| Phase 1（最小骨格） | `target_path` / 3分類一覧 / 件数 / 初回保存の基本返却形 |
| Phase 2（コアロジック） | 再帰走査、差分分類、拡張子判定、シンボリックリンク無視、mtime 比較、決定性 |
| Phase 3（エッジケース） | 空ディレクトリ、全削除、相対パス正規化と並び順 |
| Phase 4（外部連携） | 例外送出、永続化失敗、アクセス権不足、可観測性 |

## Phase 1: 最小骨格

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-01 | 初回実行で `.md` 通常ファイルをすべて `new_files` として返す | `FileDiffSnapshotStore` に `/vault/study` の前回スナップショットは存在しない | `target_path = "/vault/study"`、現在FS: `/vault/study/typescript/generics.md` mtime=`1716112800000000000`、`/vault/study/docker/dockerfile.md` mtime=`1716116400000000000`、`/vault/study/notes.txt` | `FileDiffResult = {target_path: "/vault/study", new_files: ["docker/dockerfile.md", "typescript/generics.md"], updated_files: [], deleted_files: [], new_count: 2, updated_count: 0, deleted_count: 0}` を返し、同一 `target_path` の最新スナップショットとして `{"docker/dockerfile.md": 1716116400000000000, "typescript/generics.md": 1716112800000000000}` を保存する | 仕様書 例1 に対応 |
| TC-02 | 前回スナップショットがあり、差分がない場合は 3 一覧とも空で返す | 前回スナップショット: `docker/dockerfile.md` mtime=`1716116400000000000`、`typescript/generics.md` mtime=`1716112800000000000` | `target_path = "/vault/study"`、現在FS: `/vault/study/docker/dockerfile.md` mtime=`1716116400000000000`、`/vault/study/typescript/generics.md` mtime=`1716112800000000000` | `FileDiffResult = {target_path: "/vault/study", new_files: [], updated_files: [], deleted_files: [], new_count: 0, updated_count: 0, deleted_count: 0}` を返し、今回の走査結果と同一内容のスナップショットを保存する | 変更なしの最小正常系 |

## Phase 2: コアロジック

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-10 | 新規 1 件・更新 1 件・削除 1 件を同時に正しく分類する | 前回スナップショット: `docker/dockerfile.md` mtime=`1716116400000000000`、`typescript/generics.md` mtime=`1716112800000000000`、`python/contextmanager.md` mtime=`1716111000000000000` | `target_path = "/vault/study"`、現在FS: `/vault/study/docker/dockerfile.md` mtime=`1716116400000000000`、`/vault/study/typescript/generics.md` mtime=`1716120000000000000`、`/vault/study/rust/ownership.md` mtime=`1716123600000000000` | `FileDiffResult = {target_path: "/vault/study", new_files: ["rust/ownership.md"], updated_files: ["typescript/generics.md"], deleted_files: ["python/contextmanager.md"], new_count: 1, updated_count: 1, deleted_count: 1}` を返し、保存スナップショットは `docker/dockerfile.md` / `typescript/generics.md` / `rust/ownership.md` の3件になる | 仕様書 例2 に対応 |
| TC-11 | サブディレクトリを再帰走査し、`.md` 完全一致のみを対象にする | 前回スナップショットなし | `target_path = "/vault/study"`、現在FS: `/vault/study/backend/api/design.md` mtime=`1`、`/vault/study/backend/api/README.MD` mtime=`2`、`/vault/study/backend/api/schema.markdown` mtime=`3`、`/vault/study/backend/todo.txt` mtime=`4` | `new_files = ["backend/api/design.md"]`、`updated_files = []`、`deleted_files = []`、件数は `(1, 0, 0)` を返す | 拡張子の大文字・別拡張子は対象外 |
| TC-12 | `.md` 名のシンボリックリンクファイルを差分対象から完全に除外する | 前回スナップショットなし | `target_path = "/vault/study"`、現在FS: `/vault/study/topic.md` は通常ファイル mtime=`10`、`/vault/study/alias.md` は `topic.md` を指すシンボリックリンク | `new_files = ["topic.md"]`、`updated_files = []`、`deleted_files = []`、件数は `(1, 0, 0)` を返す | 同一実体の重複取り込み防止 |
| TC-13 | シンボリックリンクディレクトリ配下には再帰しない | 前回スナップショットなし | `target_path = "/vault/study"`、現在FS: `/vault/study/real/keep.md` mtime=`10`、`/vault/study/linked` は別ディレクトリを指すシンボリックリンク、`/vault/study/linked/skip.md` 相当の実体は存在 | `new_files = ["real/keep.md"]`、`updated_files = []`、`deleted_files = []`、件数は `(1, 0, 0)` を返す | シンボリックリンク配下の `.md` は探索対象外 |
| TC-14 | mtime が同一なら内容が変わっていても更新扱いしない | 前回スナップショット: `topic.md` mtime=`1716112800000000000` | `target_path = "/vault/study"`、現在FS: `/vault/study/topic.md` の内容は前回と異なるが mtime=`1716112800000000000` のまま | `new_files = []`、`updated_files = []`、`deleted_files = []`、件数は `(0, 0, 0)` を返す | 変更判定キーは mtime のみ |
| TC-15 | 同一の前回スナップショットと同一の現在FSなら結果は毎回同一になる | 前回スナップショット: `b.md` mtime=`20`、`a.md` mtime=`10` | 同一条件で 2 回連続実行する。`target_path = "/vault/study"`、現在FS: `/vault/study/a.md` mtime=`11`、`/vault/study/c.md` mtime=`30` | 1 回目も 2 回目も `new_files = ["c.md"]`、`updated_files = ["a.md"]`、`deleted_files = ["b.md"]`、件数は `(1, 1, 1)` で一致し、一覧の順序・表記揺れ・重複がない | 結果の決定性 |

## Phase 3: エッジケース

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-20 | 初回実行で `.md` ファイルが 0 件なら空差分を返し、空スナップショットを保存する | `FileDiffSnapshotStore` に `/vault/empty` の前回スナップショットは存在しない | `target_path = "/vault/empty"`、現在FS: `/vault/empty/assets/image.png` のみ存在 | `FileDiffResult = {target_path: "/vault/empty", new_files: [], updated_files: [], deleted_files: [], new_count: 0, updated_count: 0, deleted_count: 0}` を返し、空スナップショットを保存する | 仕様書 例3 に対応 |
| TC-21 | 前回スナップショットには `.md` が存在し、今回 0 件なら全件を `deleted_files` として返す | 前回スナップショット: `algorithms/bfs.md` mtime=`100`、`db/index.md` mtime=`200` | `target_path = "/vault/study"`、現在FS: `/vault/study/assets/logo.png` のみ存在 | `new_files = []`、`updated_files = []`、`deleted_files = ["algorithms/bfs.md", "db/index.md"]`、件数は `(0, 0, 2)` を返し、空スナップショットを保存する | 最後の 1 件まで削除されたケース |
| TC-22 | 返却パスは `target_path` からの相対パスで `/` 区切りに正規化され、各一覧は辞書順昇順になる | 前回スナップショットなし | `target_path = "/vault/study"`、現在FS: `/vault/study/zeta/last.md` mtime=`30`、`/vault/study/alpha/first.md` mtime=`10`、`/vault/study/alpha/beta/middle.md` mtime=`20` | `new_files = ["alpha/beta/middle.md", "alpha/first.md", "zeta/last.md"]`、`updated_files = []`、`deleted_files = []`、件数は `(3, 0, 0)` を返す | 相対パス化・区切り文字正規化・ソートを集約確認 |

## Phase 4: 外部連携

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-30 | `target_path` が存在しない場合は `TargetPathNotFoundError` を送出する | 前回スナップショットの有無は問わない | `target_path = "/vault/missing"` | `TargetPathNotFoundError` を送出し、差分結果を返さず、スナップショット保存も行わない | 設定不備の検知 |
| TC-31 | `target_path` が通常ファイルの場合は `InvalidTargetPathError` を送出する | `/vault/file.md` は存在する通常ファイル | `target_path = "/vault/file.md"` | `InvalidTargetPathError` を送出し、差分結果を返さない | 非ディレクトリ入力 |
| TC-32 | `target_path` 自体がシンボリックリンクの場合は `InvalidTargetPathError` を送出する | `/vault/link-study` は `/vault/study` を指すシンボリックリンク | `target_path = "/vault/link-study"` | `InvalidTargetPathError` を送出し、差分結果を返さない | ルートシンボリックリンク禁止 |
| TC-33 | 走査途中のディレクトリまたはファイルで権限不足がある場合は `TargetPathAccessError` を送出する | `/vault/study/private` または `/vault/study/secret.md` の走査・stat に必要な権限がなく、完全なスキャン結果を確定できない | `target_path = "/vault/study"` | `TargetPathAccessError` を送出し、差分結果を返さず、今回スナップショットを保存しない | 途中失敗時は不完全結果を返さない |
| TC-34 | 前回スナップショットの読み込み失敗時は `ScanStatePersistenceError` を送出する | `FileDiffSnapshotStore` の前回スナップショット読み込みが失敗する | `target_path = "/vault/study"` | `ScanStatePersistenceError` を送出し、差分結果を返さず、走査結果保存も行わない | 読み込み失敗 |
| TC-35 | 今回スナップショットの保存失敗時は `ScanStatePersistenceError` を送出する | 走査と差分判定は正常に完了するが、`FileDiffSnapshotStore` の保存が失敗する | `target_path = "/vault/study"`、現在FS: `/vault/study/topic.md` mtime=`10`、前回スナップショットなし | `ScanStatePersistenceError` を送出し、差分結果を返さない | 保存失敗 |
| TC-36 | 正常終了時、呼び出し元が `target_path`・件数・処理時間を取得できる | ログまたはメトリクス収集基盤を有効化し、差分 1 件以上が発生する | `target_path = "/vault/study"`、前回スナップショット: `a.md` mtime=`10`、現在FS: `/vault/study/a.md` mtime=`11`、`/vault/study/b.md` mtime=`20` | 非エラーで差分結果を返し、呼び出し元は少なくとも `target_path="/vault/study"`、`new_count=1`、`updated_count=1`、`deleted_count=0`、処理時間をログまたはメトリクスとして取得できる | 可観測性の非機能要件 |

# 網羅性チェック

仕様書の受け入れ基準の各項目に対応するテストケース ID を記載する。
全項目が少なくとも1つのテストケースでカバーされていることを確認する。

| 受け入れ基準 | 対応テストケース |
|---|---|
| 初回実行時、対象ディレクトリ配下の `.md` 通常ファイルがすべて `new_files` として返る | TC-01, TC-11 |
| 2 回目以降の実行時、前回保存済み mtime と比較して新規・変更・削除が正しく分類される | TC-10, TC-21 |
| `.md` 以外のファイルおよびシンボリックリンクは差分判定対象に含まれない | TC-11, TC-12, TC-13 |
| サブディレクトリ配下の `.md` ファイルも再帰的に検出される | TC-10, TC-11, TC-22 |
| 対象ディレクトリが存在しない場合は `TargetPathNotFoundError` が送出される | TC-30 |
| 対象 `.md` ファイルが存在しない場合、削除対象がなければ空の差分 `(0, 0, 0)` が返る | TC-02, TC-20 |
| 前回スナップショットから全 `.md` ファイルが消えた場合、それらが `deleted_files` として返る | TC-21 |
| 差分結果の各一覧は相対パスの辞書順昇順で返り、件数フィールドと整合する | TC-01, TC-10, TC-22 |
| 正常終了時、今回の走査結果が次回比較用スナップショットとして永続化される | TC-01, TC-02, TC-10, TC-20, TC-21 |

# 記述ルール

- 仕様書に明記された振る舞いだけを前提にする
- 仕様未記載の振る舞いを期待結果に置く場合は `[要仕様追記]` タグを付ける
- 正常系・境界系・異常系が重複なく網羅されていることを確認する
- 仕様書の受け入れ基準の各項目に対応するテストケースが最低1つあることを確認する
