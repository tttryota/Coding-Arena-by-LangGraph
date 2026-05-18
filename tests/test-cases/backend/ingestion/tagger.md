---
status: ready
---

# テストケース一覧

# 検証焦点

| テストの種類 | 検証焦点 |
|---|---|
| Phase 1（最小骨格） | `chunk_index` / `tags` の基本返却形、入力順保持、空結果 |
| Phase 2（コアロジック） | 既存タグ優先、新規タグ許可条件、大分類タグ、重複排除、順序、本文保持 |
| Phase 3（エッジケース） | 空入力、既存タグ正規化、候補外タグ、粒度不一致、空本文 |
| Phase 4（外部連携） | `TaggingPromptStrategy` / `LlmTagClassifier` 契約、例外送出、可観測性 |

## Phase 1: 最小骨格

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-01 | 既存タグありの単一チャンクで最小結果を 1 件返す | `prompt_strategy.build_prompt(chunk_text, existing_tags)` は正常に `PromptPayload` を返し、`llm_client.classify()` は `["TypeScript"]` を返す | `chunks = [{chunk_index: 0, text: "TypeScript のジェネリクスを整理した。"}]`、`existing_tags = ["TypeScript", "React", "Docker"]` | `[{chunk_index: 0, tags: ["TypeScript"]}]` を返す | 全フィールドの最小正常系 |
| TC-02 | 分類困難な単一チャンクは空リストを返す | `prompt_strategy` は正常、`llm_client.classify()` は `[]` を返す | `chunks = [{chunk_index: 5, text: "今日は学習メモを見直し、次に何を読むか考えた。"}]`、`existing_tags = ["TypeScript", "React", "Docker"]` | `[{chunk_index: 5, tags: []}]` を返す | 正常系の空結果 |
| TC-03 | `chunks=[]` は空リストを返し外部依存を呼ばない | `prompt_strategy` と `llm_client` はスパイ可能 | `chunks = []`、`existing_tags = ["TypeScript"]` | `[]` を返し、`prompt_strategy.build_prompt()` と `llm_client.classify()` は 1 回も呼ばれない | 最小境界 |

## Phase 2: コアロジック

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-10 | 複数チャンクを独立に判定し、入力順を結果順として保持する | `prompt_strategy` は呼び出しごとに受け取った `chunk_text` を記録し、`llm_client.classify()` は 1 件目で `["Docker"]`、2 件目で `["React"]` を返す | `chunks = [{chunk_index: 4, text: "Docker Compose でアプリと PostgreSQL を起動する。"}, {chunk_index: 1, text: "useEffect の依存配列を整理した。"}]`、`existing_tags = ["React", "Docker", "PostgreSQL"]` | `[{chunk_index: 4, tags: ["Docker"]}, {chunk_index: 1, tags: ["React"]}]` をこの順で返し、各 `build_prompt()` 呼び出しは対応チャンクの本文だけを受け取る | `chunk_index` の数値順へ並べ替えないことも確認 |
| TC-11 | 既存タグがある場合は候補内のみ採用し、重複は先勝ち除去し、最終順序は `existing_tags` に従う | `llm_client.classify()` は `["PostgreSQL", "Docker", "Docker", "MySQL"]` を返す | `chunks = [{chunk_index: 0, text: "Docker Compose でアプリケーションと PostgreSQL をまとめて起動する。"}]`、`existing_tags = ["Docker", "PostgreSQL", "Linux"]` | `[{chunk_index: 0, tags: ["Docker", "PostgreSQL"]}]` を返す | `MySQL` は候補外なので不採用 |
| TC-12 | `existing_tags` が空のときのみ新規タグを返し、重複除去後も LLM の返却順を維持する | `llm_client.classify()` は `["tRPC", "TypeScript", "tRPC"]` を返す | `chunks = [{chunk_index: 3, text: "tRPC の router 定義と end-to-end 型安全の利点を整理した。"}]`、`existing_tags = []` | `[{chunk_index: 3, tags: ["tRPC", "TypeScript"]}]` を返す | 新規タグ生成許可の正常系 |
| TC-13 | Obsidian 内部リンク記法を変形せず `prompt_strategy` へ渡す | `prompt_strategy` は受け取った `chunk_text` を検査でき、`llm_client.classify()` は `["TypeScript"]` を返す | `chunks = [{chunk_index: 0, text: "TypeScript のジェネリクスを整理した。[[TypeScript公式ドキュメント]] と [[型システム|型安全]] を参照。"}]`、`existing_tags = ["TypeScript", "React"]` | `build_prompt()` は `[[TypeScript公式ドキュメント]]` と `[[型システム|型安全]]` を含む原文そのままを受け取り、返却値は `[{chunk_index: 0, tags: ["TypeScript"]}]` になる | 本文前処理の禁止を確認 |
| TC-14 | `existing_tags` はプロンプト構築前に trim・空文字除外・先勝ち一意化される | `prompt_strategy` は受け取った `existing_tags` を検査でき、`llm_client.classify()` は `["React"]` を返す | `chunks = [{chunk_index: 0, text: "React の useEffect を整理した。"}]`、`existing_tags = ["  React  ", "", "React", " TypeScript "]` | `build_prompt()` は `["React", "TypeScript"]` を受け取り、返却値は `[{chunk_index: 0, tags: ["React"]}]` になる | 境界条件の正規化をルール本体に接続して確認 |
| TC-15 | 正規化後の `existing_tags` が空なら「新規タグ生成可」に切り替わる | `prompt_strategy` は正規化後タグを検査でき、`llm_client.classify()` は `["SQL"]` を返す | `chunks = [{chunk_index: 2, text: "LEFT JOIN の使いどころを整理した。"}]`、`existing_tags = [" ", ""]` | `build_prompt()` は `[]` を受け取り、返却値は `[{chunk_index: 2, tags: ["SQL"]}]` になる | ルール間相互作用 1 の確認 |
| TC-16 | 下位概念を主題とする本文でも、返却タグは大分類レベルを許容する | `llm_client.classify()` は `["React"]` を返す | `chunks = [{chunk_index: 7, text: "useEffect の依存配列とクリーンアップの挙動を整理した。"}]`、`existing_tags = ["React", "TypeScript"]` | `[{chunk_index: 7, tags: ["React"]}]` を返す | 大分類丸めの正常系 |

