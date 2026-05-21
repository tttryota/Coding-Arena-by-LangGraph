---
feature: topic-listing
status: ready
reviewed_by:
approved_at:
---

# 概要

- この機能が解決する課題:
  ロードマップ生成のためのトピック候補をユーザーに提示する。候補ソースはプリセット、ノートから自動生成されたタグ、自由入力で登録済みのトピックの 3 つに固定する。
- 利用者・呼び出し元・前提条件:
  呼び出し元は presentation 層の API エンドポイントを想定する。依存先は `Protocol` による DI で keyword-only 引数として注入する。プリセットとノート由来タグは読み取り可能であり、自由入力で登録されたトピックは永続化済みまたはこれから永続化可能であることを前提とする。

# 入出力

- 公開 API:
  公開エントリポイントはモジュールレベル関数 2 つに固定する。代替名、クラスメソッド、位置引数 DI は定義しない。
  ```python
  list_topic_candidates(
      *,
      preset_reader: TopicPresetReader,
      note_topic_reader: NoteTopicReader,
      topic_store: TopicStore,
      note_count_reader: TopicNoteCountReader,
  ) -> list[TopicCandidate]

  register_manual_topic(
      raw_name: str,
      *,
      topic_store: TopicStore,
      note_count_reader: TopicNoteCountReader,
  ) -> TopicCandidate
  ```
- 入力:
  - `list_topic_candidates`:
    業務入力は持たない。依存ポートのみ受け取る。
  - `register_manual_topic`:
    - `raw_name: str` — ユーザーが自由入力したトピック名。正規化規則は本仕様の「自由入力登録の規則」に従う。
- 依存インターフェース:
  - `canonical_name` 共通契約:
    本仕様で扱う `canonical_name` はすべて、トピック名から前後空白を除去した値に対して `NFKC` と `casefold()` を順に適用した比較用キーを指す。`PresetTopicRecord`、`NoteTopicRecord`、`StoredTopicRecord`、`TopicNoteCountRecord` と、それらを返す reader/store はこの形式の値を返す前提とする。`topic_listing` 本体は返却値をこの共通契約の比較キーとしてそのまま使い、全ソース横断の一覧統合と重複判定を行う。
  - `TopicPresetReader`
    - `list_preset_topics() -> list[PresetTopicRecord]`
      プリセット候補を返す。返却順は不定。`canonical_name` は前記の共通契約に従う比較用キーであり、リスト内で一意。
  - `NoteTopicReader`
    - `list_note_topics() -> list[NoteTopicRecord]`
      ノートから自動生成された候補を返す。返却順は不定。`canonical_name` は前記の共通契約に従う比較用キーであり、リスト内で一意。
  - `TopicStore`
    - `list_manual_topics() -> list[StoredTopicRecord]`
      `source="manual"` の登録済みトピックだけを返す。返却順は不定。`canonical_name` は前記の共通契約に従う比較用キーであり、リスト内で一意。
    - `find_topic_by_canonical_name(canonical_name: str) -> StoredTopicRecord | None`
      引数 `canonical_name` は前記の共通契約に従う比較用キーとする。`canonical_name` が一致する既存トピックを 1 件返す。対象ソースは `preset` / `note` / `manual` を含む全登録トピック。複数ソースに同じ `canonical_name` が存在する場合は、一覧取得の統合規則と同じく `preset` → `manual` → `note` の優先順で代表 1 件を返す。存在しない場合は `None`。この代表選択は `TopicStore` 側の契約であり、`topic_listing` 本体は返された 1 件をそのまま既存トピックとして扱う。
    - `create_manual_topic(name: str, canonical_name: str) -> StoredTopicRecord`
      新しい自由入力トピックを登録し、登録後レコードを返す。引数 `canonical_name` と戻り値 `canonical_name` は前記の共通契約に従う比較用キーとする。戻り値の `source` は必ず `manual`。
  - `TopicNoteCountReader`
    - `list_note_counts(canonical_names: list[str]) -> list[TopicNoteCountRecord]`
      指定した `canonical_name` 群に対するノート件数を返す。入力 `canonical_names` と戻り値の `canonical_name` は前記の共通契約に従う比較用キーとする。戻り値の `canonical_name` は、入力 `canonical_names` の部分集合であり、同一呼び出しの返却リスト内で一意とする。返却順は不定であり、呼び出し側は入力順と無関係に結果を解釈する。返却されなかった `canonical_name` の件数は `0` とみなす。件数の意味はノートとトピックの関連付け件数であり、プリセット登録や自由入力登録そのものは加算しない。同一 `note_id` 内で同じトピックが複数回出現しても 1 件として数える。この集計意味論は `TopicNoteCountReader` 側の契約であり、`topic_listing` 本体は返された件数を採用する。
