---
status: ready
---

# テストケース一覧

# 検証焦点

| テストの種類 | 検証焦点 |
|---|---|
| Phase 1（最小骨格） | モジュール配置、公開 API の存在確認と不在確認、DTO/Protocol の静的契約、最小正常系の戻り値全フィールド |
| Phase 2（コアロジック） | 3 ソース統合、`canonical_name` 単位の重複排除、`source` / `name` 優先順、`note_count` 付与、ソート、既存重複登録 |
| Phase 3（エッジケース） | 0 件一覧、空白入力エラー、保存値と比較値の分離、内部空白保持 |
| Phase 4（外部連携） | reader/store 呼び出し回数、非呼び出し確認、keyword-only DI に沿った連携引数 |

## Phase 1: 最小骨格

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-01 | 実装配置先と `inspect` / `dataclasses` で観測できる公開 API / types の静的契約が仕様どおりであり、公開エントリポイントの不在条件も満たす | Python から `backend.roadmap.infrastructure.topic_listing` と `backend.roadmap.infrastructure.topic_listing_types` を import でき、`inspect` / `dataclasses` / 型注釈を検査できる | `topic_listing.py` と `topic_listing_types.py` を import し、モジュールパス・公開属性集合・公開関数・シグネチャ・dataclass 定義・Protocol メソッド注釈を検査する | [topic_listing.py](/Users/tsuryoryo/Desktop/repo/obsidian-topic-listing/backend/roadmap/infrastructure/topic_listing.py) と [topic_listing_types.py](/Users/tsuryoryo/Desktop/repo/obsidian-topic-listing/backend/roadmap/infrastructure/topic_listing_types.py) が存在する。`topic_listing` に存在する公開エントリポイントはモジュールレベル関数 `list_topic_candidates` と `register_manual_topic` の 2 つだけであり、これらと別名で同一 callable を再公開する追加名は存在しない。公開クラスや公開オブジェクトに、同等機能を classmethod / staticmethod 経由で再公開する API も存在しない。`list_topic_candidates` のシグネチャは `(*, preset_reader, note_topic_reader, topic_store, note_count_reader)` と完全一致し、依存はすべて keyword-only で、位置引数 DI を許す引数は存在しない。`register_manual_topic` のシグネチャは `(raw_name, *, topic_store, note_count_reader)` と完全一致し、業務入力は `raw_name` だけで、DI 引数はすべて keyword-only である。`topic_listing_types` には `TopicCandidate`、`PresetTopicRecord`、`NoteTopicRecord`、`StoredTopicRecord`、`TopicNoteCountRecord`、`TopicPresetReader`、`NoteTopicReader`、`TopicStore`、`TopicNoteCountReader`、`TopicListingEmptyTopicNameError` が定義されている。DTO 5 種はすべて frozen dataclass であり、必須フィールドと型注釈は `TopicCandidate(name: str, source: Literal["preset", "note", "manual"], note_count: int)`、`PresetTopicRecord(name: str, canonical_name: str)`、`NoteTopicRecord(name: str, canonical_name: str)`、`StoredTopicRecord(name: str, canonical_name: str, source: Literal["preset", "note", "manual"])`、`TopicNoteCountRecord(canonical_name: str, note_count: int)` と完全一致する。`TopicCandidate.source` と `StoredTopicRecord.source` の許容値が `preset` / `note` / `manual` であることを型注釈上で確認する。Protocol 4 種の必須メソッドと注釈上の返却型は `TopicPresetReader.list_preset_topics(self) -> list[PresetTopicRecord]`、`NoteTopicReader.list_note_topics(self) -> list[NoteTopicRecord]`、`TopicStore.list_manual_topics(self) -> list[StoredTopicRecord]`、`TopicStore.find_topic_by_canonical_name(self, canonical_name: str) -> StoredTopicRecord | None`、`TopicStore.create_manual_topic(self, name: str, canonical_name: str) -> StoredTopicRecord`、`TopicNoteCountReader.list_note_counts(self, canonical_names: list[str]) -> list[TopicNoteCountRecord]` と完全一致する | `inspect` / `dataclasses` / 型注釈で観測できる静的契約に限定し、存在確認と不在確認を同一 TC で行う。依存契約の実行時意味論は対象外とする |
| TC-02 | プリセットのみ存在する初回相当状態で候補一覧を返し、`note_count` 未返却分を 0 にする | `preset_reader.list_preset_topics()`、`note_topic_reader.list_note_topics()`、`topic_store.list_manual_topics()`、`note_count_reader.list_note_counts(...)` の引数と戻り値を制御できるテストダブルを用意する | `list_topic_candidates(*, preset_reader=..., note_topic_reader=..., topic_store=..., note_count_reader=...)`。`preset_reader.list_preset_topics()` は返却順不定で `[{name: "Docker", canonical_name: "docker"}, {name: "TypeScript", canonical_name: "typescript"}]` を返す。`note_topic_reader.list_note_topics()` は `[]`、`topic_store.list_manual_topics()` は `[]`、`note_count_reader.list_note_counts(["docker", "typescript"])` は `[{canonical_name: "typescript", note_count: 2}]` を返す | 戻り値は `TopicCandidate` 2 件をちょうど含み、`[{name: "TypeScript", source: "preset", note_count: 2}, {name: "Docker", source: "preset", note_count: 0}]` と完全一致する。プリセット候補が一覧に含まれること、`note_count_reader` が返さなかった `docker` の `note_count` が `0` になること、返却順が `note_count` 降順かつ同値なしで決まることを確認する | 初回起動時相当の最小正常系 |
| TC-03 | 新規の自由入力トピックを登録し、一覧と同じ `TopicCandidate` を返す | `topic_store.find_topic_by_canonical_name(...)`、`topic_store.create_manual_topic(...)`、`note_count_reader.list_note_counts(...)` の入出力を制御できるテストダブルを用意する | `register_manual_topic(" GraphRAG ", *, topic_store=..., note_count_reader=...)`。`topic_store.find_topic_by_canonical_name("graphrag")` は `None`、`topic_store.create_manual_topic(name="GraphRAG", canonical_name="graphrag")` は `{name: "GraphRAG", canonical_name: "graphrag", source: "manual"}` を返し、`note_count_reader.list_note_counts(["graphrag"])` は `[]` を返す | 戻り値は `TopicCandidate(name="GraphRAG", source="manual", note_count=0)` と完全一致する。保存用正規化が前後空白除去だけであること、一覧と同じ DTO で `name` / `source` / `note_count` を観測できること、新規登録時でも `note_count_reader` の未返却分が `0` になることを確認する | 新規登録の最小正常系 |

