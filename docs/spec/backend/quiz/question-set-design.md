---
feature: question-set-design
status: ready
reviewed_by:
approved_at:
---

## 機能概要

セッション開始時に、ロードマップ項目の理解度を確認するための「確認ポイントリスト」を設計する。LLMが `SessionState.roadmap_item_title` と `SessionState.roadmap_item_description` から、何を確認すべきかを判断する。問題文自体はここでは作らず、出題ノードが都度生成する。

## 振る舞い

### 基本動作

`SessionState.roadmap_item_title` / `SessionState.roadmap_item_description` / `SessionState.roadmap_item_level` を受け取り、確認ポイントのリストを返す。

返却する各要素は、`SessionState.confirmation_points` に格納するものと同じ `ConfirmationPoint` DTO とする。

| フィールド | 型 | 意味 |
|---|---|---|
| `id` | `str` | 確認ポイント識別子。返却リスト内で一意な非空文字列 |
| `content` | `str` | 何を理解しているか確認するかを表す非空文字列 |
| `format` | `Literal["knowledge", "knowledge_and_practice"]` | 出題形式。`knowledge` は知識問題のみ、`knowledge_and_practice` は知識問題と実践問題をセットで出題する |

`QuestionSetDesignLlmClient.generate_confirmation_points(...)` の返却要素と、`design_question_set(...)` が返す `confirmation_points` の各要素は、この DTO と完全に一致する。

### 知識+実践のセット出題

コードで表現できる確認ポイントには、知識問題と実践問題をセットで出題する。概念的なポイントは知識問題のみ。この判断はLLMが行う。

### 確認ポイント数の制約

`roadmap_item_level` が `detail` / `middle` / `major` のいずれでも、LLMには1項目あたり3〜5個の確認ポイントを設計させる。これは node の返却値に対する hard postcondition ではなく設計目標であり、LLM が 2 件以下または 6 件以上を返した場合も、`design_question_set(...)` は warning を記録したうえでその返却件数を尊重して続行する。知識+実践のセット出題を含めると、通常は1セッション6〜10問程度を想定する。深掘りで追加される場合はこれを超えるが、20問を超えた場合は収束に向かう。

### まとめテストの扱い

`roadmap_item_level="middle"` または `roadmap_item_level="major"` のときも、入力として使うのは `SessionState` の `roadmap_item_title` / `roadmap_item_description` / `roadmap_item_level` のみとする。配下の具体項目や追加データソースは参照しない。

まとめテストでも、LLM には通常 3〜5 件を目標に確認ポイントを設計させる。`roadmap_item_title` / `roadmap_item_description` に対して重要度の高い観点、より広い理解を確認する観点へ寄せることは LLM への設計方針であり、この feature の公開契約としては観測可能な判定条件を定義しない。したがって、この性質は直接のテスト対象に含めない。

### 具体例

以下は参考例であり、特定の観点や文言の出現を必須契約化するものではない。

入力:
```
roadmap_item_title: "ジェネリクスの基本構文と型パラメータ"
roadmap_item_description: "TypeScriptのジェネリクスの基本的な構文と、型パラメータの使い方を理解する"
roadmap_item_level: "detail"
```

出力:
```
confirmation_points:
1. {id: "cp_001", content: "ジェネリクスの概念と必要性を説明できる", format: "knowledge"}
2. {id: "cp_002", content: "型パラメータの構文を理解している", format: "knowledge_and_practice"}
3. {id: "cp_003", content: "明示的型指定と型推論の違いを説明できる", format: "knowledge"}
4. {id: "cp_004", content: "ジェネリクスを使った関数定義を扱える", format: "knowledge_and_practice"}
5. {id: "cp_005", content: "any型と比較したジェネリクスの存在意義を説明できる", format: "knowledge"}
```

→ 確認ポイント5件。`knowledge_and_practice` が2件あるため、知識問題5問 + 実践問題2問 = 計7問（深掘りなしの場合）

## 技術判断

- 問題文ではなく確認ポイントを設計する理由: 問題文は前の問答の文脈を踏まえて出題ノードが都度生成する。事前に問題文を作ると文脈を無視した出題になる
- 知識+実践のセット出題を設ける理由: 概念を説明できてもコードに落とせないケースがある。生成AI時代にアウトプット力を鍛える場として両方を確認する
- 確認ポイント数を3〜5個に制約する理由: ロードマップ側で具体項目の粒度を制御することで、問題数の肥大化を防ぐ

## 境界条件