- 内部 DTO:
  - `PresetTopicRecord`
    frozen dataclass。
    - `name: str`
    - `canonical_name: str`
      比較用正規化済みの名前。前後空白除去後の値に `NFKC` と `casefold()` を順に適用した比較用キー。
  - `NoteTopicRecord`
    frozen dataclass。
    - `name: str`
    - `canonical_name: str`
      前後空白除去後の値に `NFKC` と `casefold()` を順に適用した比較用キー。
  - `StoredTopicRecord`
    frozen dataclass。
    - `name: str`
    - `canonical_name: str`
      前後空白除去後の値に `NFKC` と `casefold()` を順に適用した比較用キー。
    - `source: Literal["preset", "note", "manual"]`
  - `TopicNoteCountRecord`
    frozen dataclass。
    - `canonical_name: str`
      前後空白除去後の値に `NFKC` と `casefold()` を順に適用した比較用キー。
    - `note_count: int`
      0 以上の整数。
- 出力 DTO:
  - `TopicCandidate`
    frozen dataclass。`list_topic_candidates` と `register_manual_topic` の戻り値はこの DTO に固定する。
    - `name: str`
      一覧に表示するトピック名。
    - `source: Literal["preset", "note", "manual"]`
      その候補の代表ソース。決定規則は本仕様の「一覧取得の規則」に従う。
    - `note_count: int`
      関連ノート件数。算出規則は本仕様の「一覧取得の規則」に従う。
- エラー:
  - `TopicListingEmptyTopicNameError`
    `register_manual_topic` が、保存用正規化後に空文字となる `raw_name` を受け取った場合に送出する。戻り値 DTO では表現しない。

# 一覧取得の規則

1. `list_topic_candidates` は `preset_reader.list_preset_topics`、`note_topic_reader.list_note_topics`、`topic_store.list_manual_topics` をそれぞれ 1 回ずつ呼び出し、3 ソースを同時に一覧対象とする。自由入力で登録済みのトピックは一覧対象に含める。除外しない。
2. 候補の統合単位は `canonical_name` とする。各ソースの record は同じ共通契約の比較用キーを返す前提とし、`topic_listing` 本体はその `canonical_name` 一致だけで全ソース横断の重複判定を行う。同じ `canonical_name` が複数ソースに存在する場合でも、返却する `TopicCandidate` は 1 件だけに統合する。別件として 2 件以上返さない。
3. 統合後の `source` と `name` は、同じ `canonical_name` に属する元レコードのうち、`preset` → `manual` → `note` の優先順で決める。
   - `source` は優先順位が最も高い元レコードの `source` を設定する。
   - `name` は同じ元レコードの `name` をそのまま使う。
   - 例: `preset` の `Docker` と `note` の `docker` が同居する場合、返却は `name="Docker"`、`source="preset"` の 1 件。
   - 例: `manual` の `Terraform` と `note` の `terraform` が同居する場合、返却は `name="Terraform"`、`source="manual"` の 1 件。
4. `note_count` は `TopicNoteCountReader` が返す件数を使う。`topic_listing` 本体の責務は次に限定する。
   - `list_note_counts` が件数を返した `canonical_name` には、その `note_count` をそのまま採用する。
   - `list_note_counts` が件数を返さない `canonical_name` は `note_count=0` とする。
   - 自由入力で登録済みだがノートにまだ紐付いていないトピックは `note_count=0` とする。
   - 件数の集計意味論、すなわちノートとトピックの関連付けだけを数えること、および同一 `note_id` を 1 件として扱うことは `TopicNoteCountReader` 側の契約とし、`topic_listing` 本体は再集計や補正を行わない。
5. `list_topic_candidates` は、集約対象の全 `canonical_name` を重複排除したうえで `canonical_name` 昇順に並べ、`note_count_reader.list_note_counts` に 1 回だけ渡して件数を引く。この引数順は件数取得用リストにだけ適用する決定規則であり、最終的な `TopicCandidate` の返却順を定める安定ソート規則とは別契約とする。
6. 返却順は reader/store の返却順に依存させない。安定ソート規則は次のとおり。
   - 主ソートキー: `note_count` 降順
   - 第 2 ソートキー: `canonical_name` 昇順
   - 同じ `canonical_name` は 1 件に統合済みのため、これで順序が一意に決まる。

# 自由入力登録の規則

