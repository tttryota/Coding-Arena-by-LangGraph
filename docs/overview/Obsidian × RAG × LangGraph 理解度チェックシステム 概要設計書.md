# Obsidian × RAG × LangGraph 理解度チェックシステム 概要設計書

**作成日：** 2026年4月29日

---

## 1. プロジェクト概要

### 1.1 目的と背景

本システムは、Obsidianに蓄積した学習ノートを知識ソースとして活用し、RAG（Retrieval-Augmented Generation）とLangGraphによるマルチエージェントワークフローを用いて、**自分の理解度を客観的に評価・可視化する個人学習支援システム**である。

転職活動における技術ポートフォリオとしての側面も持ち、「RAGシステムの設計・実装経験」「LangGraphによるマルチエージェント構成の設計経験」「FastAPI + Reactによるフルスタック実装経験」を一つのプロダクトで証明することを副次的な目的とする。

### 1.2 競合・類似事例との差別化

調査の結果、以下の類似プロジェクト・プラグインが既に存在する。

| 名称 | 概要 | 本システムとの差異 |
| :--- | :--- | :--- |
| [obsidian-quiz-generator](https://github.com/ECuiDev/obsidian-quiz-generator) | ObsidianプラグインとしてAIで問題生成 | Obsidian内で完結。外部GUIなし。エージェント構成なし |
| [obsidian-rag](https://github.com/ParthSareen/obsidian-rag) | LangChainでObsidianノートにRAG | チャット形式のみ。理解度評価・弱点可視化なし |
| LangGraph + Obsidian（個人ブログ事例） | エージェントがObsidianノートをタスク化 | 株式分析用途。学習評価への転用なし |

**本システムの差別化ポイントは3点ある。** 第一に、問題生成（Generator）と採点・フィードバック（Evaluator）を分離した二段階エージェント構成を採用する点。第二に、回答履歴から弱点ノートを自動タグ付けし、Obsidianのノートグラフに反映させる点。第三に、外部GUIから学習進捗をダッシュボード形式で確認できる点である。

---

## 2. システムアーキテクチャ

### 2.1 全体構成図

![システムアーキテクチャ図](https://private-us-east-1.manuscdn.com/sessionFile/l2HvFcxb1vDqc0GUIuI1rs/sandbox/tFj3NKqDS3UamBt8QpohVZ-images_1777449732234_na1fn_L2hvbWUvdWJ1bnR1L29ic2lkaWFuX3F1aXpfYXJjaGl0ZWN0dXJl.png?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9wcml2YXRlLXVzLWVhc3QtMS5tYW51c2Nkbi5jb20vc2Vzc2lvbkZpbGUvbDJIdkZjeGIxdkRxYzBHVUl1STFycy9zYW5kYm94L3RGajNOS3FEUzNVYW1CdDhRcG9oVlotaW1hZ2VzXzE3Nzc0NDk3MzIyMzRfbmExZm5fTDJodmJXVXZkV0oxYm5SMUwyOWljMmxrYVdGdVgzRjFhWHBmWVhKamFHbDBaV04wZFhKbC5wbmciLCJDb25kaXRpb24iOnsiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3OTg3NjE2MDB9fX1dfQ__&Key-Pair-Id=K2HSFNDJXOU9YS&Signature=GvhKHTF3ASiqAp3maxknNrLeEusr6uZ5IaUQERVrNxOIrRPLsxgW5xe0GLQ6dT-m5ltH4fKp2Jmo6v8B-aLpX8hL7GQERXAb9XqEOa1OH82EcBXY5~wKkifoU3f2eCs0Zx-I-C~C4t7aQW4MAtEJ7CTKn4SsKO4h6wGAKkr4DD87jjFS~sy1i-IKSLxtbrwQ12b3idP4SqiKgZQCbPtvD4X2GLZXAE-mqP6bx5ensVGSb5qk5MttHY5DiyxOd6Ucg~FPQZT6x23G9ydCi9Ha8EjdpLtfBaoTkag8bK-HywTWojdTUoqVFdpO9hUYD1acKGMsBmeyGXmwrP-wW~BOTQ__)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Obsidian Vault                           │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│   │ note_A.md│  │ note_B.md│  │ note_C.md│  │ _weakness.md │  │
│   └──────────┘  └──────────┘  └──────────┘  └──────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │ ファイル監視 (watchdog)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Ingestion Pipeline                          │
│  見出し単位チャンク分割 → Embedding生成 → ChromaDB（ローカル）  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LangGraph Agent Workflow                      │
│                                                                 │
│   ┌─────────────────┐         ┌─────────────────────────────┐  │
│   │  Generator Agent │         │      Evaluator Agent        │  │
│   │                 │         │                             │  │
│   │ RAGで関連ノート  │ ──────▶ │ 回答を採点し、フィードバック │  │
│   │ を検索し、問題を │         │ と弱点スコアを出力する      │  │
│   │ 生成する        │         │                             │  │
│   └─────────────────┘         └──────────────┬──────────────┘  │
│                                              │                  │
│                                              ▼                  │
│                               ┌─────────────────────────┐      │
│                               │  Weakness Tagger Agent  │      │
│                               │                         │      │
│                               │ 弱点ノートにタグを付与し │      │
│                               │ Obsidianに書き戻す      │      │
│                               └─────────────────────────┘      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                         │
│  /quiz/start  /quiz/answer  /progress  /weakness                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend GUI (React)                        │
│  問題表示 / 回答入力 / 進捗ダッシュボード / 弱点ノート一覧      │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 技術スタック

| レイヤー | 採用技術 | 選定理由 |
| :--- | :--- | :--- |
| ノート管理 | Obsidian（Markdown） | 既存の学習環境を活用。LangChainのObsidianLoaderで直接読み込み可能 |
| ファイル監視 | watchdog（Python） | ノート更新を検知してインデックスを自動再構築するため |
| チャンク分割 | LangChain `MarkdownHeaderTextSplitter` | 見出し（H1/H2/H3）単位の意味的分割。固定長分割より検索精度が高い |
| 埋め込みモデル | OpenAI `text-embedding-3-small` または `sentence-transformers/all-MiniLM-L6-v2`（ローカル） | コスト重視ならローカルモデル、精度重視ならOpenAI |
| ベクトルDB | ChromaDB（ローカル永続化） | ローカル動作・設定不要・LangChain統合が容易 |
| エージェントフレームワーク | LangGraph | ステートフルなマルチエージェントワークフローを有向グラフで定義できる |
| LLM | OpenAI GPT-4o-mini または Claude 3.5 Haiku | コストと精度のバランスが良い |
| バックエンドAPI | FastAPI（Python） | 非同期対応・型安全・自動ドキュメント生成 |
| フロントエンド | React + TypeScript + Vite | 既存スキルの活用 |
| 状態管理 | Jotai | 既存スキルの活用（モバイルでの経験あり） |
| UIコンポーネント | Chakra UI | 既存スキルの活用（セマンティックトークン設計経験あり） |

---

## 3. コアコンポーネントの詳細設計

### 3.1 Ingestion Pipeline（知識の取り込み）

ObsidianのVaultディレクトリをwatchdogで監視し、Markdownファイルの追加・更新を検知した際に自動でインデックスを再構築する。

**チャンク分割の設計判断**が本システムの技術的な核心の一つである。一般的なRAGシステムでは固定長（例：500トークン）でテキストを分割するが、本システムでは`MarkdownHeaderTextSplitter`を用いて見出し単位で分割する。これにより、「Djangoのクエリセット最適化」という見出しのチャンクには、その見出し以下のすべての内容が含まれ、意味的な文脈が保持される。

```python
from langchain.text_splitter import MarkdownHeaderTextSplitter

headers_to_split_on = [
    ("#", "H1"),
    ("##", "H2"),
    ("###", "H3"),
]
splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
```

チャンクのメタデータには、元のファイルパス・見出し階層・最終更新日時を付与する。これにより、問題生成時に「どのノートから出題されたか」を追跡できる。

### 3.2 LangGraphエージェントワークフロー

本システムの最大の技術的特徴は、**Generator・Evaluator・Weakness Taggerの3エージェントを有向グラフで接続したワークフロー**である。

#### ステート定義

```python
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph

class QuizState(TypedDict):
    topic: str                    # 出題トピック（ユーザー指定）
    retrieved_chunks: List[str]   # RAGで取得したチャンク
    question: str                 # 生成された問題
    user_answer: str              # ユーザーの回答
    score: int                    # 採点結果（0〜100）
    feedback: str                 # フィードバックコメント
    weakness_tags: List[str]      # 弱点として記録するタグ
    source_note_path: str         # 出題元ノートのパス
```

#### Generator Agent

RAGでChromaDBから関連チャンクを検索し、そのチャンクのみを文脈として問題を生成する。**重要な設計判断として、LLM自身の学習データに頼らず、必ずRAGで取得したチャンクのみを根拠として問題を生成するようにシステムプロンプトで制約する。** これにより、ノートに書いていない知識は出題されないという保証が得られる。

```python
GENERATOR_SYSTEM_PROMPT = """
あなたは学習支援AIです。
以下の【参考資料】のみを根拠として、理解度を確認する問題を1問生成してください。
参考資料に記載のない知識を問う問題は絶対に生成しないでください。

問題形式：記述式（200字以内で回答できる難易度）
出力形式：JSON {{ "question": "...", "key_points": ["...", "..."] }}
"""
```

#### Evaluator Agent

ユーザーの回答と、Generatorが保持する`key_points`（採点基準）を照合し、0〜100点のスコアとフィードバックを出力する。**採点はLLMに委ねるが、採点基準（key_points）はGeneratorが生成した構造化データを使用することで、評価の一貫性を担保する。**

#### Weakness Tagger Agent

スコアが閾値（例：60点）を下回った場合にのみ起動する条件分岐をLangGraphのエッジで表現する。弱点と判定されたノートのパスに`#weakness`タグをObsidianのフロントマターに書き込む。

```python
def should_tag_weakness(state: QuizState) -> str:
    """LangGraphの条件分岐ノード"""
    if state["score"] < 60:
        return "weakness_tagger"
    return "end"
```

### 3.3 チャンク分割の精度チューニング

RAGシステムの品質は、チャンク分割の設計と埋め込みモデルの選択に大きく依存する。本システムでは以下の2軸で精度を評価・改善するサイクルを設ける。

| 評価指標 | 測定方法 |
| :--- | :--- |
| **検索精度（Recall@K）** | 「このトピックについて質問したとき、正しいチャンクがTop-K件に含まれるか」を手動で評価 |
| **問題品質スコア** | 生成された問題を「ノートの内容を正確に反映しているか」「難易度は適切か」の2軸で主観評価 |

---

## 4. フロントエンドGUI設計

### 4.1 画面構成

| 画面 | 機能 |
| :--- | :--- |
| **ホーム / ダッシュボード** | 累計出題数・平均スコア・弱点タグ数の可視化（recharts使用） |
| **クイズ画面** | トピック選択 → 問題表示 → 回答入力 → 採点・フィードバック表示 |
| **弱点ノート一覧** | `#weakness`タグが付いたノートの一覧。クリックでObsidianを直接開く（`obsidian://open`プロトコル） |
| **進捗履歴** | 日付別のスコア推移グラフ |

### 4.2 Obsidianとの連携

フロントエンドから`obsidian://open?vault=MyVault&file=note_A`のURIスキームを呼び出すことで、弱点ノートをObsidianで直接開く動線を実現する。これにより、「弱点の発見 → Obsidianでノートを復習 → 再度クイズに挑戦」というフィードバックループが完成する。

---

## 5. 開発ロードマップ

### Phase 1（2週間）：RAGパイプラインの構築と検証

まず、エージェントなしでRAGの精度を検証することを最優先とする。Obsidianのノートを読み込み、ChromaDBにインデックスを構築し、任意のクエリで関連チャンクが正しく取得できるかを確認する。**この段階で「見出し単位の意味的分割」と「固定長分割」の検索精度を比較し、その結果をREADMEに記録する。** これが「設計の意思決定を語れるエンジニア」の証明になる。

### Phase 2（2週間）：LangGraphエージェントの実装

Generator → Evaluatorの二段構成を実装する。この段階ではフロントエンドは不要で、Jupyter Notebookまたはコマンドラインで動作確認する。LangGraphのステートグラフの可視化機能（`graph.get_graph().draw_mermaid()`）を使い、ワークフロー図をREADMEに掲載する。

### Phase 3（1週間）：FastAPI + React GUIの実装

Phase 2までで動作が確認できたエージェントワークフローをFastAPIでAPIとして公開し、ReactのGUIから呼び出す。既存のスキル（React・TypeScript・Chakra UI・Jotai）をそのまま活用できるため、工数は最小限に抑えられる。

### Phase 4（1週間）：Weakness Taggerの実装と精度チューニング

条件分岐エッジとWeakness Taggerを追加し、弱点タグのObsidian書き戻しを実装する。合わせて、チャンク分割の精度評価結果をドキュメントに記録する。

---

## 6. 面接でのアピール戦略

本システムを面接でアピールする際、**「何を作ったか」ではなく「なぜその設計にしたか」を語ることが最重要である。**

以下の問いに対して、自分の言葉で答えられる状態にしておくこと。

| 想定質問 | 準備すべき回答の核心 |
| :--- | :--- |
| なぜ既存のObsidianプラグインを使わなかったのか | RAGとエージェント設計を実装レベルで理解するためであり、プラグインは「使う側」にとどまるため |
| なぜ固定長分割ではなく見出し単位の分割にしたのか | Obsidianのノートは見出しで意味的に区切られており、固定長分割では文脈が失われる。実際に比較評価した結果を数値で示せる |
| なぜGeneratorとEvaluatorを分離したのか | 単一エージェントでは「問題を作った自分が採点する」という自己参照の問題が生じ、採点の客観性が担保できないため |
| RAGの限界はどこか | ノートに書いていない知識は問えない。また、ノートの記述が曖昧な場合、問題の品質も下がる。この限界を認識した上で、ノートの記述品質を上げるというフィードバックループが副次的な学習効果をもたらす |

---

## 7. 批判的リスク評価

本プロジェクトを開始する前に、以下のリスクを認識しておくこと。

**リスク1：「Obsidianプラグインで十分では？」という問いへの回答準備不足**
既に`obsidian-quiz-generator`というプラグインが存在する。「なぜ自作したのか」という問いに答えられない場合、面接での評価はゼロどころかマイナスになる。**必ず「設計の意思決定の記録」をREADMEに書くこと。**

**リスク2：完成させずに途中で止まるリスク**
Phase 1のRAGパイプラインだけでも、GitHubに公開して「設計の意思決定を語れる状態」にすれば価値がある。完璧なシステムを作ることより、**「なぜこの設計にしたか」を語れる状態にすること**を最優先とする。

**リスク3：ファインチューニングへの誘惑**
本システムの範囲内でファインチューニングを試みることは推奨しない。理由は、ファインチューニングの効果を評価するには適切なベンチマークデータセットの準備が必要であり、工数が膨大になるためである。RAGとエージェント設計の完成度を高めることに集中すること。