## Phase 2: コアロジック

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-10 | 3 ソースを `canonical_name` 単位で統合し、`preset -> manual -> note` 優先、`note_count` 付与、最終ソートを一度に満たす | 各 reader/store の返却順を任意順にでき、`note_count_reader.list_note_counts(...)` の受け取り引数を検査できる | `list_topic_candidates(*, ...)`。`preset_reader.list_preset_topics()` は `[{name: "React", canonical_name: "react"}, {name: "Docker", canonical_name: "docker"}, {name: "TypeScript", canonical_name: "typescript"}]`、`note_topic_reader.list_note_topics()` は `[{name: "docker", canonical_name: "docker"}, {name: "LangGraph", canonical_name: "langgraph"}, {name: "react", canonical_name: "react"}]`、`topic_store.list_manual_topics()` は `[{name: "Terraform", canonical_name: "terraform", source: "manual"}, {name: "React Manual", canonical_name: "react", source: "manual"}]` を返す。`note_count_reader.list_note_counts(["docker", "langgraph", "react", "terraform", "typescript"])` は返却順不定で `[{canonical_name: "docker", note_count: 3}, {canonical_name: "typescript", note_count: 12}, {canonical_name: "langgraph", note_count: 5}]` を返す | `note_count_reader.list_note_counts(...)` は、集約対象の `canonical_name` を重複排除して `["docker", "langgraph", "react", "terraform", "typescript"]` の昇順配列でちょうど 1 回だけ呼ばれる。戻り値はちょうど 5 件で、`[{name: "TypeScript", source: "preset", note_count: 12}, {name: "LangGraph", source: "note", note_count: 5}, {name: "Docker", source: "preset", note_count: 3}, {name: "React", source: "preset", note_count: 0}, {name: "Terraform", source: "manual", note_count: 0}]` と完全一致する。`docker` は preset と note の重複でも 1 件だけ、`react` は preset / manual / note の 3 重複でも 1 件だけ返り、`name` / `source` は常に最優先ソースの record を使う。reader/store の返却順と `list_note_counts` の返却順に依存しないことを確認する | 仕様書 例1 を拡張して 3 重複も含める主ケース |
| TC-11 | preset がない重複では manual が note より優先される | 各 reader/store の返却値を制御できるテストダブルを用意する | `list_topic_candidates(*, ...)`。`preset_reader.list_preset_topics()` は `[]`、`note_topic_reader.list_note_topics()` は `[{name: "terraform", canonical_name: "terraform"}]`、`topic_store.list_manual_topics()` は `[{name: "Terraform", canonical_name: "terraform", source: "manual"}]` を返す。`note_count_reader.list_note_counts(["terraform"])` は `[{canonical_name: "terraform", note_count: 7}]` を返す | 戻り値は `[{name: "Terraform", source: "manual", note_count: 7}]` と完全一致する。`canonical_name="terraform"` の候補は 1 件に統合され、`preset` 不在時は `manual` が `note` より優先されることを確認する | `manual > note` の優先順を単独で検証 |
| TC-12 | 既存トピックとの重複登録では `NFKC + casefold()` の比較キーで find し、store が返した代表 record をそのまま返して新規登録しない | `topic_store.find_topic_by_canonical_name(...)` の引数と `create_manual_topic(...)` の非呼び出しを検査できるテストダブルを用意する | `register_manual_topic("ｔｅｒｒａｆｏｒｍ", *, topic_store=..., note_count_reader=...)`。`topic_store.find_topic_by_canonical_name("terraform")` は `{name: "Terraform", canonical_name: "terraform", source: "preset"}` を返し、`note_count_reader.list_note_counts(["terraform"])` は `[{canonical_name: "terraform", note_count: 2}]` を返す | `topic_store.find_topic_by_canonical_name(...)` は `canonical_name="terraform"` でちょうど 1 回呼ばれる。`topic_store.create_manual_topic(...)` は 0 回である。戻り値は `TopicCandidate(name="Terraform", source="preset", note_count=2)` と完全一致する。全角英字と大小文字差分が吸収されること、既存重複時の `name` / `source` / `note_count` が `find_topic_by_canonical_name(...)` と `list_note_counts(...)` の返却値をそのまま反映することを確認する。`preset -> manual -> note` の代表選択自体は `TopicStore` 契約であり、本 TC の観測対象外とする | 仕様書 例3 に対応 |
| TC-13 | 重複判定は `canonical_name` 完全一致だけに限定され、部分一致や同義語扱いはしない | `topic_store.find_topic_by_canonical_name(...)` が exact match のみを見るテストダブルを用意する | `register_manual_topic("Type", *, topic_store=..., note_count_reader=...)`。既存データとして `canonical_name="typescript"` の topic は存在するとみなすが、`topic_store.find_topic_by_canonical_name("type")` は `None` を返す。`topic_store.create_manual_topic(name="Type", canonical_name="type")` は `{name: "Type", canonical_name: "type", source: "manual"}` を返し、`note_count_reader.list_note_counts(["type"])` は `[]` を返す | 戻り値は `TopicCandidate(name="Type", source="manual", note_count=0)` と完全一致する。`Type` は `TypeScript` と同義語辞書・部分一致・あいまい一致では重複扱いされず、`canonical_name` 完全一致だけで判定されることを確認する | スコープ外機能を採らないことの確認 |

