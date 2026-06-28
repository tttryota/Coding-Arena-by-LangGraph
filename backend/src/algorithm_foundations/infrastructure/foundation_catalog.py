"""競プロうさぎの静的カタログ生成。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from algorithm_foundations.domain.foundation_types import (
    AlgorithmFoundationCatalogError,
    AlgorithmFoundationCatalogResponse,
    AlgorithmFoundationExample,
    AlgorithmFoundationGroupSummary,
    AlgorithmFoundationProblem,
    AlgorithmFoundationRubricItem,
    AlgorithmFoundationUnit,
    AlgorithmFoundationUnitBank,
    AlgorithmFoundationUnitSummary,
)
from algorithm_foundations.infrastructure.foundation_banks import (
    UNIT_BANK_REGISTRY as _UNIT_BANK_REGISTRY,
)
from algorithm_foundations.infrastructure.foundation_units import (
    SPECIAL_THEME_UNITS as _SPECIAL_THEME_UNITS,
)

_GROUP_ORDER: Final[dict[str, int]] = {
    "データ構造": 0,
    "探索": 1,
    "ソート": 2,
    "数学": 3,
    "動的計画法": 4,
    "グラフ": 5,
    "文字列": 6,
    "貪欲法": 7,
    "ビット演算": 8,
    "分割統治": 9,
    "幾何": 10,
    "フロー・マッチング": 11,
}

_GROUP_DISPLAY_TITLE: Final[dict[str, str]] = {
    "データ構造": "データ構造",
    "探索": "探索",
    "ソート": "ソート",
    "数学": "数え上げ・整数・確率",
    "動的計画法": "動的計画法",
    "グラフ": "グラフ",
    "文字列": "文字列処理",
    "貪欲法": "その場で決めるアルゴリズム",
    "ビット演算": "ビット演算",
    "分割統治": "分けて解くアルゴリズム",
    "幾何": "図形・座標",
    "フロー・マッチング": "最大流・マッチング",
}

_DEFAULT_THEME_PATHS: Final[tuple[Path, ...]] = (
    Path("data/algo_themes.json"),
    Path("/opt/fixtures/algo_themes.json"),
    Path(__file__).resolve().parents[3] / "data" / "algo_themes.json",
)

_IMPORTANT_THEME_IDS: Final[tuple[str, ...]] = (
    "algo-002",
    "algo-004",
    "algo-005",
    "algo-022",
    "algo-028",
    "algo-036",
    "algo-037",
    "algo-044",
    "algo-079",
    "algo-081",
    "algo-093",
    "algo-096",
    "algo-098",
    "algo-099",
    "algo-102",
    "algo-104",
)

_EXPECTED_MULTI_PROBLEM_COUNTS: Final[dict[str, int]] = {
    "algo-093-stack-basics": 5,
    "algo-093-stack-brackets": 6,
    "algo-093-stack-cancel": 3,
    "algo-094-queue-basics": 3,
    "algo-094-deque-basics": 3,
    "algo-099-prefix-sum-1d": 6,
    "algo-099-prefix-sum-range": 4,
    "algo-099-prefix-sum-2d": 3,
    "algo-102-hashmap-exists": 6,
    "algo-102-hashmap-duplicate": 6,
    "algo-102-hashmap-count": 3,
    "algo-102-hashmap-index": 3,
    "algo-102-hashmap-match": 3,
    "algo-025-practice": 2,
    "algo-095-practice": 2,
    "algo-103-practice": 2,
    "algo-107-practice": 2,
    "algo-111-practice": 2,
}

@dataclass(frozen=True)
class _Theme:
    id: str
    category: str
    label: str
    display_order: int


class AlgorithmFoundationCatalog:
    """既存 algo_themes を元に、静的な学習 unit 群を生成する。"""

    def __init__(self, themes_path: str | Path = "data/algo_themes.json") -> None:
        self._path = Path(themes_path)
        self._themes = self._load_themes()
        self._units = self._build_units()
        self._validate_units()
        self._unit_map = {unit["unit_id"]: unit for unit in self._units}

    def list_catalog(
        self,
        *,
        best_scores: dict[str, int | None] | None = None,
        last_attempted_at: dict[str, str | None] | None = None,
        started_problem_counts: dict[str, int] | None = None,
    ) -> AlgorithmFoundationCatalogResponse:
        best_scores = best_scores or {}
        last_attempted_at = last_attempted_at or {}
        started_problem_counts = started_problem_counts or {}
        recommended_id = self.pick_recommended_unit_id(best_scores)
        groups: dict[str, AlgorithmFoundationGroupSummary] = {}
        for unit in self._units:
            group = groups.setdefault(
                unit["group_id"],
                {
                    "group_id": unit["group_id"],
                    "group_title": unit["group_title"],
                    "order": int(str(unit["group_id"]).removeprefix("group-")),
                    "units": [],
                },
            )
            summary: AlgorithmFoundationUnitSummary = {
                "unit_id": unit["unit_id"],
                "theme_id": unit["theme_id"],
                "title": unit["title"],
                "display_order": unit["display_order"],
                "prerequisite_unit_ids": unit["prerequisite_unit_ids"],
                "prerequisite_titles": unit["prerequisite_titles"],
                "target_skill": unit["target_skill"],
                "unit_kind": unit["unit_kind"],
                "problem_count": len(unit["problem_bank"]),
                "started_problem_count": started_problem_counts.get(unit["unit_id"], 0),
                "best_score": best_scores.get(unit["unit_id"]),
                "last_attempted_at": last_attempted_at.get(unit["unit_id"]),
                "recommended": unit["unit_id"] == recommended_id,
                "has_unmet_prerequisites": self._has_unmet_prerequisites(
                    unit["prerequisite_unit_ids"],
                    best_scores,
                ),
            }
            group["units"].append(summary)

        ordered_groups = sorted(
            groups.values(),
            key=lambda item: item["order"],
        )
        return {
            "total_unit_count": len(self._units),
            "total_problem_count": sum(len(unit["problem_bank"]) for unit in self._units),
            "groups": ordered_groups,
        }

    def get_unit(self, unit_id: str) -> AlgorithmFoundationUnit:
        try:
            return self._unit_map[unit_id]
        except KeyError as exc:
            raise AlgorithmFoundationCatalogError(
                error_code="unit_not_found",
                message=f"Algorithm foundation unit not found: {unit_id}",
            ) from exc

    def pick_recommended_unit_id(self, best_scores: dict[str, int | None]) -> str:
        for unit in self._units:
            score = best_scores.get(unit["unit_id"])
            if score is None or score < 80:
                return unit["unit_id"]
        return self._units[0]["unit_id"]

    def pick_problem(
        self,
        unit_id: str,
        recent_problem_ids: list[str],
    ) -> AlgorithmFoundationProblem:
        unit = self.get_unit(unit_id)
        seen = set(recent_problem_ids)
        for problem in unit["problem_bank"]:
            if problem["problem_id"] not in seen:
                return problem
        if not recent_problem_ids:
            return unit["problem_bank"][0]
        problem_ids = [problem["problem_id"] for problem in unit["problem_bank"]]
        try:
            latest_index = problem_ids.index(recent_problem_ids[0])
        except ValueError:
            return unit["problem_bank"][0]
        return unit["problem_bank"][(latest_index + 1) % len(unit["problem_bank"])]

    def get_problem(
        self,
        unit_id: str,
        problem_id: str,
    ) -> AlgorithmFoundationProblem:
        unit = self.get_unit(unit_id)
        for problem in unit["problem_bank"]:
            if problem["problem_id"] == problem_id:
                return problem
        raise AlgorithmFoundationCatalogError(
            error_code="problem_not_found",
            message=f"Algorithm foundation problem not found: {problem_id}",
        )

    def counts(self) -> tuple[int, int]:
        return len(self._units), sum(len(unit["problem_bank"]) for unit in self._units)

    def _load_themes(self) -> list[_Theme]:
        path = next((candidate for candidate in self._candidate_theme_paths() if candidate.exists()), None)
        if path is None:
            msg = f"algo theme file not found: {self._path}"
            raise AlgorithmFoundationCatalogError(
                error_code="theme_file_not_found",
                message=msg,
            )
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [
            _Theme(
                id=str(item["id"]),
                category=str(item["category"]),
                label=str(item["label"]),
                display_order=int(item["display_order"]),
            )
            for item in raw
        ]

    def _candidate_theme_paths(self) -> tuple[Path, ...]:
        return (self._path, *(candidate for candidate in _DEFAULT_THEME_PATHS if candidate != self._path))

    def _build_units(self) -> list[AlgorithmFoundationUnit]:
        ordered_themes = sorted(self._themes, key=lambda item: item.display_order)
        default_total = len(ordered_themes) * 2
        extra_needed = 320 - default_total - self._special_extra_count()
        candidates = [
            theme.id
            for theme in ordered_themes
            if theme.id not in _SPECIAL_THEME_UNITS
        ]
        expanded_ids = set(candidates[:extra_needed])
        units: list[AlgorithmFoundationUnit] = []
        last_unit_by_theme: dict[str, list[str]] = {}
        for index, theme in enumerate(ordered_themes):
            group_id = f"group-{_GROUP_ORDER.get(theme.category, index)}"
            definitions = self._unit_definitions(theme, theme.id in expanded_ids)
            theme_unit_ids: list[str] = []
            for local_index, (suffix, title, unit_kind) in enumerate(definitions):
                unit_id = f"{theme.id}-{suffix}"
                previous_ids = theme_unit_ids[-2:] if unit_kind == "integration" else theme_unit_ids[-1:]
                prerequisite_titles = [
                    self._unit_map_title(units, pid)
                    for pid in previous_ids
                ]
                unit = self._build_unit(
                    theme=theme,
                    group_id=group_id,
                    title=title,
                    unit_id=unit_id,
                    unit_kind=unit_kind,
                    prerequisite_unit_ids=previous_ids,
                    prerequisite_titles=prerequisite_titles,
                    display_order=(index * 10) + local_index,
                )
                units.append(unit)
                theme_unit_ids.append(unit_id)
            last_unit_by_theme[theme.id] = theme_unit_ids
        return units

    def _unit_definitions(
        self,
        theme: _Theme,
        expanded: bool,
    ) -> list[tuple[str, str, str]]:
        if theme.id in _SPECIAL_THEME_UNITS:
            return _SPECIAL_THEME_UNITS[theme.id]
        if theme.id == "algo-127":
            return [
                ("basic", "割当問題（部分集合DP） の基本", "foundation"),
                ("practice", "割当問題（部分集合DP） を素直に実装する", "foundation"),
            ]
        if theme.id == "algo-051":
            return [
                ("basic", "活動どうしが両立する条件 の基本", "foundation"),
                ("practice", "参加計画が実行できるかを順に確かめる", "foundation"),
                ("integration", "休憩時間つきの参加計画を検査する", "integration"),
            ]
        if theme.id == "algo-080":
            return [
                ("basic", "素数判定・試し割り の基本", "foundation"),
                ("practice", "素数判定・試し割り を複数回の判定に使う", "foundation"),
                ("integration", "素数判定・試し割り の活用", "integration"),
            ]
        if theme.id == "algo-082":
            return [
                ("basic", "素因数分解 の基本", "foundation"),
                ("practice", "素因数分解 から種類数を読む", "foundation"),
                ("integration", "素因数分解 の総合演習", "integration"),
            ]
        if theme.id == "algo-090":
            return [
                ("basic", "約数列挙 の基本", "foundation"),
                ("practice", "約数列挙 で条件に合うものを抜き出す", "foundation"),
                ("integration", "約数列挙 の総合演習", "integration"),
            ]
        if theme.id == "algo-129":
            return [
                ("basic", "重み付き二部マッチング（部分集合DP） の基本", "foundation"),
                ("practice", "重み付き二部マッチング（部分集合DP） を素直に実装する", "foundation"),
            ]
        defs: list[tuple[str, str, str]] = [
            ("basic", f"{theme.label} の基本", "foundation"),
            ("practice", f"{theme.label} を素直に実装する", "foundation"),
        ]
        if expanded:
            defs.append(("integration", f"{theme.label} の総合演習", "integration"))
        return defs

    def _build_unit(  # noqa: PLR0913
        self,
        *,
        theme: _Theme,
        group_id: str,
        title: str,
        unit_id: str,
        unit_kind: str,
        prerequisite_unit_ids: list[str],
        prerequisite_titles: list[str],
        display_order: int,
    ) -> AlgorithmFoundationUnit:
        allowed = [title, theme.label]
        if unit_kind == "integration":
            allowed.extend(prerequisite_titles)
        forbidden = self._forbidden_knowledge(theme, title)
        unit_bank = self._get_unit_bank(unit_id)
        if unit_bank["title"] != title:
            raise AlgorithmFoundationCatalogError(
                error_code="unit_title_mismatch",
                message=f"Static unit bank title mismatch for {unit_id}: {unit_bank['title']} != {title}",
            )
        if unit_bank["unit_kind"] != unit_kind:
            raise AlgorithmFoundationCatalogError(
                error_code="unit_kind_mismatch",
                message=f"Static unit bank kind mismatch for {unit_id}: {unit_bank['unit_kind']} != {unit_kind}",
            )
        concept_overview = unit_bank["concept_overview"]
        problem_bank = self._decorate_problem_bank(
            theme=theme,
            unit_title=title,
            concept_overview=concept_overview,
            problem_bank=unit_bank["problem_bank"],
        )
        return {
            "unit_id": unit_id,
            "theme_id": theme.id,
            "group_id": group_id,
            "group_title": _GROUP_DISPLAY_TITLE.get(theme.category, theme.category),
            "title": title,
            "concept_overview": concept_overview,
            "display_order": display_order,
            "prerequisite_unit_ids": prerequisite_unit_ids,
            "prerequisite_titles": prerequisite_titles,
            "allowed_knowledge": allowed,
            "forbidden_knowledge": forbidden,
            "target_skill": unit_bank["target_skill"],
            "unit_kind": unit_kind,
            "problem_bank": problem_bank,
        }

    def _decorate_problem_bank(
        self,
        *,
        theme: _Theme,
        unit_title: str,
        concept_overview: str,
        problem_bank: list[AlgorithmFoundationProblem],
    ) -> list[AlgorithmFoundationProblem]:
        prefix = (
            f"{concept_overview}\n\n"
            f"- カテゴリ: {theme.category}\n"
            f"- 学習単位: {unit_title}\n\n"
        )
        decorated: list[AlgorithmFoundationProblem] = []
        for problem in problem_bank:
            statement = problem["problem_statement"]
            if not statement.startswith(prefix):
                statement = prefix + statement
            decorated.append(
                {
                    **problem,
                    "problem_statement": statement,
                },
            )
        return decorated

    def _get_unit_bank(self, unit_id: str) -> AlgorithmFoundationUnitBank:
        try:
            return _UNIT_BANK_REGISTRY[unit_id]
        except KeyError as exc:
            raise AlgorithmFoundationCatalogError(
                error_code="unit_bank_not_found",
                message=f"Static unit bank not found for {unit_id}",
            ) from exc

    def _concept_overview(  # noqa: PLR0913
        self,
        *,
        theme: _Theme,
        unit_id: str,
        title: str,
        unit_kind: str,
        prerequisite_titles: list[str],
    ) -> str:
        del unit_id
        base_title = title
        for suffix in (" の基本", " を素直に実装する", " の総合演習"):
            if base_title.endswith(suffix):
                base_title = base_title.removesuffix(suffix)
                break

        concept = theme.label if theme.label in title else base_title
        explanation = self._concept_overview_for_concept(concept, category=theme.category)
        if unit_kind == "integration" and prerequisite_titles:
            joined = " と ".join(prerequisite_titles[:2])
            return f"{explanation} この unit では、既習の {joined} を順に使いながら、1 問を分けて解く流れまで確認します。"
        return explanation

    def _concept_overview_for_concept(self, concept: str, *, category: str) -> str:  # noqa: C901, PLR0915
        key = concept
        if "bit全探索" in key:
            return "bit 全探索は、各要素を選ぶ・選ばないをビットで表し、部分集合を全部試す解き方です。整数のビット表現と集合の対応づけを使えるようにします。"
        if "順列全探索" in key:
            return "順列全探索は、並べ方をすべて試し、その中から条件を満たすものを見つける解き方です。候補を生成して順に評価する流れを押さえます。"
        if "半分全列挙" in key:
            return "半分全列挙は、候補を前半と後半に分けて列挙し、あとで組み合わせて全体の答えを作る考え方です。全部試したいがそのままでは多すぎるときの基本形を学びます。"
        if "全探索" in key or "ブルートフォース" in key:
            return "全探索（ブルートフォース）は、ありえる候補を順番に全部試し、条件を満たすものを見つける解き方です。まずは漏れなく列挙し、1 つずつ判定する形を身につけます。"
        if "二分探索" in key:
            return "二分探索は、条件を満たす境目や値を、探索範囲を半分ずつ絞りながら見つける解き方です。単調性を見つけて mid で判定する流れを身につけます。"
        if "三分探索" in key:
            return "三分探索は、値が山型や谷型に変化するとき、比較する位置を 3 分するように動かして最適値に近づく解き方です。関数の形に注目して範囲を狭める感覚を学びます。"
        if "尺取り法" in key:
            return "尺取り法は、左右の端を動かしながら連続区間を保ち、条件を満たす最短・最長・個数を求める考え方です。区間を伸ばすときと縮めるときの役割分担を押さえます。"
        if "深さ優先探索" in key or "DFS" in key:
            return "深さ優先探索は、行けるところまで進んでから戻る形で状態や頂点をたどる解き方です。再帰やスタックで探索順を管理する基本を学びます。"
        if "幅優先探索" in key or "BFS" in key:
            return "幅優先探索は、近い状態から順に広げていく解き方です。キューを使って層ごとに進むことで、最短手数や到達可否を素直に求めます。"
        if "スタック" in key:
            return "スタックは、最後に入れたものを先に取り出す考え方です。直前の状態や未処理の情報をあとから回収したい場面で使います。"
        if "キュー" in key:
            return "キューは、先に入れたものを先に取り出す考え方です。到着順の処理や、近い順に広げる探索で基本になります。"
        if "デック" in key:
            return "デックは、前後どちらの端からも追加・削除できる考え方です。両端を使い分けながら状態を保つ場面で使います。"
        if "累積和" in key:
            return "累積和は、左上や左から順に合計をためておき、あとで区間や長方形の和を差で取り出す考え方です。前計算して問い合わせを軽くする基本形を学びます。"
        if "いもす" in key:
            return "いもす法は、区間への加算を差分として記録し、最後に累積して各位置の値を復元する考え方です。更新をまとめて遅延処理する形を押さえます。"
        if "ハッシュ" in key:
            return "ハッシュは、値をキーにして必要な情報へすぐたどる考え方です。『探す』を『表から引く』に置き換えて、判定や数え上げを高速化します。"
        if "Union-Find" in key:
            return "Union-Find は、要素どうしが同じグループかを管理し、グループをくっつける操作を高速に行う考え方です。連結性をまとめて扱う基本を学びます。"
        if "ダイクストラ" in key:
            return "ダイクストラ法は、重みが負でないグラフで、いちばん近い頂点から順に最短距離を確定していく解き方です。優先度付きキューを使う最短路の基本形です。"
        if "ベルマンフォード" in key:
            return "ベルマンフォード法は、辺の緩和を繰り返して最短距離を更新する解き方です。負辺がある場合や負閉路の検出まで扱える基本を学びます。"
        if "ワーシャルフロイド" in key:
            return "ワーシャルフロイド法は、『この頂点を経由してよいか』を順に増やしながら、全点対間の最短距離を更新する解き方です。表を段階的に改善する形を押さえます。"
        if "最小全域木" in key or "プリム" in key or "クラスカル" in key:
            return "最小全域木は、全頂点をつなぎつつ重み合計を最小にする辺集合を作る考え方です。どの辺を採用すると無駄なくつながるかを順に決める基本を学びます。"
        if "トポロジカル" in key:
            return "トポロジカルソートは、依存関係を壊さない順番に頂点を並べる考え方です。『先に済ませるべきもの』を整理して順序を作る基本を学びます。"
        if "最小共通祖先" in key or "LCA" in key:
            return "最小共通祖先は、木の 2 頂点に対して共通の祖先のうち最も深いものを求める考え方です。木の親子関係を前計算して質問に素早く答える形を学びます。"
        if "強連結成分" in key or "SCC" in key:
            return "強連結成分分解は、互いに行き来できる頂点どうしをひとかたまりにまとめる考え方です。グラフを縮約して構造を見やすくする基本を学びます。"
        if "二部グラフ" in key:
            return "二部グラフ判定は、頂点を 2 色に分け、隣り合う頂点が同じ色にならないかを見る考え方です。制約を色分けとして扱う基本形を押さえます。"
        if "トーシェント" in key or "phi(" in key or "φ" in key:
            return "オイラーのトーシェント関数は、1 以上 N 以下で N と互いに素な整数の個数を数える知識です。素因数分解して掛け算の形に直す基本を学びます。"
        if "オイラー" in key:
            return "オイラー路・オイラー閉路は、辺をちょうど 1 回ずつ通る道が作れるかを考える知識です。次数や通り方の条件を整理する基本を学びます。"
        if "座標圧縮" in key:
            return "座標圧縮は、大小関係を保ったまま値を小さい番号に置き換える考え方です。広い値域を扱いやすい添字に直す基本を学びます。"
        if "転倒数" in key:
            return "転倒数は、順序が逆になっている組の個数を数える知識です。『何個後ろに小さいものがあるか』を効率よく数える形を学びます。"
        if "Fenwick木" in key or "BIT/Fenwick木" in key or "Binary Indexed Tree" in key:
            return "Binary Indexed Tree（BIT/Fenwick木）は、配列の値を少しずつまとめて持ち、更新しながら区間和を素早く求める知識です。1 点更新と累積和の対応を使う基本を学びます。"
        if "遅延評価セグメント木" in key:
            return "遅延評価セグメント木は、区間更新の情報を今すぐ全部配らずに持っておき、必要になったときだけ反映する知識です。広い区間への更新と問い合わせを両立する基本を学びます。"
        if "セグメント木" in key:
            return "セグメント木は、区間を二分しながら情報を木に持たせ、更新と区間問い合わせを素早く行う知識です。部分区間の答えを合体して全体の答えを作る基本を学びます。"
        if "スパーステーブル" in key or "RMQ" in key:
            return "スパーステーブルは、動かない配列に対して区間最小値などを何度も聞かれるときに、前計算で問い合わせを速くする知識です。『更新なし・問い合わせ多数』の形を見抜く基本を学びます。"
        if "素数" in key or "エラトステネス" in key:
            return "素数判定やふるいは、数の割り切れ方を使って素数を見分けたり列挙したりする知識です。約数の性質を利用する基本を押さえます。"
        if "最大公約数" in key or "最小公倍数" in key or "GCD" in key or "LCM" in key:
            return "最大公約数・最小公倍数は、整数の割り切れ方を使って共通する周期やまとまりを扱う知識です。互除法と関係式を使う基本を学びます。"
        if "mod" in key or "剰余" in key:
            return "剰余は、値をある法で割ったあまりとして扱い、巨大な数でも性質を保ったまま計算する考え方です。足し算・掛け算・逆元の基本を押さえます。"
        if "組み合わせ" in key or "二項係数" in key:
            return "組み合わせは、順序を区別せずに選ぶ方法の数を数える知識です。場合分けではなく公式や前計算で数える基本を学びます。"
        if "確率" in key or "期待値" in key:
            return "確率・期待値は、各結果がどれだけ起こりやすいかを数で扱い、平均的な値を求める知識です。場合の数と重みづけを整理する基本を押さえます。"
        if "ローリングハッシュ" in key:
            return "ローリングハッシュは、文字列の一部分を数として持ち回り、部分文字列どうしを素早く比較する考え方です。再計算せずに比較する基本を学びます。"
        if "KMP" in key or "Z-algorithm" in key:
            return "文字列検索アルゴリズムは、一致しなかった場所の情報を使い回し、比較を最初からやり直さない考え方です。文字列の自己一致を利用する基本を学びます。"
        if "Suffix Array" in key or "LCP" in key:
            return "Suffix Array や LCP は、文字列の suffix を順序づけて管理し、部分文字列の比較や共通部分を扱いやすくする知識です。並べ替えた構造で文字列を見る基本を学びます。"
        if "Trie" in key:
            return "Trie は、文字列を文字ごとの木として共有しながら保存する考え方です。接頭辞が共通する語をまとめて扱う基本を学びます。"
        if category == "動的計画法" or "DP" in key:
            return "動的計画法は、小さい状態の答えを先に求め、その結果を使って大きい状態の答えを作る考え方です。状態・遷移・初期値を整理する基本を身につけます。"
        if "ソート" in key or category == "ソート":
            return "ソートは、要素を決まった順番に並べ替える知識です。比較や交換をどう進めると目的の順序になるかを手順として理解します。"
        if "文字列" in key or category == "文字列":
            return "文字列処理は、文字の並びを比較したり、部分文字列を見つけたり、規則性を前計算で利用したりする知識です。並びをそのまま走査して構造をつかむ基本を学びます。"
        if category == "貪欲法" or "貪欲" in key:
            return "貪欲法は、その時点で最もよさそうな選択を順に確定していく考え方です。後戻りせずに決めてよい条件を見抜く基本を学びます。"
        if category == "ビット演算" or "bit" in key.lower() or "XOR" in key or "OR" in key or "AND" in key:
            return "ビット演算は、整数を 2 進数として見て、立っている桁の有無で状態や条件を扱う知識です。集合や状態をコンパクトに表す基本を学びます。"
        if category == "分割統治":
            return "分割統治は、問題を小さく分けて解き、その結果を合体して元の問題の答えを作る考え方です。分け方と戻し方を整理する基本を学びます。"
        if category == "幾何":
            return "図形・座標の問題は、点や線の位置関係を式に直し、距離・面積・向きなどを使って判定する知識です。図を数式として扱う基本を学びます。"
        if category == "フロー・マッチング" or "最大流" in key or "マッチング" in key:
            return "最大流・マッチングは、通せる量や組み合わせをグラフの辺として表し、制約つきでどれだけ流せるか・結べるかを考える知識です。問題をネットワークに置き換える基本を学びます。"
        return f"{concept}は、入力の構造や候補を整理し、決まった手順で答えを作る知識です。まずは典型の使い方を自分の手で追える状態を目指します。"


    def _forbidden_knowledge(self, theme: _Theme, title: str) -> list[str]:
        common = ["未学習の別テクニック", "テーマ外の発想ジャンプ"]
        if theme.id == "algo-102":
            return [*common, "尺取り法", "二分探索", "累積和", "グラフ探索"]
        if theme.id == "algo-094":
            return [*common, "0-1 BFS", "単調デック", "ダイクストラ法"]
        if "累積和" in title:
            return [*common, "二分探索", "尺取り法", "セグメント木"]
        return common

    def _has_unmet_prerequisites(
        self,
        prerequisite_unit_ids: list[str],
        best_scores: dict[str, int | None],
    ) -> bool:
        return any((best_scores.get(unit_id) or 0) < 80 for unit_id in prerequisite_unit_ids)

    def _validate_units(self) -> None:  # noqa: C901, PLR0915
        unit_ids = [unit["unit_id"] for unit in self._units]
        if len(unit_ids) != len(set(unit_ids)):
            raise AlgorithmFoundationCatalogError(
                error_code="duplicate_unit_id",
                message="algorithm foundations catalog contains duplicate unit_id",
            )
        if len(_UNIT_BANK_REGISTRY) != len(self._units):
            raise AlgorithmFoundationCatalogError(
                error_code="unit_bank_count_mismatch",
                message=(
                    "static unit bank registry size does not match built units: "
                    f"{len(_UNIT_BANK_REGISTRY)} != {len(self._units)}"
                ),
            )
        problem_ids: set[str] = set()
        for unit in self._units:
            if not unit["problem_bank"]:
                raise AlgorithmFoundationCatalogError(
                    error_code="empty_problem_bank",
                    message=f"unit {unit['unit_id']} must contain at least one problem",
                )
            expected_problem_count = _EXPECTED_MULTI_PROBLEM_COUNTS.get(unit["unit_id"], 1)
            if len(unit["problem_bank"]) != expected_problem_count:
                raise AlgorithmFoundationCatalogError(
                    error_code="problem_bank_size_mismatch",
                    message=(
                        f"unit {unit['unit_id']} must contain exactly "
                        f"{expected_problem_count} problems"
                    ),
                )
            seen_payloads: set[tuple[str, str, str, str, str]] = set()
            for index, problem in enumerate(unit["problem_bank"], start=1):
                expected_problem_id = f"{unit['unit_id']}-p{index}"
                if problem["problem_id"] != expected_problem_id:
                    raise AlgorithmFoundationCatalogError(
                        error_code="problem_id_sequence_mismatch",
                        message=(
                            f"unit {unit['unit_id']} expected problem_id "
                            f"{expected_problem_id} but got {problem['problem_id']}"
                        ),
                    )
                if problem["problem_id"] in problem_ids:
                    raise AlgorithmFoundationCatalogError(
                        error_code="duplicate_problem_id",
                        message=f"duplicate problem_id found: {problem['problem_id']}",
                    )
                problem_ids.add(problem["problem_id"])
                if problem["canonical_language"] != "python":
                    raise AlgorithmFoundationCatalogError(
                        error_code="unsupported_canonical_language",
                        message=(
                            f"unit {unit['unit_id']} problem {problem['problem_id']} "
                            f"must use canonical_language='python'"
                        ),
                    )
                payload = (
                    problem["problem_statement"],
                    problem["input_format"],
                    problem["output_format"],
                    problem["constraints"],
                    repr(problem["examples"]),
                )
                if payload in seen_payloads:
                    raise AlgorithmFoundationCatalogError(
                        error_code="duplicate_problem_payload",
                        message=(
                            f"unit {unit['unit_id']} contains duplicated problem payloads"
                        ),
                    )
                seen_payloads.add(payload)
        counts = self.counts()
        if counts != (320, 366):
            raise AlgorithmFoundationCatalogError(
                error_code="catalog_count_mismatch",
                message=(
                    "algorithm foundations catalog must contain exactly "
                    "320 units and 366 problems"
                ),
            )
        self._validate_prerequisite_cycles()

    def _validate_prerequisite_cycles(self) -> None:
        graph = {unit["unit_id"]: unit["prerequisite_unit_ids"] for unit in self._units}
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> None:
            if node in visited:
                return
            if node in visiting:
                raise AlgorithmFoundationCatalogError(
                    error_code="prerequisite_cycle",
                    message=f"cycle detected in algorithm foundations prerequisites: {node}",
                )
            visiting.add(node)
            for nxt in graph[node]:
                visit(nxt)
            visiting.remove(node)
            visited.add(node)

        for node in graph:
            visit(node)

    def _special_extra_count(self) -> int:
        return sum(len(defs) - 2 for defs in _SPECIAL_THEME_UNITS.values())

    def _unit_map_title(self, units: list[AlgorithmFoundationUnit], unit_id: str) -> str:
        for unit in units:
            if unit["unit_id"] == unit_id:
                return unit["title"]
        return unit_id

    def _is_important_unit(self, theme_id: str, unit_id: str) -> bool:
        if theme_id not in _IMPORTANT_THEME_IDS:
            return False
        return unit_id.endswith(("-basic", "-practice")) or (
            theme_id in _SPECIAL_THEME_UNITS and (
                unit_id.endswith(
                    (
                        "stack-basics",
                        "stack-brackets",
                        "prefix-sum-1d",
                        "prefix-sum-range",
                        "hashmap-exists",
                        "hashmap-duplicate",
                    ),
                )
            )
        )

    def _slug(self, text: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", text.lower())
        slug = slug.strip("-")
        return slug or "unit"


def _default_rubric(unit_kind: str) -> list[AlgorithmFoundationRubricItem]:
    if unit_kind == "integration":
        return [
            {"criterion": "方針の選択", "points": 40, "description": "既習2unitまでで素直に解法を立てている"},
            {"criterion": "実装の正しさ", "points": 40, "description": "境界条件を含めて正しく動作する"},
            {"criterion": "整理されたコード", "points": 20, "description": "補助構造の更新順が読み取りやすい"},
        ]
    return [
        {"criterion": "基本方針", "points": 45, "description": "学習単位の中核発想を使えている"},
        {"criterion": "実装の正しさ", "points": 40, "description": "標準的なケースを正しく処理できる"},
        {"criterion": "境界条件", "points": 15, "description": "空・重複・端の扱いを崩さない"},
    ]


def _array_template(  # noqa: PLR0913
    *,
    statement: str,
    input_format: str,
    output_format: str,
    constraints: str,
    examples: list[AlgorithmFoundationExample],
    reference_solution: str,
) -> dict[str, str | list[AlgorithmFoundationExample]]:
    return {
        "statement": statement,
        "input_format": input_format,
        "output_format": output_format,
        "constraints": constraints,
        "examples": examples,
        "reference_solution": reference_solution,
    }


__all__ = ["AlgorithmFoundationCatalog"]