1. `register_manual_topic` は、ユーザー入力 `raw_name` から保存用正規化名 `normalized_name` を作る。保存用正規化は `raw_name.strip()` のみとし、前後空白だけを除去する。内部の連続空白は潰さない。大小文字変換、Unicode 正規化、全半角変換は保存値には適用しない。
2. `normalized_name == ""` の場合は `TopicListingEmptyTopicNameError` を送出する。`topic_store` と `note_count_reader` は呼び出さない。
3. 重複判定用の比較キー `canonical_name` は、`normalized_name` に対して以下を順に適用して作る。
   - Unicode 正規化 `NFKC`
   - `casefold()` による大小文字の吸収
   この比較キーは前後空白除去後の値に対して作る。
   `PresetTopicRecord`、`NoteTopicRecord`、`StoredTopicRecord`、`TopicNoteCountRecord` と各依存インターフェースが扱う `canonical_name` も、この比較用キーに統一する。
4. `register_manual_topic` は `topic_store.find_topic_by_canonical_name(canonical_name)` を 1 回呼ぶ。
   - 既存トピックが見つかった場合:
     - 新規登録しない。`topic_store.create_manual_topic` は呼び出さない。
     - `find_topic_by_canonical_name` が返す `StoredTopicRecord` は、同じ共通契約の `canonical_name` を持つ候補を一覧取得した場合と同じ `preset` → `manual` → `note` 優先の代表レコードである。この代表選択自体は `TopicStore` 側の契約とする。
     - 戻り値は一覧と同じ `TopicCandidate` とする。`name` と `source` はその代表 `StoredTopicRecord` をそのまま使うため、同じ `canonical_name` の候補を一覧取得した場合の `name` / `source` と一致する。`register_manual_topic` は代表選択を再計算しない。
     - `note_count_reader.list_note_counts([canonical_name])` を 1 回呼び、その返却値を `note_count` に採用する。件数未返却時は `0`。
   - 既存トピックが見つからない場合:
     - `topic_store.create_manual_topic(name=normalized_name, canonical_name=canonical_name)` を 1 回呼んで登録する。
     - 登録後に `note_count_reader.list_note_counts([canonical_name])` を 1 回呼び、その返却値を `note_count` に採用する。件数未返却時は `0`。
     - 戻り値は `TopicCandidate(name=normalized_name, source="manual", note_count=<上記件数>)` と同義の値とする。
5. 同一視するのは `canonical_name` 一致だけに限定する。同義語辞書、略語展開、形態素解析、部分一致、あいまい一致では重複判定しない。

# 具体例

## 例1: 一覧取得で 3 ソースを統合する

- 事前データ:
  ```yaml
  preset_reader.list_preset_topics():
    - { name: "TypeScript", canonical_name: "typescript" }
    - { name: "Docker", canonical_name: "docker" }
    - { name: "React", canonical_name: "react" }
  note_topic_reader.list_note_topics():
    - { name: "docker", canonical_name: "docker" }
    - { name: "LangGraph", canonical_name: "langgraph" }
  topic_store.list_manual_topics():
    - { name: "Terraform", canonical_name: "terraform", source: "manual" }
  note_count_reader.list_note_counts(["docker", "langgraph", "react", "terraform", "typescript"]):
    - { canonical_name: "typescript", note_count: 12 }
    - { canonical_name: "docker", note_count: 3 }
    - { canonical_name: "langgraph", note_count: 5 }
  ```
- 期待される出力:
  ```yaml
  - { name: "TypeScript", source: "preset", note_count: 12 }
  - { name: "LangGraph",  source: "note",   note_count: 5 }
  - { name: "Docker",     source: "preset", note_count: 3 }
  - { name: "React",      source: "preset", note_count: 0 }
  - { name: "Terraform",  source: "manual", note_count: 0 }
  ```
- 補足:
  - `note_count_reader.list_note_counts(...)` に渡す `canonical_name` 配列は、集約後の重複を除去したうえで `canonical_name` 昇順に固定する。reader の返却順は不定でもよく、返却 `canonical_name` はその配列の部分集合かつ一意である前提で解釈する。
  - `Docker` は preset と note の重複だが、`canonical_name="docker"` 単位で 1 件に統合され、`source="preset"` が採用される。
  - `Terraform` は自由入力由来でも一覧に含まれる。
  - `note_count=3` の集計根拠、たとえば同一 `note_id` の複数出現を 1 件として数えるかどうかは `TopicNoteCountReader` 側の契約であり、この機能は返却された件数をそのまま採用する。

## 例2: 自由入力が既存トピックと重複する