## Phase 3: エッジケース

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-20 | 既存タグが非空で候補外タグしか返らない場合は空リストになり、新規生成へフォールバックしない | `llm_client.classify()` は `["TS", "JavaScript"]` を返す | `chunks = [{chunk_index: 1, text: "TypeScript の型推論を整理した。"}]`、`existing_tags = ["TypeScript", "React"]` | `[{chunk_index: 1, tags: []}]` を返す | 既存タグ優先の境界 |
| TC-21 | チャンク本文が空文字または空白のみなら `tags=[]` を返す | `llm_client.classify()` の返却値は任意とし、たとえば `["Docker"]` を返してもよい | `chunks = [{chunk_index: 0, text: ""}, {chunk_index: 1, text: " \n\t "}]`、`existing_tags = ["Docker"]` | `[{chunk_index: 0, tags: []}, {chunk_index: 1, tags: []}]` をこの順で返す | LLM を呼ぶかどうかは問わない |
| TC-22 | `existing_tags` が空で、LLM が細かすぎるタグしか返せない場合は `TaggingResponseFormatError` ではなく空リストに丸める | `llm_client.classify()` は `["LEFT JOIN", "ON句"]` を返す | `chunks = [{chunk_index: 2, text: "LEFT JOIN と ON 句の違いを整理した。"}]`、`existing_tags = []` | `[{chunk_index: 2, tags: []}]` を返す | 粒度不一致の扱い |
| TC-23 | 1 チャンクが既存タグの複数候補にまたがる場合は関連する全タグを返せる | `llm_client.classify()` は `["PostgreSQL", "Docker"]` を返す | `chunks = [{chunk_index: 6, text: "Docker Compose で PostgreSQL を立ち上げ、コンテナ間通信も確認した。"}]`、`existing_tags = ["Docker", "PostgreSQL", "Linux"]` | `[{chunk_index: 6, tags: ["Docker", "PostgreSQL"]}]` を返す | 1 つに絞らないことの確認 |
| TC-24 | `existing_tags` がすべて重複・空白由来でも、正規化結果が非空なら既存タグ限定を維持する | `prompt_strategy` は受け取った `existing_tags` を検査でき、`llm_client.classify()` は `["React", "Vue"]` を返す | `chunks = [{chunk_index: 0, text: "React Hooks の整理。"}]`、`existing_tags = [" React ", "React", " "]` | `build_prompt()` は `["React"]` を受け取り、返却値は `[{chunk_index: 0, tags: ["React"]}]` になる | 正規化後空判定の逆側 |