## Phase 3: エッジケース

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-20 | 3 ソースがすべて空でも一覧取得は正常終了する | 4 依存の呼び出し回数を検査できるテストダブルを用意する | `list_topic_candidates(*, ...)`。`preset_reader.list_preset_topics()`、`note_topic_reader.list_note_topics()`、`topic_store.list_manual_topics()` はすべて `[]` を返し、`note_count_reader.list_note_counts([])` は `[]` を返す | 戻り値は空リスト `[]` と完全一致する。`note_count_reader.list_note_counts(...)` は空配列 `[]` でちょうど 1 回だけ呼ばれる。reader/store の返却順に依存せず、0 件でも非エラーであることを確認する | 一覧 0 件の境界条件 |
| TC-21 | 前後空白除去後に空文字となる自由入力は `TopicListingEmptyTopicNameError` を送出し、外部依存を呼ばない | `topic_store` と `note_count_reader` の全メソッド呼び出し有無を検査できるテストダブルを用意する | `register_manual_topic("   ", *, topic_store=..., note_count_reader=...)` | `TopicListingEmptyTopicNameError` を送出する。検証対象は例外型と依存の非呼び出しであり、message は仕様未規定のため検証対象外とする。`topic_store.find_topic_by_canonical_name(...)`、`topic_store.create_manual_topic(...)`、`note_count_reader.list_note_counts(...)` はいずれも 0 回である | 仕様書の唯一の異常系 |
| TC-22 | 保存用正規化名は内部空白を保持し、比較用 `canonical_name` だけに `NFKC + casefold()` を適用する | `create_manual_topic(...)` の引数文字列を厳密比較できるテストダブルを用意する | `register_manual_topic("  AI　Agent  ", *, topic_store=..., note_count_reader=...)`。`topic_store.find_topic_by_canonical_name("ai agent")` は `None`、`topic_store.create_manual_topic(name="AI　Agent", canonical_name="ai agent")` は `{name: "AI　Agent", canonical_name: "ai agent", source: "manual"}` を返し、`note_count_reader.list_note_counts(["ai agent"])` は `[]` を返す | 戻り値は `TopicCandidate(name="AI　Agent", source="manual", note_count=0)` と完全一致する。保存値 `name` は前後空白だけ除去した `AI　Agent` であり、内部の全角空白は保持される。比較用 `canonical_name` は `NFKC + casefold()` 適用後の `ai agent` であり、内部空白の潰し込みや追加の文字変換は保存値には反映されないことを確認する | 保存値と比較値の分離を明示検証 |