- 入力:
  ```yaml
  raw_name: " Terraform "
  topic_store.find_topic_by_canonical_name("terraform"):
    { name: "Terraform", canonical_name: "terraform", source: "manual" }
  note_count_reader.list_note_counts(["terraform"]):
    []
  ```
- 期待される出力:
  ```yaml
  { name: "Terraform", source: "manual", note_count: 0 }
  ```
- 補足:
  - 前後空白除去後に比較するため重複とみなす。
  - 新規登録は行わない。
  - 既存重複時の `name` / `source` は、`TopicStore.find_topic_by_canonical_name(...)` が返した代表レコードをそのまま使うため、同じ `canonical_name` の候補を一覧取得した場合と同じ値に揃う。

## 例3: 大小文字差分と全半角差分を重複として扱う

- 入力:
  ```yaml
  raw_name: "ｔｅｒｒａｆｏｒｍ"
  topic_store.find_topic_by_canonical_name("terraform"):
    { name: "Terraform", canonical_name: "terraform", source: "preset" }
  note_count_reader.list_note_counts(["terraform"]):
    - { canonical_name: "terraform", note_count: 2 }
  ```
- 期待される出力:
  ```yaml
  { name: "Terraform", source: "preset", note_count: 2 }
  ```
- 補足:
  - 比較キーは `NFKC` と `casefold()` を適用するため、全角英字と大小文字差分は吸収する。
  - 戻り値 DTO は一覧と同じ `TopicCandidate` であり、`source` は既存レコードの値を返す。

## 例4: 新規登録時も `note_count_reader` の結果を使う

- 入力:
  ```yaml
  raw_name: "GraphRAG"
  topic_store.find_topic_by_canonical_name("graphrag"):
    null
  topic_store.create_manual_topic(name="GraphRAG", canonical_name="graphrag"):
    { name: "GraphRAG", canonical_name: "graphrag", source: "manual" }
  note_count_reader.list_note_counts(["graphrag"]):
    []
  ```
- 期待される出力:
  ```yaml
  { name: "GraphRAG", source: "manual", note_count: 0 }
  ```
- 補足:
  - 新規登録時も `note_count_reader.list_note_counts([canonical_name])` を 1 回呼ぶ。
  - 件数未返却時は `note_count=0` を返す。

# 技術判断

- プリセットを用意する理由:
  自由入力だけだと表記ゆれが起きる。また「何を入力すればいいかわからない」問題を防ぐ。
- プリセットの粒度:
  「ロードマップを作る意味がある単位」。初期はメジャーなトピックのみ、後から追加可能。
- `note_count` を含める理由:
  ノートがあるトピックは「既に学習中」であることを示す手がかりになる。
- 候補統合を `canonical_name` 単位で行う理由:
  `source` 違いだけで同名候補が重複表示されると、ユーザーが同じトピックを別候補だと誤解するため。
- 自由入力の保存値と比較値を分ける理由:
  表示名はユーザー入力のトリム済み文字列を保ちつつ、重複判定は決定的にしたいため。

# 境界条件

- プリセットはあるがノート由来タグも自由入力登録済みトピックもない（初回起動時）:
  プリセットのみが返る。
- プリセット、ノート由来タグ、自由入力登録済みトピックで同じ `canonical_name` が重なる:
  各 record が同じ比較用正規化済み `canonical_name` を返す前提で一覧では 1 件に統合し、`source` / `name` は `preset` → `manual` → `note` 優先で決める。
- 自由入力のトピック名が既存トピックと重複する:
  `canonical_name` 一致なら一覧取得時と同じ代表トピックを `TopicCandidate` で返し、新規登録しない。
- 一覧取得で件数を引く:
  集約対象の `canonical_name` を重複排除し、`canonical_name` 昇順に並べた配列で `note_count_reader.list_note_counts` を 1 回だけ呼ぶ。これは最終返却順とは別に固定する。
- 自由入力の新規登録が成功する:
  `topic_store.create_manual_topic` の後に `note_count_reader.list_note_counts([canonical_name])` を 1 回呼び、件数未返却時は `note_count=0` を返す。
- 自由入力が前後空白のみ:
  `TopicListingEmptyTopicNameError` を送出する。
- 自由入力で登録済みだがノート未紐付け:
  一覧に含め、`note_count=0` を返す。
- 同一ノート内で同じトピックが複数回出現:
  `TopicNoteCountReader` の件数意味論では、そのノートは 1 件として数える。`topic_listing` 本体は返却された件数をそのまま採用する。

# 非機能・制約