## Phase 4: 外部連携

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-30 | `TaggingPromptStrategy` を差し替えても tagger 本体の入出力契約は変わらない | 戦略 A / B がともに `build_prompt(chunk_text, existing_tags) -> PromptPayload` を実装し、各 `PromptPayload` に対して `llm_client.classify()` は `["Docker"]` を返す | 同一の `chunks = [{chunk_index: 0, text: "Docker ネットワークを整理した。"}]`、`existing_tags = ["Docker", "Linux"]` を戦略 A と戦略 B でそれぞれ実行する | いずれも `[{chunk_index: 0, tags: ["Docker"]}]` を返す | プロンプト文面を本体が保持しないことの確認 |
| TC-31 | `prompt_strategy` がプロンプトを構築できない場合は `TaggingPromptBuildError` を送出する | `prompt_strategy.build_prompt()` が 1 件目のチャンクで失敗する | `chunks = [{chunk_index: 0, text: "React Hooks を整理した。"}]`、`existing_tags = ["React"]` | `TaggingPromptBuildError` を送出し、結果リストを返さない | 例外契約 |
| TC-32 | `llm_client` 呼び出し失敗時は `TaggingLlmCallError` を送出する | `prompt_strategy` は正常、`llm_client.classify()` がタイムアウトまたは接続失敗で失敗する | `chunks = [{chunk_index: 0, text: "Docker Compose を整理した。"}]`、`existing_tags = ["Docker"]` | `TaggingLlmCallError` を送出し、結果リストを返さない | モデル実行失敗も同系統で扱う |
| TC-33 | `llm_client` が `list[str]` として解釈できない値を返した場合は `TaggingResponseFormatError` を送出する | `prompt_strategy` は正常、`llm_client.classify()` は `{"tags": ["Docker"]}` を返す | `chunks = [{chunk_index: 0, text: "Docker Compose を整理した。"}]`、`existing_tags = ["Docker"]` | `TaggingResponseFormatError` を送出し、結果リストを返さない | 非リスト応答 |
| TC-34 | `llm_client` がリストを返しても要素に文字列以外が含まれる場合は `TaggingResponseFormatError` を送出する | `prompt_strategy` は正常、`llm_client.classify()` は `["Docker", 1]` を返す | `chunks = [{chunk_index: 0, text: "Docker Compose を整理した。"}]`、`existing_tags = ["Docker"]` | `TaggingResponseFormatError` を送出し、結果リストを返さない | 非 `str` 要素の契約違反 |
| TC-35 | 呼び出し元が `source_path`・件数系メトリクスを記録できる | `source_path = "notes/react.md"` を持つ呼び出しコンテキストで実行し、ログまたはメトリクス収集基盤を有効化する。`llm_client.classify()` は 1 件目で `["React"]`、2 件目で `[]` を返す | `chunks = [{chunk_index: 0, text: "React Hooks を整理した。"}, {chunk_index: 1, text: "今日は次に読む記事を考えた。"}]`、`existing_tags = ["React", "TypeScript"]` | 非エラーで `[{chunk_index: 0, tags: ["React"]}, {chunk_index: 1, tags: []}]` を返し、呼び出し元は `source_path`、各 `chunk_index`、`使用した既存タグ件数 = 2`、`生成タグ件数 = 1`、`空リストになった件数 = 1`、`LLM 呼び出し失敗件数 = 0` を記録できる | 可観測性 |

# 網羅性チェック

仕様書の受け入れ基準の各項目に対応するテストケース ID を記載する。
全項目が少なくとも1つのテストケースでカバーされていることを確認する。

| 受け入れ基準 | 対応テストケース |
|---|---|
| 既存タグ一覧が非空のとき、返されるタグは既存タグ一覧の完全一致文字列のみに制限される | TC-11, TC-20, TC-24 |
| 既存タグ一覧が空のときのみ、新規タグ生成結果を返せる | TC-12, TC-15, TC-20 |
| 1 チャンクに対して複数タグを返せる | TC-11, TC-23 |
| 分類困難なチャンクは例外ではなく空リストになる | TC-02, TC-21, TC-22 |
| Obsidian 内部リンク記法を変形せずに LLM へ渡すことが仕様として定義されている | TC-13 |
| プロンプト生成が `TaggingPromptStrategy` の外部注入であることが明記されている | TC-30, TC-31 |
| 大分類レベルのタグに丸めるルールが定義されている | TC-16, TC-22 |
| 境界条件とルール間相互作用から、候補外タグや空入力の扱いを一意に判断できる | TC-03, TC-15, TC-20, TC-21, TC-22, TC-24 |

# 記述ルール

- 仕様書に明記された振る舞いだけを前提にする
- 仕様未記載の振る舞いを期待結果に置く場合は `[要仕様追記]` タグを付ける
- 正常系・境界系・異常系が重複なく網羅されていることを確認する
- 仕様書の受け入れ基準の各項目に対応するテストケースが最低1つあることを確認する