- `roadmap_item_description` が空 → `roadmap_item_title` のみから確認ポイントを設計する
- 概念的な項目でコード実践が不適切（例: 「プログラミングパラダイムの比較」） → 全て `format="knowledge"`
- まとめテスト（中枠・大枠） → `roadmap_item_title` / `roadmap_item_description` / `roadmap_item_level` だけを材料に設計する。重要度の高い観点へ寄せること自体は公開契約ではなく、非テスト対象の内部方針とする

## スコープ外

- 確認ポイントの手動編集
- 問題のテンプレート管理
- 難易度の段階設定
- 配下の具体項目を取得する追加入力や探索API
- `QuestionSetDesignLlmClient` の concrete client の配置先、raw JSON 文字列、内部プロンプト文面の公開契約化

## 受け入れ基準

- [ ] `SessionState.roadmap_item_title` / `SessionState.roadmap_item_description` / `SessionState.roadmap_item_level` から確認ポイントリストが生成される
- [ ] 各確認ポイントは `ConfirmationPoint` DTO（`id: str`, `content: str`, `format: "knowledge" | "knowledge_and_practice"`）で返る
- [ ] 通常系では、確認ポイント数は 3〜5 個を目標に生成される
- [ ] コードで表現できるポイントには `format="knowledge_and_practice"` が設定される
- [ ] `roadmap_item_level="middle"` または `roadmap_item_level="major"` のまとめテストでも、ノードが参照する入力は `SessionState.roadmap_item_title` / `SessionState.roadmap_item_description` / `SessionState.roadmap_item_level` のみである

## 異常系

- `QuestionSetDesignLlmClient` は注入境界であり、このfeatureでは concrete client の実装場所や直接テスト対象までは定義しない
- `QuestionSetDesignLlmClient` の公開契約は「`list[ConfirmationPoint]` を返す」または「`QuestionSetDesignError` を送出する」のいずれかとする
- LLM呼び出し失敗、および LLM応答が確認ポイントとして解釈できない場合（JSON パース失敗、スキーマ不整合）の分類責務は `QuestionSetDesignLlmClient` 側にある。これらは `QuestionSetDesignError` として正規化し、`error_code: str` と `message: str` を属性として持ち、`__cause__` に元例外を保持する
- `design_question_set` は raw JSON のパースやスキーマ判定を行わない。`QuestionSetDesignError` を受け取ったら自動再試行せず、`structlog` の構造化ログをちょうど1件出力して同じ例外を再送出する

| error_code | 発生条件 | message | ログイベント |
|---|---|---|---|
| `llm_request_failed` | LLM呼び出し自体が失敗 | `question set design llm request failed` | `question_set_design_failed` |
| `llm_response_parse_failed` | LLM応答のJSONパースまたはスキーマ検証に失敗 | `question set design llm response parse failed` | `question_set_design_failed` |

## モジュール構成

- 構成方針: 2ファイル構成（types + logic）
- モジュール一覧:
  - `backend/quiz/application/question_set_design_types.py`
    - `QuestionSetDesignError(Exception)` — `error_code: str`, `message: str` を属性として持つ
    - `QuestionSetDesignLlmClient(Protocol)` — `generate_confirmation_points(title: str, description: str, level: str) -> list[ConfirmationPoint]`。`ConfirmationPoint` は `SessionState.confirmation_points` と同じ DTO（`id`, `content`, `format`）を使う。正常時は DTO のリストを返し、LLM呼び出し失敗またはレスポンス解釈失敗時は `QuestionSetDesignError` を送出する。concrete client の配置先と直接テストはこのfeatureのスコープ外
  - `backend/quiz/application/question_set_design.py`
    - `design_question_set(state: SessionState, *, llm: QuestionSetDesignLlmClient) -> dict[str, object]` — LangGraphノード関数。SessionState から `roadmap_item_title` / `roadmap_item_description` / `roadmap_item_level` を読み、LLMで確認ポイントを生成し、`{"confirmation_points": list[ConfirmationPoint], "current_point_index": 0}` を返す
    - 確認ポイント数が3〜5個でない場合はログ警告するが、LLMの出力を尊重して続行する
    - `roadmap_item_level="middle"` または `roadmap_item_level="major"` の場合も、ノードが扱う入力は `roadmap_item_title` / `roadmap_item_description` / `roadmap_item_level` のみである
    - `QuestionSetDesignError` を受けた場合は `question_set_design_failed` を1件だけ記録して再送出する