## Phase 4: 外部連携

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-30 | `list_topic_candidates` は 4 依存を所定メソッドだけ 1 回ずつ呼び、登録系メソッドは使わない | `TopicPresetReader`、`NoteTopicReader`、`TopicStore`、`TopicNoteCountReader` の各メソッド呼び出し回数を個別に検査できるテストダブルを用意する | `list_topic_candidates(*, ...)`。返却データは任意の 1 件ずつでよい | `preset_reader.list_preset_topics()`、`note_topic_reader.list_note_topics()`、`topic_store.list_manual_topics()`、`note_count_reader.list_note_counts(...)` はそれぞれちょうど 1 回だけ呼ばれる。`topic_store.find_topic_by_canonical_name(...)` と `topic_store.create_manual_topic(...)` は 0 回である | 一覧取得の依存境界を確認 |
| TC-31 | 既存重複の自由入力登録では find のみで重複判定し、create を呼ばずに件数取得する | `topic_store.find_topic_by_canonical_name(...)`、`topic_store.create_manual_topic(...)`、`note_count_reader.list_note_counts(...)` の呼び出し回数と引数を検査できるテストダブルを用意する | `register_manual_topic(" Terraform ", *, topic_store=..., note_count_reader=...)`。`topic_store.find_topic_by_canonical_name("terraform")` は `{name: "Terraform", canonical_name: "terraform", source: "manual"}` を返し、`note_count_reader.list_note_counts(["terraform"])` は `[]` を返す | `topic_store.find_topic_by_canonical_name("terraform")` はちょうど 1 回、`topic_store.create_manual_topic(...)` は 0 回、`note_count_reader.list_note_counts(["terraform"])` はちょうど 1 回呼ばれる。戻り値は `TopicCandidate(name="Terraform", source="manual", note_count=0)` と完全一致する | 仕様書 例2 に対応 |
| TC-32 | 新規の自由入力登録では create を 1 回だけ呼び、keyword-only DI の契約どおりに件数取得まで完了する | `find` / `create` / `list_note_counts` の引数と回数を検査できるテストダブルを用意する | `register_manual_topic("GraphRAG", *, topic_store=..., note_count_reader=...)`。`topic_store.find_topic_by_canonical_name("graphrag")` は `None`、`topic_store.create_manual_topic(name="GraphRAG", canonical_name="graphrag")` は `{name: "GraphRAG", canonical_name: "graphrag", source: "manual"}` を返し、`note_count_reader.list_note_counts(["graphrag"])` は `[{canonical_name: "graphrag", note_count: 4}]` を返す | `topic_store.find_topic_by_canonical_name("graphrag")` はちょうど 1 回、`topic_store.create_manual_topic(name="GraphRAG", canonical_name="graphrag")` はちょうど 1 回、`note_count_reader.list_note_counts(["graphrag"])` はちょうど 1 回呼ばれる。戻り値は `TopicCandidate(name="GraphRAG", source="manual", note_count=4)` と完全一致する | 新規登録時の依存呼び出し契約 |

# 網羅性チェック

仕様書の受け入れ基準の各項目に対応するテストケース ID を記載する。
全項目が少なくとも1つのテストケースでカバーされていることを確認する。