- 外部依存:
  依存先は `Protocol` で表現した `TopicPresetReader`、`NoteTopicReader`、`TopicStore`、`TopicNoteCountReader` のみ。RDB 実装、タグ生成実装、ノート保存形式の詳細はこの機能の契約に含めない。

# モジュール構成

- 構成方針:
  DTO・Protocol・例外を `types` 側に分離し、一覧統合、正規化、登録オーケストレーションを本体モジュールにまとめる。
- 配置先:
  `backend/roadmap/infrastructure/` 配下に配置する。
- モジュール一覧:
  - `topic_listing_types.py`
    - 責務: DTO（`TopicCandidate`、`PresetTopicRecord`、`NoteTopicRecord`、`StoredTopicRecord`、`TopicNoteCountRecord`）、Protocol（`TopicPresetReader`、`NoteTopicReader`、`TopicStore`、`TopicNoteCountReader`）、例外型（`TopicListingEmptyTopicNameError`）の定義
  - `topic_listing.py`
    - 責務: `list_topic_candidates` と `register_manual_topic` の公開 API、自由入力の保存用正規化と比較用正規化、候補統合、`note_count` 付与、安定ソート

# スコープ外

- プリセットの管理画面（追加・削除は DB 直接操作またはシードデータ更新）
- トピックの階層構造（タグはフラット）
- トピックの統合・リネーム機能
- 同義語辞書ベース統合、略語展開、部分一致、形態素解析などの高度な表記ゆれ吸収
- HTTP エンドポイントの実装（presentation 層で別途実装）
- ロードマップ生成そのものの実装と、このモジュール外で `TopicCandidate` を downstream へ受け渡す連携方法

# 受け入れ基準

- [ ] 公開 API は `list_topic_candidates` と `register_manual_topic` の 2 つに固定され、どちらもモジュールレベル関数かつ keyword-only DI である
- [ ] 実装配置先が `backend/roadmap/infrastructure/topic_listing.py` と `backend/roadmap/infrastructure/topic_listing_types.py` に固定されている
- [ ] プリセットのトピック候補が一覧で返る
- [ ] ノートから自動生成されたタグがトピック候補に含まれる
- [ ] 自由入力で登録済みのトピックが一覧候補に含まれる
- [ ] 同じ `canonical_name` の候補は 1 件に統合され、`source` / `name` は `preset` → `manual` → `note` 優先で決まる
- [ ] `PresetTopicRecord`、`NoteTopicRecord`、`StoredTopicRecord`、`TopicNoteCountRecord` と各依存インターフェースが扱う `canonical_name` は、前後空白除去後に `NFKC + casefold()` を適用した比較用キーで統一される
- [ ] 各トピックに関連ノート件数が付与され、`TopicNoteCountReader` が件数を返さない `canonical_name` には `note_count=0` を採用する
- [ ] ノート未紐付けの候補は `note_count=0` で返る
- [ ] `list_topic_candidates` は集約対象の `canonical_name` を重複排除して `canonical_name` 昇順に並べた配列で `note_count_reader.list_note_counts` を 1 回だけ呼び、reader の返却順には依存せず、返却 `canonical_name` の重複も前提にしない
- [ ] 一覧の返却順は `note_count` 降順、同値時は `canonical_name` 昇順で安定化され、reader/store の返却順に依存しない
- [ ] `register_manual_topic` は前後空白除去後に空でない自由入力を受け付け、一覧と同じ `TopicCandidate` を返すため、呼び出し元は追加 API なしで登録結果の `name` / `source` / `note_count` を公開戻り値から観測できる
- [ ] 自由入力したトピックの新規登録時は `topic_store.create_manual_topic(name=normalized_name, canonical_name=canonical_name)` を 1 回呼び、manual topic を永続化対象として作成する
- [ ] 既存トピックと重複する自由入力は、前後空白除去と `NFKC + casefold()` 適用後の `canonical_name` 一致で判定され、新規登録されない
- [ ] `register_manual_topic` の戻り値は一覧と同じ `TopicCandidate` であり、既存重複時の `name` / `source` は `topic_store.find_topic_by_canonical_name(...)` が返した代表 record をそのまま使うため、一覧取得時の代表候補と一致する
- [ ] `register_manual_topic` は既存重複時も新規登録時も `note_count_reader.list_note_counts([canonical_name])` を 1 回だけ呼び、その返却値を `note_count` に採用し、未返却時は `0` を返す
- [ ] 前後空白のみの自由入力は `TopicListingEmptyTopicNameError` を送出し、戻り値 DTO では表現しない