| 受け入れ基準 | 対応テストケース |
|---|---|
| 公開 API は `list_topic_candidates` と `register_manual_topic` の 2 つに固定され、どちらもモジュールレベル関数かつ keyword-only DI である | TC-01 |
| 実装配置先が `backend/roadmap/infrastructure/topic_listing.py` と `backend/roadmap/infrastructure/topic_listing_types.py` に固定されている | TC-01 |
| DTO 5 種の必須フィールド集合・型注釈・frozen dataclass 制約、および Protocol 4 種の必須メソッド名・引数シグネチャ・返却型注釈が静的契約として定義されている | TC-01 |
| プリセットのトピック候補が一覧で返る | TC-02, TC-10 |
| ノートから自動生成されたタグがトピック候補に含まれる | TC-10 |
| 自由入力で登録済みのトピックが一覧候補に含まれる | TC-10, TC-11 |
| 同じ `canonical_name` の候補は 1 件に統合され、`source` / `name` は `preset` → `manual` → `note` 優先で決まる | TC-10, TC-11 |
| `PresetTopicRecord`、`NoteTopicRecord`、`StoredTopicRecord`、`TopicNoteCountRecord` と各依存インターフェースが扱う `canonical_name` は、前後空白除去後に `NFKC + casefold()` を適用した比較用キーで統一される | TC-10, TC-12, TC-22 |
| 各トピックに関連ノート件数が付与され、`TopicNoteCountReader` が件数を返さない `canonical_name` には `note_count=0` を採用する | TC-02, TC-03, TC-10, TC-22, TC-31, TC-32 |
| ノート未紐付けの候補は `note_count=0` で返る | TC-02, TC-03, TC-10, TC-22, TC-31 |
| `list_topic_candidates` は集約対象の `canonical_name` を重複排除して `canonical_name` 昇順に並べた配列で `note_count_reader.list_note_counts` を 1 回だけ呼び、reader の返却順には依存せず、返却 `canonical_name` の重複も前提にしない | TC-10, TC-20, TC-30 |
| 一覧の返却順は `note_count` 降順、同値時は `canonical_name` 昇順で安定化され、reader/store の返却順に依存しない | TC-10 |
| `register_manual_topic` は前後空白除去後に空でない自由入力を受け付け、一覧と同じ `TopicCandidate` を返すため、呼び出し元は追加 API なしで登録結果の `name` / `source` / `note_count` を公開戻り値から観測できる | TC-03, TC-22 |
| 自由入力したトピックの新規登録時は `topic_store.create_manual_topic(name=normalized_name, canonical_name=canonical_name)` を 1 回呼び、manual topic を永続化対象として作成する | TC-03, TC-22, TC-32 |
| 既存トピックと重複する自由入力は、前後空白除去と `NFKC + casefold()` 適用後の `canonical_name` 一致で判定され、新規登録されない | TC-12, TC-31 |
| `register_manual_topic` の戻り値は一覧と同じ `TopicCandidate` であり、既存重複時の `name` / `source` は `topic_store.find_topic_by_canonical_name(...)` が返した代表 record をそのまま使うため、一覧取得時の代表候補と一致する | TC-12, TC-31 |
| `register_manual_topic` は既存重複時も新規登録時も `note_count_reader.list_note_counts([canonical_name])` を 1 回だけ呼び、その返却値を `note_count` に採用し、未返却時は `0` を返す | TC-03, TC-12, TC-22, TC-31, TC-32 |
| 前後空白のみの自由入力は `TopicListingEmptyTopicNameError` を送出し、戻り値 DTO では表現しない | TC-21 |

# 依存契約メモ

- `TopicNoteCountReader` が同一 `note_id` 内の複数出現を 1 件として数える集計意味論は依存契約であり、このテスト群では stub を通じた観測対象外とする。`topic_listing` 側の件数採用と未返却時 `0` は TC-02, TC-03, TC-10, TC-22, TC-31, TC-32 で観測する。
- `TopicStore.find_topic_by_canonical_name(...)` が同じ `canonical_name` の代表 1 件を `preset` → `manual` → `note` 優先で返す選択アルゴリズムは依存契約であり、このテスト群ではその内部選択自体を観測しない。`register_manual_topic` が store の返した代表 record をそのまま戻り値へ反映することは TC-12, TC-31 で観測する。

# 記述ルール

- 仕様書に明記された振る舞いだけを前提にする
- 仕様未記載の振る舞いを期待結果に置く場合は `[要仕様追記]` タグを付ける
- 正常系・境界系・異常系が重複なく網羅されていることを確認する
- 仕様書の受け入れ基準の各項目に対応するテストケースが最低1つあることを確認する
- 期待結果に「含まれる」「完全一致」「少なくとも1件」「ちょうど1件」などの検証粒度を明示する
- ログ検証を含む場合は、検証対象イベント名、必須キー、期待値、件数制約、追加キー許容の有無を明示する
- 例外検証を含む場合は、例外型、message、cause chain、ログ記録有無のうち何を確認するかを明示する
- テストが「存在確認」なのか「内容検証」なのかを期待結果で区別して書く
- テストケース文書に書いていない検証を impl レビューで追加要求しなくて済む粒度まで、期待結果を具体化する
