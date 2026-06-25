"""競プロうさぎの静的カタログ生成。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

from algorithm_foundations.domain.foundation_types import (
    AlgorithmFoundationCatalogError,
    AlgorithmFoundationCatalogResponse,
    AlgorithmFoundationExample,
    AlgorithmFoundationGroupSummary,
    AlgorithmFoundationProblem,
    AlgorithmFoundationRubricItem,
    AlgorithmFoundationUnit,
    AlgorithmFoundationUnitSummary,
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

_SPECIAL_THEME_UNITS: Final[dict[str, list[tuple[str, str, str]]]] = {
    "algo-093": [
        ("stack-basics", "スタックの基本操作", "foundation"),
        ("stack-brackets", "括弧対応と後入れ先出し", "foundation"),
        ("stack-cancel", "スタックで消去をシミュレート", "integration"),
    ],
    "algo-094": [
        ("queue-basics", "キューの基本操作", "foundation"),
        ("deque-basics", "デックの基本操作", "foundation"),
    ],
    "algo-099": [
        ("prefix-sum-1d", "一次元累積和の基本", "foundation"),
        ("prefix-sum-range", "累積和で区間和を求める", "foundation"),
        ("prefix-sum-2d", "二次元累積和で長方形和を求める", "integration"),
    ],
    "algo-102": [
        ("hashmap-exists", "存在判定をハッシュで高速化", "foundation"),
        ("hashmap-duplicate", "重複検出をハッシュで行う", "foundation"),
        ("hashmap-count", "出現回数カウント", "foundation"),
        ("hashmap-index", "値から位置を引く対応表", "foundation"),
        ("hashmap-match", "2配列の照合をハッシュで処理", "integration"),
    ],
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
    ) -> AlgorithmFoundationCatalogResponse:
        best_scores = best_scores or {}
        last_attempted_at = last_attempted_at or {}
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
        expanded_ids = {
            theme.id
            for theme in ordered_themes
            if theme.id not in _SPECIAL_THEME_UNITS
        }
        expanded_ids = set(list(expanded_ids)[:0])
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
        important_unit = self._is_important_unit(theme.id, unit_id)
        problem_count = 6 if important_unit else 3
        problem_bank = [
            self._build_problem(
                unit_id=unit_id,
                unit_title=title,
                theme=theme,
                problem_index=index,
                unit_kind=unit_kind,
                prerequisite_titles=prerequisite_titles,
            )
            for index in range(problem_count)
        ]
        return {
            "unit_id": unit_id,
            "theme_id": theme.id,
            "group_id": group_id,
            "group_title": _GROUP_DISPLAY_TITLE.get(theme.category, theme.category),
            "title": title,
            "display_order": display_order,
            "prerequisite_unit_ids": prerequisite_unit_ids,
            "prerequisite_titles": prerequisite_titles,
            "allowed_knowledge": allowed,
            "forbidden_knowledge": forbidden,
            "target_skill": title,
            "unit_kind": unit_kind,  # type: ignore[typeddict-item]
            "problem_bank": problem_bank,
        }

    def _build_problem(  # noqa: PLR0913
        self,
        *,
        unit_id: str,
        unit_title: str,
        theme: _Theme,
        problem_index: int,
        unit_kind: str,
        prerequisite_titles: list[str],
    ) -> AlgorithmFoundationProblem:
        template = self._problem_template(theme, unit_title)
        difficulty_labels = (
            (
                "既習2unitの組み合わせ確認",
                "実装のつなぎ込み",
                "条件違いの確認",
            )
            if unit_kind == "integration"
            else (
                "知識をそのまま使う確認",
                "実装の定着",
                "境界条件の確認",
                "別表現への言い換え",
                "制約付きの整理",
                "軽い総合確認",
            )
        )
        prompt_kind = difficulty_labels[problem_index]
        support = (
            "既習の 2 unit までを素直に組み合わせてください。"
            if unit_kind == "integration"
            else "この unit の知識だけで解けるように作ってあります。"
        )
        prerequisites_text = (
            f"前提として使ってよい知識: {', '.join(prerequisite_titles)}。"
            if prerequisite_titles
            else "前提として他の知識は要求しません。"
        )
        statement = (
            f"{prompt_kind}として、{unit_title} を使う 1 問です。\n\n"
            f"- カテゴリ: {theme.category}\n"
            f"- 学習単位: {unit_title}\n"
            f"- ねらい: {support}\n"
            f"- 補足: {prerequisites_text}\n\n"
            + cast("str", template["statement"])
        )
        return {
            "problem_id": f"{unit_id}-p{problem_index + 1}",
            "title": f"{prompt_kind}: {unit_title}",
            "problem_statement": statement,
            "input_format": cast("str", template["input_format"]),
            "output_format": cast("str", template["output_format"]),
            "constraints": cast("str", template["constraints"]),
            "examples": cast("list[AlgorithmFoundationExample]", template["examples"]),
            "canonical_reference_solution": cast(
                "str",
                template["reference_solution"],
            ),
            "canonical_language": "python",
            "grading_rubric": _default_rubric(unit_kind),
        }

    def _problem_template(  # noqa: C901, PLR0915
        self,
        theme: _Theme,
        unit_title: str,
    ) -> dict[str, str | list[AlgorithmFoundationExample]]:
        key = f"{theme.label} {unit_title}"
        title = unit_title
        if title == "括弧対応と後入れ先出し":
            return _array_template(
                statement="括弧列 S が与えられる。対応が正しい括弧列なら Yes、そうでなければ No を出力せよ。",
                input_format="1 行目に S。",
                output_format="Yes / No を出力する。",
                constraints="1 <= |S| <= 2 * 10^5\nS は '(' と ')' からなる",
                examples=[{"input": "(()())", "output": "Yes"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    s = input().strip()\n"
                    "    depth = 0\n"
                    "    for ch in s:\n"
                    "        if ch == '(':\n"
                    "            depth += 1\n"
                    "        else:\n"
                    "            depth -= 1\n"
                    "        if depth < 0:\n"
                    "            print('No')\n"
                    "            return\n"
                    "    print('Yes' if depth == 0 else 'No')\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if title == "スタックで消去をシミュレート":
            return _array_template(
                statement=(
                    "英小文字からなる文字列 S が与えられる。"
                    " 左から順に見て、直前と同じ文字が現れたら 2 文字まとめて消す操作を繰り返した最終文字列を出力せよ。"
                ),
                input_format="1 行目に S。",
                output_format="最終文字列を出力する。",
                constraints="1 <= |S| <= 2 * 10^5",
                examples=[{"input": "abbaca", "output": "ca"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    s = input().strip()\n"
                    "    stack = []\n"
                    "    for ch in s:\n"
                    "        if stack and stack[-1] == ch:\n"
                    "            stack.pop()\n"
                    "        else:\n"
                    "            stack.append(ch)\n"
                    "    print(''.join(stack))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if title == "一次元累積和の基本":
            return _array_template(
                statement="長さ N の整数列 A が与えられる。累積和 P を `P0=0, Pi=A1+...+Ai` と定義し、P0 から PN までを出力せよ。",
                input_format="1 行目に N。\n2 行目に A1..AN。",
                output_format="P0..PN を空白区切りで出力する。",
                constraints="1 <= N <= 2 * 10^5\n|Ai| <= 10^9",
                examples=[{"input": "4\n3 1 4 1", "output": "0 3 4 8 9"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    input()\n"
                    "    a = list(map(int, input().split()))\n"
                    "    prefix = [0]\n"
                    "    for value in a:\n"
                    "        prefix.append(prefix[-1] + value)\n"
                    "    print(*prefix)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if title == "二次元累積和で長方形和を求める":
            return _array_template(
                statement=(
                    "H 行 W 列の整数表 A と Q 個の長方形が与えられる。"
                    " 各問い合わせについて、左上 (r1, c1)、右下 (r2, c2) に囲まれる長方形の総和を求めよ。"
                ),
                input_format=(
                    "1 行目に H W Q。\n"
                    "続く H 行に各行の値。\n"
                    "続く Q 行に r1 c1 r2 c2 (1-indexed)。"
                ),
                output_format="各問い合わせの長方形和を 1 行ずつ出力する。",
                constraints="1 <= H, W, Q <= 2 * 10^3\n|Aij| <= 10^9",
                examples=[{"input": "2 3 2\n1 2 3\n4 5 6\n1 1 2 2\n2 2 2 3", "output": "12\n11"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    h, w, q = map(int, input().split())\n"
                    "    prefix = [[0] * (w + 1) for _ in range(h + 1)]\n"
                    "    for i in range(1, h + 1):\n"
                    "        row = list(map(int, input().split()))\n"
                    "        for j in range(1, w + 1):\n"
                    "            prefix[i][j] = (\n"
                    "                prefix[i - 1][j]\n"
                    "                + prefix[i][j - 1]\n"
                    "                - prefix[i - 1][j - 1]\n"
                    "                + row[j - 1]\n"
                    "            )\n"
                    "    out = []\n"
                    "    for _ in range(q):\n"
                    "        r1, c1, r2, c2 = map(int, input().split())\n"
                    "        total = (\n"
                    "            prefix[r2][c2]\n"
                    "            - prefix[r1 - 1][c2]\n"
                    "            - prefix[r2][c1 - 1]\n"
                    "            + prefix[r1 - 1][c1 - 1]\n"
                    "        )\n"
                    "        out.append(str(total))\n"
                    "    sys.stdout.write('\\n'.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if title == "存在判定をハッシュで高速化":
            return _array_template(
                statement=(
                    "長さ N の整数列 A と Q 個の問い合わせ x が与えられる。"
                    " 各問い合わせについて x が A に含まれるなら Yes、含まれないなら No を出力せよ。"
                ),
                input_format="1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に x。",
                output_format="各問い合わせごとに Yes / No を 1 行ずつ出力する。",
                constraints="1 <= N, Q <= 2 * 10^5\n0 <= Ai, x <= 10^9",
                examples=[
                    {"input": "5 3\n1 4 2 4 7\n4\n3\n7", "output": "Yes\nNo\nYes"},
                ],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, q = map(int, input().split())\n"
                    "    values = set(map(int, input().split()))\n"
                    "    out = []\n"
                    "    for _ in range(q):\n"
                    "        x = int(input())\n"
                    "        out.append('Yes' if x in values else 'No')\n"
                    "    sys.stdout.write('\\n'.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if title == "重複検出をハッシュで行う":
            return _array_template(
                statement="長さ N の整数列 A が与えられる。同じ値が 2 回以上現れるなら Yes、そうでなければ No を出力せよ。",
                input_format="1 行目に N。\n2 行目に A1..AN。",
                output_format="Yes / No を出力する。",
                constraints="1 <= N <= 2 * 10^5\n0 <= Ai <= 10^9",
                examples=[{"input": "5\n1 4 2 4 7", "output": "Yes"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    input()\n"
                    "    a = list(map(int, input().split()))\n"
                    "    seen = set()\n"
                    "    for value in a:\n"
                    "        if value in seen:\n"
                    "            print('Yes')\n"
                    "            return\n"
                    "        seen.add(value)\n"
                    "    print('No')\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if title == "出現回数カウント":
            return _array_template(
                statement=(
                    "長さ N の整数列 A と Q 個の問い合わせ x が与えられる。"
                    " 各問い合わせについて x の出現回数を出力せよ。"
                ),
                input_format="1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に x。",
                output_format="各問い合わせの答えを 1 行ずつ出力する。",
                constraints="1 <= N, Q <= 2 * 10^5\n0 <= Ai, x <= 10^9",
                examples=[{"input": "6 3\n1 4 2 4 7 4\n4\n3\n1", "output": "3\n0\n1"}],
                reference_solution=(
                    "from collections import Counter\n\n"
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, q = map(int, input().split())\n"
                    "    counter = Counter(map(int, input().split()))\n"
                    "    out = []\n"
                    "    for _ in range(q):\n"
                    "        x = int(input())\n"
                    "        out.append(str(counter[x]))\n"
                    "    sys.stdout.write('\\n'.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if title == "値から位置を引く対応表":
            return _array_template(
                statement=(
                    "長さ N の整数列 A はすべて異なる。"
                    " Q 個の問い合わせ x について、x が A の何番目にあるかを 1-indexed で出力し、"
                    " 含まれなければ -1 を出力せよ。"
                ),
                input_format="1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に x。",
                output_format="各問い合わせの答えを 1 行ずつ出力する。",
                constraints="1 <= N, Q <= 2 * 10^5\n0 <= Ai, x <= 10^9",
                examples=[{"input": "5 3\n10 20 30 40 50\n40\n15\n10", "output": "4\n-1\n1"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, q = map(int, input().split())\n"
                    "    pos = {value: idx for idx, value in enumerate(map(int, input().split()), start=1)}\n"
                    "    out = []\n"
                    "    for _ in range(q):\n"
                    "        x = int(input())\n"
                    "        out.append(str(pos.get(x, -1)))\n"
                    "    sys.stdout.write('\\n'.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if title == "2配列の照合をハッシュで処理":
            return _array_template(
                statement=(
                    "長さ N の整数列 A, B が与えられる。"
                    " 並べ替えると一致するなら Yes、そうでなければ No を出力せよ。"
                ),
                input_format="1 行目に N。\n2 行目に A1..AN。\n3 行目に B1..BN。",
                output_format="Yes / No を出力する。",
                constraints="1 <= N <= 2 * 10^5\n0 <= Ai, Bi <= 10^9",
                examples=[{"input": "4\n1 2 2 5\n2 5 1 2", "output": "Yes"}],
                reference_solution=(
                    "from collections import Counter\n\n"
                    "def solve() -> None:\n"
                    "    input()\n"
                    "    a = Counter(map(int, input().split()))\n"
                    "    b = Counter(map(int, input().split()))\n"
                    "    print('Yes' if a == b else 'No')\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if title == "いもす法 の基本":
            return _array_template(
                statement=(
                    "長さ N の配列に対して Q 個の加算操作 `[l, r] に x を足す` が与えられる。"
                    " すべて適用した後の配列を出力せよ。"
                ),
                input_format="1 行目に N Q。\n続く Q 行に l r x。",
                output_format="最終的な配列を空白区切りで出力する。",
                constraints="1 <= N, Q <= 2 * 10^5\n|x| <= 10^9",
                examples=[{"input": "5 3\n1 3 2\n2 5 1\n4 4 -2", "output": "2 3 3 -1 1"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, q = map(int, input().split())\n"
                    "    diff = [0] * (n + 1)\n"
                    "    for _ in range(q):\n"
                    "        l, r, x = map(int, input().split())\n"
                    "        diff[l - 1] += x\n"
                    "        if r < n:\n"
                    "            diff[r] -= x\n"
                    "    ans = []\n"
                    "    cur = 0\n"
                    "    for i in range(n):\n"
                    "        cur += diff[i]\n"
                    "        ans.append(cur)\n"
                    "    print(*ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if title == "単調スタック の基本":
            return _array_template(
                statement=(
                    "長さ N の整数列 A が与えられる。各 i について、i より左で `A_j < A_i` を満たす最も近い位置 j を求め、"
                    " 存在しなければ -1 を出力せよ。"
                ),
                input_format="1 行目に N。\n2 行目に A1..AN。",
                output_format="N 個の答えを空白区切りで出力する。",
                constraints="1 <= N <= 2 * 10^5",
                examples=[{"input": "5\n3 7 4 6 2", "output": "-1 1 1 3 -1"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    input()\n"
                    "    a = list(map(int, input().split()))\n"
                    "    stack = []\n"
                    "    ans = []\n"
                    "    for i, value in enumerate(a, start=1):\n"
                    "        while stack and stack[-1][0] >= value:\n"
                    "            stack.pop()\n"
                    "        ans.append(stack[-1][1] if stack else -1)\n"
                    "        stack.append((value, i))\n"
                    "    print(*ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if title == "単調デック（スライド最小値） の基本":
            return _array_template(
                statement=(
                    "長さ N の整数列 A と幅 K が与えられる。"
                    " 各長さ K の連続部分列について最小値を求めよ。"
                ),
                input_format="1 行目に N K。\n2 行目に A1..AN。",
                output_format="各区間の最小値を空白区切りで出力する。",
                constraints="1 <= K <= N <= 2 * 10^5",
                examples=[{"input": "7 3\n4 2 5 1 6 3 7", "output": "2 1 1 1 3"}],
                reference_solution=(
                    "from collections import deque\n\n"
                    "def solve() -> None:\n"
                    "    n, k = map(int, input().split())\n"
                    "    a = list(map(int, input().split()))\n"
                    "    dq = deque()\n"
                    "    ans = []\n"
                    "    for i, value in enumerate(a):\n"
                    "        while dq and a[dq[-1]] >= value:\n"
                    "            dq.pop()\n"
                    "        dq.append(i)\n"
                    "        if dq[0] <= i - k:\n"
                    "            dq.popleft()\n"
                    "        if i >= k - 1:\n"
                    "            ans.append(a[dq[0]])\n"
                    "    print(*ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if title == "Manacher法（最長回文） の基本":
            return _array_template(
                statement="文字列 S が与えられる。回文部分文字列の最長長さを求めよ。",
                input_format="1 行目に S。",
                output_format="最長長さを出力する。",
                constraints="1 <= |S| <= 2 * 10^5",
                examples=[{"input": "abacaba", "output": "7"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    s = input().strip()\n"
                    "    t = '^#' + '#'.join(s) + '#$'\n"
                    "    radius = [0] * len(t)\n"
                    "    center = right = 0\n"
                    "    ans = 0\n"
                    "    for i in range(1, len(t) - 1):\n"
                    "        mirror = 2 * center - i\n"
                    "        if i < right:\n"
                    "            radius[i] = min(right - i, radius[mirror])\n"
                    "        while t[i + radius[i] + 1] == t[i - radius[i] - 1]:\n"
                    "            radius[i] += 1\n"
                    "        if i + radius[i] > right:\n"
                    "            center = i\n"
                    "            right = i + radius[i]\n"
                    "        ans = max(ans, radius[i])\n"
                    "    print(ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-049":
            return _array_template(
                statement=(
                    "整数 N, K が与えられる。1 歩で 1 以上 K 以下進めるとき、"
                    " ちょうど N に到達する方法数を 10^9+7 で割った余りで求めよ。"
                ),
                input_format="1 行目に N K。",
                output_format="方法数を出力する。",
                constraints="1 <= N <= 2 * 10^5\n1 <= K <= 2 * 10^5",
                examples=[{"input": "4 2", "output": "5"}],
                reference_solution=(
                    "MOD = 10 ** 9 + 7\n\n"
                    "def solve() -> None:\n"
                    "    n, k = map(int, input().split())\n"
                    "    dp = [0] * (n + 1)\n"
                    "    pref = [0] * (n + 2)\n"
                    "    dp[0] = 1\n"
                    "    pref[1] = 1\n"
                    "    for i in range(1, n + 1):\n"
                    "        left = max(0, i - k)\n"
                    "        dp[i] = (pref[i] - pref[left]) % MOD\n"
                    "        pref[i + 1] = (pref[i] + dp[i]) % MOD\n"
                    "    print(dp[n])\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-074":
            return _array_template(
                statement="文字列 S が与えられる。回文部分文字列の最長長さを求めよ。",
                input_format="1 行目に S。",
                output_format="最長長さを出力する。",
                constraints="1 <= |S| <= 2 * 10^5",
                examples=[{"input": "abacaba", "output": "7"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    s = input().strip()\n"
                    "    t = '^#' + '#'.join(s) + '#$'\n"
                    "    radius = [0] * len(t)\n"
                    "    center = right = 0\n"
                    "    ans = 0\n"
                    "    for i in range(1, len(t) - 1):\n"
                    "        mirror = 2 * center - i\n"
                    "        if i < right:\n"
                    "            radius[i] = min(right - i, radius[mirror])\n"
                    "        while t[i + radius[i] + 1] == t[i - radius[i] - 1]:\n"
                    "            radius[i] += 1\n"
                    "        if i + radius[i] > right:\n"
                    "            center = i\n"
                    "            right = i + radius[i]\n"
                    "        ans = max(ans, radius[i])\n"
                    "    print(ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-095":
            return _array_template(
                statement=(
                    "Q 個の操作が与えられる。"
                    " `1 x` は整数 x を追加し、`2` は現在入っている値のうち最小値を出力して削除せよ。"
                ),
                input_format="1 行目に Q。\n続く Q 行に操作。",
                output_format="type=2 のたびに取り出した最小値を 1 行ずつ出力する。",
                constraints="1 <= Q <= 2 * 10^5\ntype=2 の時点で優先度付きキューは空でない",
                examples=[{"input": "6\n1 5\n1 2\n2\n1 4\n2\n2", "output": "2\n4\n5"}],
                reference_solution=(
                    "import heapq\n\n"
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    q = int(input())\n"
                    "    heap = []\n"
                    "    out = []\n"
                    "    for _ in range(q):\n"
                    "        parts = list(map(int, input().split()))\n"
                    "        if parts[0] == 1:\n"
                    "            heapq.heappush(heap, parts[1])\n"
                    "        else:\n"
                    "            out.append(str(heapq.heappop(heap)))\n"
                    "    sys.stdout.write('\\n'.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-100":
            return _array_template(
                statement=(
                    "長さ N の配列に対して Q 個の加算操作 `[l, r] に x を足す` が与えられる。"
                    " すべて適用した後の配列を出力せよ。"
                ),
                input_format="1 行目に N Q。\n続く Q 行に l r x。",
                output_format="最終的な配列を空白区切りで出力する。",
                constraints="1 <= N, Q <= 2 * 10^5\n|x| <= 10^9",
                examples=[{"input": "5 3\n1 3 2\n2 5 1\n4 4 -2", "output": "2 3 3 -1 1"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, q = map(int, input().split())\n"
                    "    diff = [0] * (n + 1)\n"
                    "    for _ in range(q):\n"
                    "        l, r, x = map(int, input().split())\n"
                    "        diff[l - 1] += x\n"
                    "        if r < n:\n"
                    "            diff[r] -= x\n"
                    "    ans = []\n"
                    "    cur = 0\n"
                    "    for i in range(n):\n"
                    "        cur += diff[i]\n"
                    "        ans.append(cur)\n"
                    "    print(*ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-101":
            return _array_template(
                statement=(
                    "Q 個の操作が与えられる。`1 x` は x を集合に追加し、`2 x` は x を削除し、"
                    " `3 x` は x が存在するなら Yes、そうでなければ No を出力せよ。"
                ),
                input_format="1 行目に Q。\n続く Q 行に操作。",
                output_format="type=3 のたびに Yes / No を出力する。",
                constraints="1 <= Q <= 2 * 10^5\n0 <= x <= 10^9",
                examples=[{"input": "6\n1 5\n1 2\n3 2\n2 2\n3 2\n3 5", "output": "Yes\nNo\nYes"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    q = int(input())\n"
                    "    values = set()\n"
                    "    out = []\n"
                    "    for _ in range(q):\n"
                    "        t, x = map(int, input().split())\n"
                    "        if t == 1:\n"
                    "            values.add(x)\n"
                    "        elif t == 2:\n"
                    "            values.discard(x)\n"
                    "        else:\n"
                    "            out.append('Yes' if x in values else 'No')\n"
                    "    sys.stdout.write('\\n'.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-104":
            return _array_template(
                statement=(
                    "長さ N の整数列 A が与えられる。各 i について、i より左で `A_j < A_i` を満たす最も近い位置 j を求め、"
                    " 存在しなければ -1 を出力せよ。"
                ),
                input_format="1 行目に N。\n2 行目に A1..AN。",
                output_format="N 個の答えを空白区切りで出力する。",
                constraints="1 <= N <= 2 * 10^5",
                examples=[{"input": "5\n3 7 4 6 2", "output": "-1 1 1 3 -1"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    input()\n"
                    "    a = list(map(int, input().split()))\n"
                    "    stack = []\n"
                    "    ans = []\n"
                    "    for i, value in enumerate(a, start=1):\n"
                    "        while stack and stack[-1][0] >= value:\n"
                    "            stack.pop()\n"
                    "        ans.append(stack[-1][1] if stack else -1)\n"
                    "        stack.append((value, i))\n"
                    "    print(*ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-105":
            return _array_template(
                statement=(
                    "長さ N の整数列 A と幅 K が与えられる。"
                    " 各長さ K の連続部分列について最小値を求めよ。"
                ),
                input_format="1 行目に N K。\n2 行目に A1..AN。",
                output_format="各区間の最小値を空白区切りで出力する。",
                constraints="1 <= K <= N <= 2 * 10^5",
                examples=[{"input": "7 3\n4 2 5 1 6 3 7", "output": "2 1 1 1 3"}],
                reference_solution=(
                    "from collections import deque\n\n"
                    "def solve() -> None:\n"
                    "    n, k = map(int, input().split())\n"
                    "    a = list(map(int, input().split()))\n"
                    "    dq = deque()\n"
                    "    ans = []\n"
                    "    for i, value in enumerate(a):\n"
                    "        while dq and a[dq[-1]] >= value:\n"
                    "            dq.pop()\n"
                    "        dq.append(i)\n"
                    "        if dq[0] <= i - k:\n"
                    "            dq.popleft()\n"
                    "        if i >= k - 1:\n"
                    "            ans.append(a[dq[0]])\n"
                    "    print(*ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-106":
            return _array_template(
                statement="平面上の 2 ベクトル (ax, ay), (bx, by) が与えられる。内積と外積をこの順に出力せよ。",
                input_format="1 行目に ax ay bx by。",
                output_format="1 行に `dot cross` を出力する。",
                constraints="各値は整数",
                examples=[{"input": "1 2 3 4", "output": "11 -2"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    ax, ay, bx, by = map(int, input().split())\n"
                    "    dot = ax * bx + ay * by\n"
                    "    cross = ax * by - ay * bx\n"
                    "    print(dot, cross)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-108":
            return _array_template(
                statement="線分 AB と線分 CD が交差するなら Yes、そうでなければ No を出力せよ。",
                input_format="1 行目に ax ay bx by cx cy dx dy。",
                output_format="Yes / No を出力する。",
                constraints="座標は整数",
                examples=[{"input": "0 0 4 4 0 4 4 0", "output": "Yes"}],
                reference_solution=(
                    "def ccw(ax: int, ay: int, bx: int, by: int, cx: int, cy: int) -> int:\n"
                    "    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)\n\n"
                    "def solve() -> None:\n"
                    "    ax, ay, bx, by, cx, cy, dx, dy = map(int, input().split())\n"
                    "    c1 = ccw(ax, ay, bx, by, cx, cy)\n"
                    "    c2 = ccw(ax, ay, bx, by, dx, dy)\n"
                    "    c3 = ccw(cx, cy, dx, dy, ax, ay)\n"
                    "    c4 = ccw(cx, cy, dx, dy, bx, by)\n"
                    "    print('Yes' if c1 * c2 <= 0 and c3 * c4 <= 0 else 'No')\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-107":
            return _array_template(
                statement="平面上の N 点が与えられる。凸包に含まれる点数を求めよ。",
                input_format="1 行目に N。\n続く N 行に xi yi。",
                output_format="凸包上の点数を出力する。",
                constraints="3 <= N <= 2 * 10^5\n座標は整数",
                examples=[{"input": "5\n0 0\n2 0\n2 2\n0 2\n1 1", "output": "4"}],
                reference_solution=(
                    "def cross(o: tuple[int, int], a: tuple[int, int], b: tuple[int, int]) -> int:\n"
                    "    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])\n\n"
                    "def solve() -> None:\n"
                    "    n = int(input())\n"
                    "    pts = sorted({tuple(map(int, input().split())) for _ in range(n)})\n"
                    "    if len(pts) <= 1:\n"
                    "        print(len(pts))\n"
                    "        return\n"
                    "    lower = []\n"
                    "    for p in pts:\n"
                    "        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:\n"
                    "            lower.pop()\n"
                    "        lower.append(p)\n"
                    "    upper = []\n"
                    "    for p in reversed(pts):\n"
                    "        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:\n"
                    "            upper.pop()\n"
                    "        upper.append(p)\n"
                    "    hull = lower[:-1] + upper[:-1]\n"
                    "    print(len(hull))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-109":
            return _array_template(
                statement="点 P と直線 AB が与えられる。P から直線 AB への距離を求めよ。",
                input_format="1 行目に px py ax ay bx by。",
                output_format="距離を出力する。",
                constraints="座標は整数",
                examples=[{"input": "0 2 -1 0 1 0", "output": "2.0"}],
                reference_solution=(
                    "import math\n\n"
                    "def solve() -> None:\n"
                    "    px, py, ax, ay, bx, by = map(int, input().split())\n"
                    "    cross = abs((bx - ax) * (py - ay) - (by - ay) * (px - ax))\n"
                    "    length = math.hypot(bx - ax, by - ay)\n"
                    "    print(cross / length)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-110":
            return _array_template(
                statement="頂点が順に与えられる多角形の面積を求めよ。",
                input_format="1 行目に N。\n続く N 行に xi yi。",
                output_format="面積を出力する。",
                constraints="3 <= N <= 2 * 10^5\n座標は整数",
                examples=[{"input": "4\n0 0\n2 0\n2 1\n0 1", "output": "2.0"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    n = int(input())\n"
                    "    points = [tuple(map(int, input().split())) for _ in range(n)]\n"
                    "    total = 0\n"
                    "    for i in range(n):\n"
                    "        x1, y1 = points[i]\n"
                    "        x2, y2 = points[(i + 1) % n]\n"
                    "        total += x1 * y2 - y1 * x2\n"
                    "    print(abs(total) / 2)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-111":
            return _array_template(
                statement="多角形と点 P が与えられる。P が多角形の内部または辺上なら Yes、外部なら No を出力せよ。",
                input_format="1 行目に N。\n続く N 行に xi yi。\n最後に px py。",
                output_format="Yes / No を出力する。",
                constraints="3 <= N <= 2 * 10^5\n座標は整数",
                examples=[{"input": "4\n0 0\n4 0\n4 4\n0 4\n2 2", "output": "Yes"}],
                reference_solution=(
                    "def on_segment(ax: int, ay: int, bx: int, by: int, px: int, py: int) -> bool:\n"
                    "    cross = (bx - ax) * (py - ay) - (by - ay) * (px - ax)\n"
                    "    if cross != 0:\n"
                    "        return False\n"
                    "    return min(ax, bx) <= px <= max(ax, bx) and min(ay, by) <= py <= max(ay, by)\n\n"
                    "def solve() -> None:\n"
                    "    n = int(input())\n"
                    "    pts = [tuple(map(int, input().split())) for _ in range(n)]\n"
                    "    px, py = map(int, input().split())\n"
                    "    inside = False\n"
                    "    for i in range(n):\n"
                    "        ax, ay = pts[i]\n"
                    "        bx, by = pts[(i + 1) % n]\n"
                    "        if on_segment(ax, ay, bx, by, px, py):\n"
                    "            print('Yes')\n"
                    "            return\n"
                    "        if ((ay > py) != (by > py)):\n"
                    "            x = (bx - ax) * (py - ay) / (by - ay) + ax\n"
                    "            if x >= px:\n"
                    "                inside = not inside\n"
                    "    print('Yes' if inside else 'No')\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-112":
            return _array_template(
                statement="直線 AB と直線 CD が平行なら Parallel、そうでなければ Intersect を出力せよ。",
                input_format="1 行目に ax ay bx by cx cy dx dy。",
                output_format="Parallel または Intersect を出力する。",
                constraints="座標は整数",
                examples=[{"input": "0 0 1 1 0 1 1 2", "output": "Parallel"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    ax, ay, bx, by, cx, cy, dx, dy = map(int, input().split())\n"
                    "    cross = (bx - ax) * (dy - cy) - (by - ay) * (dx - cx)\n"
                    "    print('Parallel' if cross == 0 else 'Intersect')\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-113":
            return _array_template(
                statement=(
                    "点 (x, y) と Q 個の操作が与えられる。"
                    " `T dx dy` は平行移動、`R` は原点まわりに 90 度反時計回り回転とする。"
                    " すべて適用した後の座標を出力せよ。"
                ),
                input_format="1 行目に x y。\n2 行目に Q。\n続く Q 行に操作。",
                output_format="最終座標を `x y` で出力する。",
                constraints="1 <= Q <= 2 * 10^5\n座標は整数",
                examples=[{"input": "1 2\n3\nT 1 0\nR\nT 0 -1", "output": "-2 1"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    x, y = map(int, input().split())\n"
                    "    q = int(input())\n"
                    "    for _ in range(q):\n"
                    "        parts = input().split()\n"
                    "        if parts[0] == 'T':\n"
                    "            x += int(parts[1])\n"
                    "            y += int(parts[2])\n"
                    "        else:\n"
                    "            x, y = -y, x\n"
                    "    print(x, y)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-114":
            return _array_template(
                statement="円の中心 C と半径 r、直線 AB が与えられる。交点の個数を 0, 1, 2 のいずれかで出力せよ。",
                input_format="1 行目に cx cy r ax ay bx by。",
                output_format="交点の個数を出力する。",
                constraints="座標と半径は整数",
                examples=[{"input": "0 0 5 -10 0 10 0", "output": "2"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import math\n"
                    "    cx, cy, r, ax, ay, bx, by = map(int, input().split())\n"
                    "    cross = abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax))\n"
                    "    length = math.hypot(bx - ax, by - ay)\n"
                    "    dist = cross / length\n"
                    "    if dist > r:\n"
                    "        print(0)\n"
                    "    elif abs(dist - r) < 1e-9:\n"
                    "        print(1)\n"
                    "    else:\n"
                    "        print(2)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-102":
            return _array_template(
                statement=(
                    "長さ N の整数列 A と Q 個の問い合わせ x が与えられる。"
                    " 各問い合わせについて x が A に含まれるなら Yes、含まれないなら No を出力せよ。"
                ),
                input_format="1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に x。",
                output_format="各問い合わせごとに Yes / No を 1 行ずつ出力する。",
                constraints="1 <= N, Q <= 2 * 10^5\n0 <= Ai, x <= 10^9",
                examples=[
                    {"input": "5 3\n1 4 2 4 7\n4\n3\n7", "output": "Yes\nNo\nYes"},
                ],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, q = map(int, input().split())\n"
                    "    values = set(map(int, input().split()))\n"
                    "    out = []\n"
                    "    for _ in range(q):\n"
                    "        x = int(input())\n"
                    "        out.append('Yes' if x in values else 'No')\n"
                    "    sys.stdout.write('\\n'.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if title == "スタックの基本操作":
            return _array_template(
                statement=(
                    "Q 個の操作が与えられる。"
                    " `1 x` は x を積み、`2` は一番上を取り除き、`3` は一番上の値を出力せよ。"
                ),
                input_format="1 行目に Q。\n続く Q 行に操作。",
                output_format="type=3 のたびに一番上の値を 1 行ずつ出力する。",
                constraints="1 <= Q <= 2 * 10^5\ntype=2,3 の時点でスタックは空でない",
                examples=[{"input": "7\n1 3\n1 5\n3\n2\n3\n1 9\n3", "output": "5\n3\n9"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    q = int(input())\n"
                    "    stack = []\n"
                    "    out = []\n"
                    "    for _ in range(q):\n"
                    "        parts = list(map(int, input().split()))\n"
                    "        if parts[0] == 1:\n"
                    "            stack.append(parts[1])\n"
                    "        elif parts[0] == 2:\n"
                    "            stack.pop()\n"
                    "        else:\n"
                    "            out.append(str(stack[-1]))\n"
                    "    sys.stdout.write('\\n'.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if title == "優先度付きキュー（ヒープ） の基本":
            return _array_template(
                statement=(
                    "Q 個の操作が与えられる。"
                    " `1 x` は整数 x を追加し、`2` は現在入っている値のうち最小値を出力して削除せよ。"
                ),
                input_format="1 行目に Q。\n続く Q 行に操作。",
                output_format="type=2 のたびに取り出した最小値を 1 行ずつ出力する。",
                constraints="1 <= Q <= 2 * 10^5\ntype=2 の時点で優先度付きキューは空でない",
                examples=[{"input": "6\n1 5\n1 2\n2\n1 4\n2\n2", "output": "2\n4\n5"}],
                reference_solution=(
                    "import heapq\n\n"
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    q = int(input())\n"
                    "    heap = []\n"
                    "    out = []\n"
                    "    for _ in range(q):\n"
                    "        parts = list(map(int, input().split()))\n"
                    "        if parts[0] == 1:\n"
                    "            heapq.heappush(heap, parts[1])\n"
                    "        else:\n"
                    "            out.append(str(heapq.heappop(heap)))\n"
                    "    sys.stdout.write('\\n'.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "デック" in title:
            return _array_template(
                statement=(
                    "Q 個の操作が与えられる。"
                    " `1 x` は先頭に追加、`2 x` は末尾に追加、`3` は先頭を出力して削除、`4` は末尾を出力して削除せよ。"
                ),
                input_format="1 行目に Q。\n続く Q 行に操作。",
                output_format="type=3,4 のたびに取り出した値を 1 行ずつ出力する。",
                constraints="1 <= Q <= 2 * 10^5",
                examples=[{"input": "6\n1 3\n2 8\n3\n1 2\n4\n3", "output": "3\n8\n2"}],
                reference_solution=(
                    "from collections import deque\n\n"
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    q = int(input())\n"
                    "    dq = deque()\n"
                    "    out = []\n"
                    "    for _ in range(q):\n"
                    "        parts = list(map(int, input().split()))\n"
                    "        t = parts[0]\n"
                    "        if t == 1:\n"
                    "            dq.appendleft(parts[1])\n"
                    "        elif t == 2:\n"
                    "            dq.append(parts[1])\n"
                    "        elif t == 3:\n"
                    "            out.append(str(dq.popleft()))\n"
                    "        else:\n"
                    "            out.append(str(dq.pop()))\n"
                    "    sys.stdout.write('\\n'.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "キュー" in title:
            return _array_template(
                statement=(
                    "Q 個の操作が与えられる。"
                    " `1 x` は末尾に x を追加し、`2` は先頭を取り除き、`3` は先頭の値を出力せよ。"
                ),
                input_format="1 行目に Q。\n続く Q 行に操作。",
                output_format="type=3 のたびに先頭の値を 1 行ずつ出力する。",
                constraints="1 <= Q <= 2 * 10^5",
                examples=[{"input": "6\n1 4\n1 7\n3\n2\n1 9\n3", "output": "4\n7"}],
                reference_solution=(
                    "from collections import deque\n\n"
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    q = int(input())\n"
                    "    queue = deque()\n"
                    "    out = []\n"
                    "    for _ in range(q):\n"
                    "        parts = list(map(int, input().split()))\n"
                    "        if parts[0] == 1:\n"
                    "            queue.append(parts[1])\n"
                    "        elif parts[0] == 2:\n"
                    "            queue.popleft()\n"
                    "        else:\n"
                    "            out.append(str(queue[0]))\n"
                    "    sys.stdout.write('\\n'.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if title == "累積和で区間和を求める":
            return _array_template(
                statement=(
                    "長さ N の整数列 A と Q 個の区間 [L, R] が与えられる。"
                    " 各区間について Ai..Aj の総和を求めよ。"
                ),
                input_format="1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に L R (1-indexed)。",
                output_format="各問い合わせの区間和を 1 行ずつ出力する。",
                constraints="1 <= N, Q <= 2 * 10^5\n|Ai| <= 10^9",
                examples=[
                    {"input": "5 3\n1 2 3 4 5\n1 3\n2 5\n4 4", "output": "6\n14\n4"},
                ],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, q = map(int, input().split())\n"
                    "    a = list(map(int, input().split()))\n"
                    "    prefix = [0]\n"
                    "    for value in a:\n"
                    "        prefix.append(prefix[-1] + value)\n"
                    "    out = []\n"
                    "    for _ in range(q):\n"
                    "        l, r = map(int, input().split())\n"
                    "        out.append(str(prefix[r] - prefix[l - 1]))\n"
                    "    sys.stdout.write('\\n'.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if title == "累積和を用いたDP高速化 の基本":
            return _array_template(
                statement=(
                    "整数 N, K が与えられる。1 歩で 1 以上 K 以下進めるとき、"
                    " ちょうど N に到達する方法数を 10^9+7 で割った余りで求めよ。"
                ),
                input_format="1 行目に N K。",
                output_format="方法数を出力する。",
                constraints="1 <= N <= 2 * 10^5\n1 <= K <= 2 * 10^5",
                examples=[{"input": "4 2", "output": "5"}],
                reference_solution=(
                    "MOD = 10 ** 9 + 7\n\n"
                    "def solve() -> None:\n"
                    "    n, k = map(int, input().split())\n"
                    "    dp = [0] * (n + 1)\n"
                    "    pref = [0] * (n + 2)\n"
                    "    dp[0] = 1\n"
                    "    pref[1] = 1\n"
                    "    for i in range(1, n + 1):\n"
                    "        left = max(0, i - k)\n"
                    "        dp[i] = (pref[i] - pref[left]) % MOD\n"
                    "        pref[i + 1] = (pref[i] + dp[i]) % MOD\n"
                    "    print(dp[n])\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if any(token in key for token in ("累積和", "いもす")):
            return _array_template(
                statement=(
                    "長さ N の整数列 A と Q 個の区間 [L, R] が与えられる。"
                    " 各区間について Ai..Aj の総和を求めよ。"
                ),
                input_format="1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に L R (1-indexed)。",
                output_format="各問い合わせの区間和を 1 行ずつ出力する。",
                constraints="1 <= N, Q <= 2 * 10^5\n|Ai| <= 10^9",
                examples=[
                    {"input": "5 3\n1 2 3 4 5\n1 3\n2 5\n4 4", "output": "6\n14\n4"},
                ],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, q = map(int, input().split())\n"
                    "    a = list(map(int, input().split()))\n"
                    "    prefix = [0]\n"
                    "    for value in a:\n"
                    "        prefix.append(prefix[-1] + value)\n"
                    "    out = []\n"
                    "    for _ in range(q):\n"
                    "        l, r = map(int, input().split())\n"
                    "        out.append(str(prefix[r] - prefix[l - 1]))\n"
                    "    sys.stdout.write('\\n'.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "二分探索" in key:
            return _array_template(
                statement=(
                    "昇順に並んだ長さ N の整数列 A と Q 個の値 x が与えられる。"
                    " 各 x について、A の中で x 以上となる最初の位置を 1-indexed で求め、"
                    " 存在しない場合は -1 を出力せよ。"
                ),
                input_format="1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に x。",
                output_format="各問い合わせの答えを 1 行ずつ出力する。",
                constraints="1 <= N, Q <= 2 * 10^5\nA は昇順",
                examples=[
                    {"input": "5 3\n1 3 5 8 13\n4\n13\n20", "output": "3\n5\n-1"},
                ],
                reference_solution=(
                    "from bisect import bisect_left\n\n"
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, q = map(int, input().split())\n"
                    "    a = list(map(int, input().split()))\n"
                    "    out = []\n"
                    "    for _ in range(q):\n"
                    "        x = int(input())\n"
                    "        idx = bisect_left(a, x)\n"
                    "        out.append(str(idx + 1) if idx < n else '-1')\n"
                    "    sys.stdout.write('\\n'.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-004":
            return _array_template(
                statement=(
                    "N 頂点 M 辺の無向グラフが与えられる。"
                    " 深さ優先探索を用いて、頂点 1 から到達できる頂点数を求めよ。"
                ),
                input_format="1 行目に N M。\n続く M 行に辺 u v。",
                output_format="頂点 1 から到達できる頂点数を出力する。",
                constraints="1 <= N, M <= 2 * 10^5",
                examples=[{"input": "5 3\n1 2\n2 3\n4 5", "output": "3"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    sys.setrecursionlimit(10 ** 7)\n"
                    "    input = sys.stdin.readline\n"
                    "    n, m = map(int, input().split())\n"
                    "    graph = [[] for _ in range(n)]\n"
                    "    for _ in range(m):\n"
                    "        u, v = map(int, input().split())\n"
                    "        u -= 1\n"
                    "        v -= 1\n"
                    "        graph[u].append(v)\n"
                    "        graph[v].append(u)\n"
                    "    seen = [False] * n\n"
                    "    def dfs(node: int) -> int:\n"
                    "        seen[node] = True\n"
                    "        total = 1\n"
                    "        for nxt in graph[node]:\n"
                    "            if not seen[nxt]:\n"
                    "                total += dfs(nxt)\n"
                    "        return total\n"
                    "    print(dfs(0))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-003":
            return _array_template(
                statement="下に凸な数列 A が与えられる。最小値を求めよ。",
                input_format="1 行目に N。\n2 行目に A1..AN。",
                output_format="最小値を出力する。",
                constraints="3 <= N <= 2 * 10^5\nA は下に凸",
                examples=[{"input": "7\n9 6 4 2 3 5 8", "output": "2"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    n = int(input())\n"
                    "    a = list(map(int, input().split()))\n"
                    "    left, right = 0, n - 1\n"
                    "    while right - left > 3:\n"
                    "        m1 = left + (right - left) // 3\n"
                    "        m2 = right - (right - left) // 3\n"
                    "        if a[m1] <= a[m2]:\n"
                    "            right = m2 - 1\n"
                    "        else:\n"
                    "            left = m1 + 1\n"
                    "    print(min(a[left:right + 1]))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-006":
            return _array_template(
                statement="長さ N の整数列 A と目標値 S が与えられる。bit 全探索で部分集合の和が S になるか判定せよ。",
                input_format="1 行目に N S。\n2 行目に A1..AN。",
                output_format="Yes / No を出力する。",
                constraints="1 <= N <= 20",
                examples=[{"input": "4 11\n2 5 9 4", "output": "Yes"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    n, s = map(int, input().split())\n"
                    "    a = list(map(int, input().split()))\n"
                    "    for mask in range(1 << n):\n"
                    "        total = 0\n"
                    "        for i in range(n):\n"
                    "            if mask >> i & 1:\n"
                    "                total += a[i]\n"
                    "        if total == s:\n"
                    "            print('Yes')\n"
                    "            return\n"
                    "    print('No')\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-007":
            return _array_template(
                statement=(
                    "N 頂点の完全グラフの重み行列が与えられる。"
                    " 頂点 1 から始めて残りを 1 回ずつ訪れる順列の中で、移動コスト合計の最小値を求めよ。"
                ),
                input_format="1 行目に N。\n続く N 行に重み行列。",
                output_format="最小コストを出力する。",
                constraints="2 <= N <= 8",
                examples=[{"input": "3\n0 2 5\n2 0 4\n5 4 0", "output": "6"}],
                reference_solution=(
                    "from itertools import permutations\n\n"
                    "def solve() -> None:\n"
                    "    n = int(input())\n"
                    "    cost = [list(map(int, input().split())) for _ in range(n)]\n"
                    "    ans = 10 ** 18\n"
                    "    for order in permutations(range(1, n)):\n"
                    "        total = 0\n"
                    "        prev = 0\n"
                    "        for nxt in order:\n"
                    "            total += cost[prev][nxt]\n"
                    "            prev = nxt\n"
                    "        ans = min(ans, total)\n"
                    "    print(ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-008":
            return _array_template(
                statement="長さ N の整数列 A と目標値 S が与えられる。半分全列挙で部分集合の和が S になるか判定せよ。",
                input_format="1 行目に N S。\n2 行目に A1..AN。",
                output_format="Yes / No を出力する。",
                constraints="1 <= N <= 40",
                examples=[{"input": "4 11\n2 5 9 4", "output": "Yes"}],
                reference_solution=(
                    "from bisect import bisect_left\n\n"
                    "def sums(values: list[int]) -> list[int]:\n"
                    "    out = [0]\n"
                    "    for value in values:\n"
                    "        out += [cur + value for cur in out]\n"
                    "    return out\n\n"
                    "def solve() -> None:\n"
                    "    n, s = map(int, input().split())\n"
                    "    a = list(map(int, input().split()))\n"
                    "    mid = n // 2\n"
                    "    left = sums(a[:mid])\n"
                    "    right = sorted(sums(a[mid:]))\n"
                    "    for value in left:\n"
                    "        need = s - value\n"
                    "        idx = bisect_left(right, need)\n"
                    "        if idx < len(right) and right[idx] == need:\n"
                    "            print('Yes')\n"
                    "            return\n"
                    "    print('No')\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-010":
            return _array_template(
                statement=(
                    "整数 N と目標値 T が与えられる。乱数 seed=0 を用いて 5000 回 0..N をランダムに試し、"
                    " T に最も近い値を出力せよ。差が同じなら小さい方を採用する。"
                ),
                input_format="1 行目に N T。",
                output_format="選ばれた値を出力する。",
                constraints="1 <= N <= 10^9",
                examples=[{"input": "10 7", "output": "7"}],
                reference_solution=(
                    "import random\n\n"
                    "def solve() -> None:\n"
                    "    n, target = map(int, input().split())\n"
                    "    random.seed(0)\n"
                    "    best = 0\n"
                    "    best_diff = abs(target)\n"
                    "    for _ in range(5000):\n"
                    "        cand = random.randint(0, n)\n"
                    "        diff = abs(cand - target)\n"
                    "        if diff < best_diff or (diff == best_diff and cand < best):\n"
                    "            best = cand\n"
                    "            best_diff = diff\n"
                    "    print(best)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-032":
            return _array_template(
                statement="N 頂点 M 辺の無向グラフが与えられる。二部グラフなら Yes、そうでなければ No を出力せよ。",
                input_format="1 行目に N M。\n続く M 行に辺 u v。",
                output_format="Yes / No を出力する。",
                constraints="1 <= N, M <= 2 * 10^5",
                examples=[{"input": "4 4\n1 2\n2 3\n3 4\n4 1", "output": "Yes"}],
                reference_solution=(
                    "from collections import deque\n\n"
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, m = map(int, input().split())\n"
                    "    graph = [[] for _ in range(n)]\n"
                    "    for _ in range(m):\n"
                    "        u, v = map(int, input().split())\n"
                    "        u -= 1\n"
                    "        v -= 1\n"
                    "        graph[u].append(v)\n"
                    "        graph[v].append(u)\n"
                    "    color = [-1] * n\n"
                    "    for start in range(n):\n"
                    "        if color[start] != -1:\n"
                    "            continue\n"
                    "        color[start] = 0\n"
                    "        dq = deque([start])\n"
                    "        while dq:\n"
                    "            node = dq.popleft()\n"
                    "            for nxt in graph[node]:\n"
                    "                if color[nxt] == -1:\n"
                    "                    color[nxt] = color[node] ^ 1\n"
                    "                    dq.append(nxt)\n"
                    "                elif color[nxt] == color[node]:\n"
                    "                    print('No')\n"
                    "                    return\n"
                    "    print('Yes')\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if any(token in key for token in ("DFS", "幅優先探索", "BFS", "二部グラフ")):
            return _array_template(
                statement=(
                    "N 頂点 M 辺の無向グラフが与えられる。"
                    " 頂点 1 から到達できる頂点数を求めよ。"
                ),
                input_format="1 行目に N M。\n続く M 行に辺 u v。",
                output_format="頂点 1 から到達できる頂点数を出力する。",
                constraints="1 <= N, M <= 2 * 10^5",
                examples=[
                    {"input": "5 3\n1 2\n2 3\n4 5", "output": "3"},
                ],
                reference_solution=(
                    "from collections import deque\n\n"
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, m = map(int, input().split())\n"
                    "    graph = [[] for _ in range(n)]\n"
                    "    for _ in range(m):\n"
                    "        u, v = map(int, input().split())\n"
                    "        u -= 1\n"
                    "        v -= 1\n"
                    "        graph[u].append(v)\n"
                    "        graph[v].append(u)\n"
                    "    seen = [False] * n\n"
                    "    queue = deque([0])\n"
                    "    seen[0] = True\n"
                    "    count = 0\n"
                    "    while queue:\n"
                    "        node = queue.popleft()\n"
                    "        count += 1\n"
                    "        for nxt in graph[node]:\n"
                    "            if seen[nxt]:\n"
                    "                continue\n"
                    "            seen[nxt] = True\n"
                    "            queue.append(nxt)\n"
                    "    print(count)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-024":
            return _array_template(
                statement=(
                    "N 頂点 M 辺の有向重み付きグラフと Q 個の問い合わせ s, t が与えられる。"
                    " 各問い合わせについて s から t への最短距離を求め、到達できなければ -1 を出力せよ。"
                ),
                input_format="1 行目に N M Q。\n続く M 行に u v w。\n続く Q 行に s t。",
                output_format="各問い合わせの答えを 1 行ずつ出力する。",
                constraints="1 <= N <= 300\n1 <= M <= 2 * 10^5\n1 <= Q <= 2 * 10^5",
                examples=[{"input": "3 3 2\n1 2 4\n2 3 5\n1 3 20\n1 3\n3 1", "output": "9\n-1"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, m, q = map(int, input().split())\n"
                    "    INF = 10 ** 18\n"
                    "    dist = [[INF] * n for _ in range(n)]\n"
                    "    for i in range(n):\n"
                    "        dist[i][i] = 0\n"
                    "    for _ in range(m):\n"
                    "        u, v, w = map(int, input().split())\n"
                    "        u -= 1\n"
                    "        v -= 1\n"
                    "        dist[u][v] = min(dist[u][v], w)\n"
                    "    for k in range(n):\n"
                    "        for i in range(n):\n"
                    "            dik = dist[i][k]\n"
                    "            if dik == INF:\n"
                    "                continue\n"
                    "            row_i = dist[i]\n"
                    "            row_k = dist[k]\n"
                    "            for j in range(n):\n"
                    "                nd = dik + row_k[j]\n"
                    "                if nd < row_i[j]:\n"
                    "                    row_i[j] = nd\n"
                    "    out = []\n"
                    "    for _ in range(q):\n"
                    "        s, t = map(int, input().split())\n"
                    "        ans = dist[s - 1][t - 1]\n"
                    "        out.append(str(-1 if ans == INF else ans))\n"
                    "    sys.stdout.write('\\n'.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-023":
            return _array_template(
                statement=(
                    "N 頂点 M 辺の有向重み付きグラフが与えられる。"
                    " 頂点 1 から各頂点への最短距離をベルマンフォード法で求め、頂点 N の距離を出力せよ。"
                    " 到達できなければ -1 を出力する。"
                ),
                input_format="1 行目に N M。\n続く M 行に u v w。",
                output_format="頂点 1 から頂点 N までの最短距離を出力する。",
                constraints="1 <= N <= 500\n1 <= M <= 2 * 10^5\n-10^9 <= w <= 10^9",
                examples=[{"input": "4 4\n1 2 3\n2 4 5\n1 3 10\n3 4 1", "output": "8"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, m = map(int, input().split())\n"
                    "    edges = [tuple(map(int, input().split())) for _ in range(m)]\n"
                    "    INF = 10 ** 18\n"
                    "    dist = [INF] * n\n"
                    "    dist[0] = 0\n"
                    "    for _ in range(n - 1):\n"
                    "        updated = False\n"
                    "        for u, v, w in edges:\n"
                    "            if dist[u - 1] == INF:\n"
                    "                continue\n"
                    "            nd = dist[u - 1] + w\n"
                    "            if nd < dist[v - 1]:\n"
                    "                dist[v - 1] = nd\n"
                    "                updated = True\n"
                    "        if not updated:\n"
                    "            break\n"
                    "    print(-1 if dist[-1] == INF else dist[-1])\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if any(token in key for token in ("ダイクストラ", "ベルマンフォード", "ワーシャルフロイド")):
            return _array_template(
                statement=(
                    "N 頂点 M 辺の有向重み付きグラフが与えられる。"
                    " 頂点 1 から頂点 N への最短距離を求め、到達できないなら -1 を出力せよ。"
                ),
                input_format="1 行目に N M。\n続く M 行に u v w。",
                output_format="頂点 1 から頂点 N までの最短距離を出力する。",
                constraints="1 <= N, M <= 2 * 10^5\n1 <= w <= 10^9",
                examples=[
                    {"input": "4 4\n1 2 3\n2 4 5\n1 3 10\n3 4 1", "output": "8"},
                ],
                reference_solution=(
                    "import heapq\n\n"
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, m = map(int, input().split())\n"
                    "    graph = [[] for _ in range(n)]\n"
                    "    for _ in range(m):\n"
                    "        u, v, w = map(int, input().split())\n"
                    "        graph[u - 1].append((v - 1, w))\n"
                    "    INF = 10 ** 30\n"
                    "    dist = [INF] * n\n"
                    "    dist[0] = 0\n"
                    "    heap = [(0, 0)]\n"
                    "    while heap:\n"
                    "        cost, node = heapq.heappop(heap)\n"
                    "        if cost != dist[node]:\n"
                    "            continue\n"
                    "        for nxt, w in graph[node]:\n"
                    "            nd = cost + w\n"
                    "            if nd < dist[nxt]:\n"
                    "                dist[nxt] = nd\n"
                    "                heapq.heappush(heap, (nd, nxt))\n"
                    "    print(-1 if dist[-1] == INF else dist[-1])\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "Union-Find" in key:
            return _array_template(
                statement=(
                    "N 個の頂点と Q 個の操作が与えられる。"
                    " `1 a b` は a と b を連結し、`2 a b` は同じ連結成分なら Yes そうでなければ No を出力せよ。"
                ),
                input_format="1 行目に N Q。\n続く Q 行に type a b。",
                output_format="type=2 の操作ごとに Yes / No を出力する。",
                constraints="1 <= N, Q <= 2 * 10^5",
                examples=[
                    {"input": "4 5\n1 1 2\n2 1 2\n2 1 3\n1 2 3\n2 1 3", "output": "Yes\nNo\nYes"},
                ],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, q = map(int, input().split())\n"
                    "    parent = list(range(n + 1))\n"
                    "    size = [1] * (n + 1)\n"
                    "    def find(x: int) -> int:\n"
                    "        while parent[x] != x:\n"
                    "            parent[x] = parent[parent[x]]\n"
                    "            x = parent[x]\n"
                    "        return x\n"
                    "    def unite(a: int, b: int) -> None:\n"
                    "        ra = find(a)\n"
                    "        rb = find(b)\n"
                    "        if ra == rb:\n"
                    "            return\n"
                    "        if size[ra] < size[rb]:\n"
                    "            ra, rb = rb, ra\n"
                    "        parent[rb] = ra\n"
                    "        size[ra] += size[rb]\n"
                    "    out = []\n"
                    "    for _ in range(q):\n"
                    "        t, a, b = map(int, input().split())\n"
                    "        if t == 1:\n"
                    "            unite(a, b)\n"
                    "        else:\n"
                    "            out.append('Yes' if find(a) == find(b) else 'No')\n"
                    "    sys.stdout.write('\\n'.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-009":
            return _array_template(
                statement=(
                    "長さ N の正整数列 A と整数 S が与えられる。"
                    " 総和が S 以上となる連続部分列のうち、長さの最小値を求めよ。存在しなければ 0 を出力せよ。"
                ),
                input_format="1 行目に N S。\n2 行目に A1..AN。",
                output_format="最小長を出力する。",
                constraints="1 <= N <= 2 * 10^5\n1 <= Ai, S <= 10^9",
                examples=[{"input": "6 11\n2 3 1 2 4 3", "output": "3"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    n, s = map(int, input().split())\n"
                    "    a = list(map(int, input().split()))\n"
                    "    ans = n + 1\n"
                    "    total = 0\n"
                    "    left = 0\n"
                    "    for right, value in enumerate(a):\n"
                    "        total += value\n"
                    "        while total >= s:\n"
                    "            ans = min(ans, right - left + 1)\n"
                    "            total -= a[left]\n"
                    "            left += 1\n"
                    "    print(0 if ans == n + 1 else ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if any(token in key for token in ("全探索", "bit全探索", "順列全探索", "半分全列挙", "三分探索", "尺取り法")):
            return _array_template(
                statement=(
                    "長さ N の整数列 A と目標値 S が与えられる。"
                    " 連続部分列または要素の選び方を工夫して、条件を満たすものが存在するか判定せよ。"
                ),
                input_format="1 行目に N S。\n2 行目に A1..AN。",
                output_format="条件を満たすなら Yes、そうでなければ No を出力する。",
                constraints="1 <= N <= 40",
                examples=[{"input": "4 11\n2 5 9 4", "output": "Yes"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    n, s = map(int, input().split())\n"
                    "    a = list(map(int, input().split()))\n"
                    "    for mask in range(1 << n):\n"
                    "        total = 0\n"
                    "        for i in range(n):\n"
                    "            if mask >> i & 1:\n"
                    "                total += a[i]\n"
                    "        if total == s:\n"
                    "            print('Yes')\n"
                    "            return\n"
                    "    print('No')\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if any(token in key for token in ("隣接リスト", "隣接行列")):
            return _array_template(
                statement="N 頂点 M 辺の無向グラフが与えられる。各頂点の次数を求めよ。",
                input_format="1 行目に N M。\n続く M 行に辺 u v。",
                output_format="1 行に N 個、各頂点の次数を出力する。",
                constraints="1 <= N, M <= 2 * 10^5",
                examples=[{"input": "4 3\n1 2\n2 3\n2 4", "output": "1 3 1 1"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, m = map(int, input().split())\n"
                    "    deg = [0] * n\n"
                    "    for _ in range(m):\n"
                    "        u, v = map(int, input().split())\n"
                    "        deg[u - 1] += 1\n"
                    "        deg[v - 1] += 1\n"
                    "    print(*deg)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "座標圧縮" in key:
            return _array_template(
                statement="長さ N の整数列 A を座標圧縮し、各要素の圧縮後の値を出力せよ。",
                input_format="1 行目に N。\n2 行目に A1..AN。",
                output_format="圧縮後の列を空白区切りで出力する。",
                constraints="1 <= N <= 2 * 10^5",
                examples=[{"input": "5\n100 50 1000 50 200", "output": "1 0 3 0 2"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    input()\n"
                    "    a = list(map(int, input().split()))\n"
                    "    values = {value: idx for idx, value in enumerate(sorted(set(a)))}\n"
                    "    print(*[values[value] for value in a])\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "エラトステネス" in key:
            return _array_template(
                statement="整数 N が与えられる。1 以上 N 以下の素数の個数を求めよ。",
                input_format="1 行目に N。",
                output_format="素数の個数を出力する。",
                constraints="2 <= N <= 10^7",
                examples=[{"input": "10", "output": "4"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    n = int(input())\n"
                    "    is_prime = [True] * (n + 1)\n"
                    "    if n >= 0:\n"
                    "        is_prime[0] = False\n"
                    "    if n >= 1:\n"
                    "        is_prime[1] = False\n"
                    "    p = 2\n"
                    "    while p * p <= n:\n"
                    "        if is_prime[p]:\n"
                    "            step = p * p\n"
                    "            for multiple in range(step, n + 1, p):\n"
                    "                is_prime[multiple] = False\n"
                    "        p += 1\n"
                    "    print(sum(is_prime))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "素因数分解" in key:
            return _array_template(
                statement="整数 N が与えられる。素因数分解し、`素因数 指数` を素因数の昇順で出力せよ。",
                input_format="1 行目に N。",
                output_format="各行に `p e` を出力する。",
                constraints="2 <= N <= 10^12",
                examples=[{"input": "72", "output": "2 3\n3 2"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    n = int(input())\n"
                    "    out = []\n"
                    "    d = 2\n"
                    "    while d * d <= n:\n"
                    "        if n % d == 0:\n"
                    "            cnt = 0\n"
                    "            while n % d == 0:\n"
                    "                n //= d\n"
                    "                cnt += 1\n"
                    "            out.append(f'{d} {cnt}')\n"
                    "        d += 1\n"
                    "    if n > 1:\n"
                    "        out.append(f'{n} 1')\n"
                    "    print('\\n'.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "拡張ユークリッド" in key:
            return _array_template(
                statement=(
                    "整数 a, b が与えられる。`ax + by = gcd(a, b)` を満たす整数 x, y の一組と `gcd(a, b)` を出力せよ。"
                ),
                input_format="1 行目に a b。",
                output_format="1 行に `g x y` を出力する。",
                constraints="1 <= a, b <= 10^18",
                examples=[{"input": "30 18", "output": "6 -1 2"}],
                reference_solution=(
                    "def extgcd(a: int, b: int) -> tuple[int, int, int]:\n"
                    "    if b == 0:\n"
                    "        return a, 1, 0\n"
                    "    g, x1, y1 = extgcd(b, a % b)\n"
                    "    x = y1\n"
                    "    y = x1 - (a // b) * y1\n"
                    "    return g, x, y\n\n"
                    "def solve() -> None:\n"
                    "    a, b = map(int, input().split())\n"
                    "    g, x, y = extgcd(a, b)\n"
                    "    print(g, x, y)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "モジュラ逆元" in key:
            return _array_template(
                statement="整数 a, m が与えられる。a の mod m における逆元が存在すれば最小の非負整数で出力し、存在しなければ -1 を出力せよ。",
                input_format="1 行目に a m。",
                output_format="逆元、存在しなければ -1 を出力する。",
                constraints="1 <= a, m <= 10^18",
                examples=[{"input": "3 11", "output": "4"}],
                reference_solution=(
                    "def extgcd(a: int, b: int) -> tuple[int, int, int]:\n"
                    "    if b == 0:\n"
                    "        return a, 1, 0\n"
                    "    g, x1, y1 = extgcd(b, a % b)\n"
                    "    return g, y1, x1 - (a // b) * y1\n\n"
                    "def solve() -> None:\n"
                    "    a, m = map(int, input().split())\n"
                    "    g, x, _ = extgcd(a, m)\n"
                    "    if g != 1:\n"
                    "        print(-1)\n"
                    "        return\n"
                    "    print(x % m)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "二項係数" in key:
            return _array_template(
                statement="整数 n, r, p が与えられる。p を法として nCr mod p を求めよ。p は素数とする。",
                input_format="1 行目に n r p。",
                output_format="nCr mod p を出力する。",
                constraints="0 <= r <= n <= 2 * 10^5\n2 <= p <= 10^9 + 7\np は素数",
                examples=[{"input": "5 2 1000000007", "output": "10"}],
                reference_solution=(
                    "def mod_pow(a: int, e: int, mod: int) -> int:\n"
                    "    ans = 1\n"
                    "    while e > 0:\n"
                    "        if e & 1:\n"
                    "            ans = ans * a % mod\n"
                    "        a = a * a % mod\n"
                    "        e >>= 1\n"
                    "    return ans\n\n"
                    "def solve() -> None:\n"
                    "    n, r, mod = map(int, input().split())\n"
                    "    if r < 0 or r > n:\n"
                    "        print(0)\n"
                    "        return\n"
                    "    fact = [1] * (n + 1)\n"
                    "    for i in range(1, n + 1):\n"
                    "        fact[i] = fact[i - 1] * i % mod\n"
                    "    inv_r = mod_pow(fact[r], mod - 2, mod)\n"
                    "    inv_nr = mod_pow(fact[n - r], mod - 2, mod)\n"
                    "    print(fact[n] * inv_r % mod * inv_nr % mod)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "包除原理" in key:
            return _array_template(
                statement="整数 N, A, B が与えられる。1 以上 N 以下で A または B の倍数である整数の個数を求めよ。",
                input_format="1 行目に N A B。",
                output_format="条件を満たす個数を出力する。",
                constraints="1 <= N, A, B <= 10^18",
                examples=[{"input": "20 4 6", "output": "6"}],
                reference_solution=(
                    "from math import gcd\n\n"
                    "def solve() -> None:\n"
                    "    n, a, b = map(int, input().split())\n"
                    "    lcm = a // gcd(a, b) * b\n"
                    "    ans = n // a + n // b - n // lcm\n"
                    "    print(ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "中国剰余定理" in key or "CRT" in key:
            return _array_template(
                statement=(
                    "整数 a, m, b, n が与えられる。`x ≡ a (mod m)` かつ `x ≡ b (mod n)` を満たす最小の非負整数 x を求めよ。"
                    " 存在しない場合は -1 を出力せよ。"
                ),
                input_format="1 行目に a m b n。",
                output_format="解があれば最小の非負整数 x、なければ -1 を出力する。",
                constraints="0 <= a < m <= 10^18\n0 <= b < n <= 10^18",
                examples=[{"input": "2 3 3 5", "output": "8"}],
                reference_solution=(
                    "def extgcd(a: int, b: int) -> tuple[int, int, int]:\n"
                    "    if b == 0:\n"
                    "        return a, 1, 0\n"
                    "    g, x1, y1 = extgcd(b, a % b)\n"
                    "    return g, y1, x1 - (a // b) * y1\n\n"
                    "def solve() -> None:\n"
                    "    a, m, b, n = map(int, input().split())\n"
                    "    g, x, _ = extgcd(m, n)\n"
                    "    diff = b - a\n"
                    "    if diff % g != 0:\n"
                    "        print(-1)\n"
                    "        return\n"
                    "    mod = n // g\n"
                    "    t = (diff // g * x) % mod\n"
                    "    lcm = m // g * n\n"
                    "    ans = (a + m * t) % lcm\n"
                    "    print(ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "行列累乗" in key:
            return _array_template(
                statement="整数 N が与えられる。フィボナッチ数列の N 項目 F_N を 10^9+7 で割った余りで求めよ。F_0=0, F_1=1 とする。",
                input_format="1 行目に N。",
                output_format="F_N mod 1000000007 を出力する。",
                constraints="0 <= N <= 10^18",
                examples=[{"input": "10", "output": "55"}],
                reference_solution=(
                    "MOD = 10 ** 9 + 7\n\n"
                    "def mul(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:\n"
                    "    return [\n"
                    "        [\n"
                    "            (a[i][0] * b[0][j] + a[i][1] * b[1][j]) % MOD\n"
                    "            for j in range(2)\n"
                    "        ]\n"
                    "        for i in range(2)\n"
                    "    ]\n\n"
                    "def solve() -> None:\n"
                    "    n = int(input())\n"
                    "    result = [[1, 0], [0, 1]]\n"
                    "    base = [[1, 1], [1, 0]]\n"
                    "    while n > 0:\n"
                    "        if n & 1:\n"
                    "            result = mul(result, base)\n"
                    "        base = mul(base, base)\n"
                    "        n >>= 1\n"
                    "    print(result[0][1])\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "約数列挙" in key:
            return _array_template(
                statement="整数 N が与えられる。N の正の約数を小さい順にすべて出力せよ。",
                input_format="1 行目に N。",
                output_format="正の約数を空白区切りで出力する。",
                constraints="1 <= N <= 10^12",
                examples=[{"input": "12", "output": "1 2 3 4 6 12"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    n = int(input())\n"
                    "    small = []\n"
                    "    large = []\n"
                    "    d = 1\n"
                    "    while d * d <= n:\n"
                    "        if n % d == 0:\n"
                    "            small.append(d)\n"
                    "            if d * d != n:\n"
                    "                large.append(n // d)\n"
                    "        d += 1\n"
                    "    print(*(small + large[::-1]))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-033":
            return _array_template(
                statement=(
                    "N 頂点 M 辺の無向グラフが与えられる。"
                    " すべての辺をちょうど 1 回ずつ通る道が存在するなら Yes、存在しなければ No を出力せよ。"
                ),
                input_format="1 行目に N M。\n続く M 行に辺 u v。",
                output_format="Yes / No を出力する。",
                constraints="1 <= N, M <= 2 * 10^5",
                examples=[{"input": "4 3\n1 2\n2 3\n3 4", "output": "Yes"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, m = map(int, input().split())\n"
                    "    parent = list(range(n))\n"
                    "    size = [1] * n\n"
                    "    degree = [0] * n\n\n"
                    "    def find(x: int) -> int:\n"
                    "        while parent[x] != x:\n"
                    "            parent[x] = parent[parent[x]]\n"
                    "            x = parent[x]\n"
                    "        return x\n\n"
                    "    def unite(a: int, b: int) -> None:\n"
                    "        ra = find(a)\n"
                    "        rb = find(b)\n"
                    "        if ra == rb:\n"
                    "            return\n"
                    "        if size[ra] < size[rb]:\n"
                    "            ra, rb = rb, ra\n"
                    "        parent[rb] = ra\n"
                    "        size[ra] += size[rb]\n\n"
                    "    for _ in range(m):\n"
                    "        u, v = map(int, input().split())\n"
                    "        u -= 1\n"
                    "        v -= 1\n"
                    "        degree[u] += 1\n"
                    "        degree[v] += 1\n"
                    "        unite(u, v)\n"
                    "    active = [i for i, deg in enumerate(degree) if deg > 0]\n"
                    "    if active:\n"
                    "        root = find(active[0])\n"
                    "        if any(find(node) != root for node in active):\n"
                    "            print('No')\n"
                    "            return\n"
                    "    odd = sum(deg % 2 for deg in degree)\n"
                    "    print('Yes' if odd in (0, 2) else 'No')\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-034":
            return _array_template(
                statement="根 1 の木が与えられる。深さ優先探索によるオイラーツアーの訪問順を出力せよ。",
                input_format="1 行目に N。\n続く N-1 行に辺 u v。",
                output_format="訪問順を空白区切りで出力する。",
                constraints="1 <= N <= 2 * 10^5",
                examples=[{"input": "4\n1 2\n1 3\n3 4", "output": "1 2 1 3 4 3 1"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    sys.setrecursionlimit(10 ** 7)\n"
                    "    input = sys.stdin.readline\n"
                    "    n = int(input())\n"
                    "    graph = [[] for _ in range(n)]\n"
                    "    for _ in range(n - 1):\n"
                    "        u, v = map(int, input().split())\n"
                    "        u -= 1\n"
                    "        v -= 1\n"
                    "        graph[u].append(v)\n"
                    "        graph[v].append(u)\n"
                    "    for adj in graph:\n"
                    "        adj.sort()\n"
                    "    order = []\n\n"
                    "    def dfs(node: int, parent: int) -> None:\n"
                    "        order.append(node + 1)\n"
                    "        for nxt in graph[node]:\n"
                    "            if nxt == parent:\n"
                    "                continue\n"
                    "            dfs(nxt, node)\n"
                    "            order.append(node + 1)\n\n"
                    "    dfs(0, -1)\n"
                    "    print(*order)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "オイラー" in key or "トーシェント" in key:
            return _array_template(
                statement="整数 N が与えられる。オイラーの φ 関数 φ(N) を求めよ。",
                input_format="1 行目に N。",
                output_format="φ(N) を出力する。",
                constraints="1 <= N <= 10^12",
                examples=[{"input": "12", "output": "4"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    n = int(input())\n"
                    "    x = n\n"
                    "    ans = n\n"
                    "    p = 2\n"
                    "    while p * p <= x:\n"
                    "        if x % p == 0:\n"
                    "            while x % p == 0:\n"
                    "                x //= p\n"
                    "            ans -= ans // p\n"
                    "        p += 1\n"
                    "    if x > 1:\n"
                    "        ans -= ans // x\n"
                    "    print(ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "メビウス" in key:
            return _array_template(
                statement="整数 N が与えられる。メビウス関数 μ(N) を求めよ。",
                input_format="1 行目に N。",
                output_format="μ(N) を出力する。",
                constraints="1 <= N <= 10^12",
                examples=[{"input": "30", "output": "-1"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    n = int(input())\n"
                    "    x = n\n"
                    "    cnt = 0\n"
                    "    p = 2\n"
                    "    while p * p <= x:\n"
                    "        if x % p == 0:\n"
                    "            exp = 0\n"
                    "            while x % p == 0:\n"
                    "                x //= p\n"
                    "                exp += 1\n"
                    "            if exp >= 2:\n"
                    "                print(0)\n"
                    "                return\n"
                    "            cnt += 1\n"
                    "        p += 1\n"
                    "    if x > 1:\n"
                    "        cnt += 1\n"
                    "    print(-1 if cnt % 2 else 1)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "繰り返し二乗法" in key:
            return _array_template(
                statement="整数 a, b, m が与えられる。a^b mod m を求めよ。",
                input_format="1 行目に a b m。",
                output_format="a^b mod m を出力する。",
                constraints="0 <= a, b <= 10^18\n1 <= m <= 10^9 + 7",
                examples=[{"input": "2 10 1000", "output": "24"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    a, b, m = map(int, input().split())\n"
                    "    ans = 1\n"
                    "    a %= m\n"
                    "    while b > 0:\n"
                    "        if b & 1:\n"
                    "            ans = ans * a % m\n"
                    "        a = a * a % m\n"
                    "        b >>= 1\n"
                    "    print(ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "転倒数" in key:
            return _array_template(
                statement="長さ N の整数列 A が与えられる。転倒数を求めよ。",
                input_format="1 行目に N。\n2 行目に A1..AN。",
                output_format="転倒数を出力する。",
                constraints="1 <= N <= 2 * 10^5",
                examples=[{"input": "4\n3 1 4 2", "output": "3"}],
                reference_solution=(
                    "def merge_count(arr: list[int]) -> tuple[list[int], int]:\n"
                    "    if len(arr) <= 1:\n"
                    "        return arr, 0\n"
                    "    mid = len(arr) // 2\n"
                    "    left, lc = merge_count(arr[:mid])\n"
                    "    right, rc = merge_count(arr[mid:])\n"
                    "    merged = []\n"
                    "    i = j = 0\n"
                    "    inv = lc + rc\n"
                    "    while i < len(left) and j < len(right):\n"
                    "        if left[i] <= right[j]:\n"
                    "            merged.append(left[i]); i += 1\n"
                    "        else:\n"
                    "            merged.append(right[j]); j += 1\n"
                    "            inv += len(left) - i\n"
                    "    merged.extend(left[i:])\n"
                    "    merged.extend(right[j:])\n"
                    "    return merged, inv\n\n"
                    "def solve() -> None:\n"
                    "    input()\n"
                    "    a = list(map(int, input().split()))\n"
                    "    print(merge_count(a)[1])\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "遅延評価セグメント木" in key:
            return _array_template(
                statement=(
                    "長さ N の整数列 A と Q 個の操作が与えられる。"
                    " `1 l r x` は区間 [l, r] の全要素に x を加算し、`2 l r` は区間 [l, r] の最小値を求めよ。"
                ),
                input_format="1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に操作。",
                output_format="type=2 のたびに区間最小値を 1 行ずつ出力する。",
                constraints="1 <= N, Q <= 2 * 10^5\n|Ai|, |x| <= 10^9",
                examples=[{"input": "5 5\n5 2 8 1 4\n2 1 5\n1 2 4 3\n2 1 3\n1 5 5 -2\n2 4 5", "output": "1\n5\n2"}],
                reference_solution=(
                    "class LazySegTree:\n"
                    "    def __init__(self, arr: list[int]) -> None:\n"
                    "        self.n = 1\n"
                    "        while self.n < len(arr):\n"
                    "            self.n <<= 1\n"
                    "        self.data = [10 ** 18] * (2 * self.n)\n"
                    "        self.lazy = [0] * (2 * self.n)\n"
                    "        for i, value in enumerate(arr):\n"
                    "            self.data[self.n + i] = value\n"
                    "        for i in range(self.n - 1, 0, -1):\n"
                    "            self.data[i] = min(self.data[i * 2], self.data[i * 2 + 1])\n\n"
                    "    def _push(self, idx: int) -> None:\n"
                    "        if self.lazy[idx] == 0:\n"
                    "            return\n"
                    "        for child in (idx * 2, idx * 2 + 1):\n"
                    "            self.data[child] += self.lazy[idx]\n"
                    "            self.lazy[child] += self.lazy[idx]\n"
                    "        self.lazy[idx] = 0\n\n"
                    "    def _range_add(self, left: int, right: int, value: int, idx: int, seg_l: int, seg_r: int) -> None:\n"
                    "        if right < seg_l or seg_r < left:\n"
                    "            return\n"
                    "        if left <= seg_l and seg_r <= right:\n"
                    "            self.data[idx] += value\n"
                    "            self.lazy[idx] += value\n"
                    "            return\n"
                    "        self._push(idx)\n"
                    "        mid = (seg_l + seg_r) // 2\n"
                    "        self._range_add(left, right, value, idx * 2, seg_l, mid)\n"
                    "        self._range_add(left, right, value, idx * 2 + 1, mid + 1, seg_r)\n"
                    "        self.data[idx] = min(self.data[idx * 2], self.data[idx * 2 + 1])\n\n"
                    "    def range_add(self, left: int, right: int, value: int) -> None:\n"
                    "        self._range_add(left, right, value, 1, 0, self.n - 1)\n\n"
                    "    def _range_min(self, left: int, right: int, idx: int, seg_l: int, seg_r: int) -> int:\n"
                    "        if right < seg_l or seg_r < left:\n"
                    "            return 10 ** 18\n"
                    "        if left <= seg_l and seg_r <= right:\n"
                    "            return self.data[idx]\n"
                    "        self._push(idx)\n"
                    "        mid = (seg_l + seg_r) // 2\n"
                    "        return min(\n"
                    "            self._range_min(left, right, idx * 2, seg_l, mid),\n"
                    "            self._range_min(left, right, idx * 2 + 1, mid + 1, seg_r),\n"
                    "        )\n\n"
                    "    def range_min(self, left: int, right: int) -> int:\n"
                    "        return self._range_min(left, right, 1, 0, self.n - 1)\n\n"
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, q = map(int, input().split())\n"
                    "    a = list(map(int, input().split()))\n"
                    "    seg = LazySegTree(a)\n"
                    "    out = []\n"
                    "    for _ in range(q):\n"
                    "        parts = list(map(int, input().split()))\n"
                    "        if parts[0] == 1:\n"
                    "            _, l, r, x = parts\n"
                    "            seg.range_add(l - 1, r - 1, x)\n"
                    "        else:\n"
                    "            _, l, r = parts\n"
                    "            out.append(str(seg.range_min(l - 1, r - 1)))\n"
                    "    sys.stdout.write('\\n'.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "Fenwick木" in key or "BIT/Fenwick木" in key:
            return _array_template(
                statement=(
                    "長さ N の整数列 A と Q 個の操作が与えられる。"
                    " `1 i x` は A_i に x を加算し、`2 l r` は区間 [l, r] の総和を求めよ。"
                ),
                input_format="1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に操作。",
                output_format="type=2 のたびに区間和を 1 行ずつ出力する。",
                constraints="1 <= N, Q <= 2 * 10^5\n|Ai|, |x| <= 10^9",
                examples=[{"input": "5 4\n1 2 3 4 5\n2 2 4\n1 3 10\n2 1 3\n2 3 5", "output": "9\n16\n22"}],
                reference_solution=(
                    "class Fenwick:\n"
                    "    def __init__(self, n: int) -> None:\n"
                    "        self.n = n\n"
                    "        self.data = [0] * (n + 1)\n\n"
                    "    def add(self, idx: int, value: int) -> None:\n"
                    "        while idx <= self.n:\n"
                    "            self.data[idx] += value\n"
                    "            idx += idx & -idx\n\n"
                    "    def sum(self, idx: int) -> int:\n"
                    "        total = 0\n"
                    "        while idx > 0:\n"
                    "            total += self.data[idx]\n"
                    "            idx -= idx & -idx\n"
                    "        return total\n\n"
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, q = map(int, input().split())\n"
                    "    a = list(map(int, input().split()))\n"
                    "    bit = Fenwick(n)\n"
                    "    for i, value in enumerate(a, start=1):\n"
                    "        bit.add(i, value)\n"
                    "    out = []\n"
                    "    for _ in range(q):\n"
                    "        parts = list(map(int, input().split()))\n"
                    "        if parts[0] == 1:\n"
                    "            _, i, x = parts\n"
                    "            bit.add(i, x)\n"
                    "        else:\n"
                    "            _, l, r = parts\n"
                    "            out.append(str(bit.sum(r) - bit.sum(l - 1)))\n"
                    "    sys.stdout.write('\\n'.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "スパーステーブル" in key or "RMQ" in key:
            return _array_template(
                statement="長さ N の整数列 A と Q 個の区間 [L, R] が与えられる。前処理を行い、各区間の最小値を求めよ。",
                input_format="1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に L R。",
                output_format="各問い合わせの最小値を 1 行ずつ出力する。",
                constraints="1 <= N, Q <= 2 * 10^5",
                examples=[{"input": "5 3\n5 2 8 1 4\n1 3\n2 5\n4 4", "output": "2\n1\n1"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, q = map(int, input().split())\n"
                    "    a = list(map(int, input().split()))\n"
                    "    log = [0] * (n + 1)\n"
                    "    for i in range(2, n + 1):\n"
                    "        log[i] = log[i // 2] + 1\n"
                    "    k = log[n] + 1\n"
                    "    st = [a[:]]\n"
                    "    j = 1\n"
                    "    while (1 << j) <= n:\n"
                    "        prev = st[-1]\n"
                    "        width = 1 << j\n"
                    "        half = width >> 1\n"
                    "        row = [0] * (n - width + 1)\n"
                    "        for i in range(n - width + 1):\n"
                    "            row[i] = min(prev[i], prev[i + half])\n"
                    "        st.append(row)\n"
                    "        j += 1\n"
                    "    out = []\n"
                    "    for _ in range(q):\n"
                    "        l, r = map(int, input().split())\n"
                    "        l -= 1\n"
                    "        r -= 1\n"
                    "        length = r - l + 1\n"
                    "        j = log[length]\n"
                    "        out.append(str(min(st[j][l], st[j][r - (1 << j) + 1])))\n"
                    "    sys.stdout.write('\\n'.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "セグメント木" in key:
            return _array_template(
                statement=(
                    "長さ N の整数列 A と Q 個の操作が与えられる。"
                    " `1 i x` は A_i を x に更新し、`2 l r` は区間 [l, r] の最小値を求めよ。"
                ),
                input_format="1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に操作。",
                output_format="type=2 のたびに区間最小値を 1 行ずつ出力する。",
                constraints="1 <= N, Q <= 2 * 10^5",
                examples=[{"input": "5 4\n5 2 8 1 4\n2 1 5\n1 3 0\n2 2 4\n2 3 3", "output": "1\n0\n0"}],
                reference_solution=(
                    "class SegTree:\n"
                    "    def __init__(self, arr: list[int]) -> None:\n"
                    "        self.n = 1\n"
                    "        while self.n < len(arr):\n"
                    "            self.n <<= 1\n"
                    "        self.data = [10 ** 18] * (2 * self.n)\n"
                    "        for i, value in enumerate(arr):\n"
                    "            self.data[self.n + i] = value\n"
                    "        for i in range(self.n - 1, 0, -1):\n"
                    "            self.data[i] = min(self.data[i * 2], self.data[i * 2 + 1])\n"
                    "    def update(self, idx: int, value: int) -> None:\n"
                    "        idx += self.n\n"
                    "        self.data[idx] = value\n"
                    "        idx >>= 1\n"
                    "        while idx:\n"
                    "            self.data[idx] = min(self.data[idx * 2], self.data[idx * 2 + 1])\n"
                    "            idx >>= 1\n\n"
                    "    def query(self, left: int, right: int) -> int:\n"
                    "        left += self.n\n"
                    "        right += self.n\n"
                    "        ans = 10 ** 18\n"
                    "        while left <= right:\n"
                    "            if left & 1:\n"
                    "                ans = min(ans, self.data[left]); left += 1\n"
                    "            if not (right & 1):\n"
                    "                ans = min(ans, self.data[right]); right -= 1\n"
                    "            left >>= 1\n"
                    "            right >>= 1\n"
                    "        return ans\n\n"
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, q = map(int, input().split())\n"
                    "    a = list(map(int, input().split()))\n"
                    "    seg = SegTree(a)\n"
                    "    out = []\n"
                    "    for _ in range(q):\n"
                    "        parts = list(map(int, input().split()))\n"
                    "        if parts[0] == 1:\n"
                    "            _, i, x = parts\n"
                    "            seg.update(i - 1, x)\n"
                    "        else:\n"
                    "            _, l, r = parts\n"
                    "            out.append(str(seg.query(l - 1, r - 1)))\n"
                    "    sys.stdout.write('\\n'.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if any(token in key for token in ("最近点対", "カラツバ法", "逆元を用いた分割統治", "平面走査と分割統治", "セグメント木上の分割統治", "重心分解")):
            return _array_template(
                statement="長さ N の整数列 A が与えられる。分割統治を用いて列全体の最小値を求めよ。",
                input_format="1 行目に N。\n2 行目に A1..AN。",
                output_format="最小値を出力する。",
                constraints="1 <= N <= 2 * 10^5",
                examples=[{"input": "5\n8 3 6 1 4", "output": "1"}],
                reference_solution=(
                    "def solve_range(a: list[int], left: int, right: int) -> int:\n"
                    "    if left == right:\n"
                    "        return a[left]\n"
                    "    mid = (left + right) // 2\n"
                    "    return min(solve_range(a, left, mid), solve_range(a, mid + 1, right))\n\n"
                    "def solve() -> None:\n"
                    "    input()\n"
                    "    a = list(map(int, input().split()))\n"
                    "    print(solve_range(a, 0, len(a) - 1))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if any(token in key for token in ("LIS", "最長増加部分列")):
            return _array_template(
                statement="長さ N の整数列 A が与えられる。最長増加部分列の長さを求めよ。",
                input_format="1 行目に N。\n2 行目に A1..AN。",
                output_format="LIS の長さを出力する。",
                constraints="1 <= N <= 2 * 10^5",
                examples=[{"input": "6\n3 1 4 1 5 9", "output": "4"}],
                reference_solution=(
                    "from bisect import bisect_left\n\n"
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    _ = int(input())\n"
                    "    a = list(map(int, input().split()))\n"
                    "    dp = []\n"
                    "    for value in a:\n"
                    "        i = bisect_left(dp, value)\n"
                    "        if i == len(dp):\n"
                    "            dp.append(value)\n"
                    "        else:\n"
                    "            dp[i] = value\n"
                    "    print(len(dp))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "編集距離" in key:
            return _array_template(
                statement="2 つの文字列 S, T が与えられる。編集距離を求めよ。",
                input_format="1 行目に S。\n2 行目に T。",
                output_format="編集距離を出力する。",
                constraints="1 <= |S|, |T| <= 2000",
                examples=[{"input": "kitten\nsitting", "output": "3"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    s = input().strip()\n"
                    "    t = input().strip()\n"
                    "    dp = [[0] * (len(t) + 1) for _ in range(len(s) + 1)]\n"
                    "    for i in range(len(s) + 1):\n"
                    "        dp[i][0] = i\n"
                    "    for j in range(len(t) + 1):\n"
                    "        dp[0][j] = j\n"
                    "    for i, ch in enumerate(s, start=1):\n"
                    "        for j, tch in enumerate(t, start=1):\n"
                    "            cost = 0 if ch == tch else 1\n"
                    "            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)\n"
                    "    print(dp[-1][-1])\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "LCS" in key:
            return _array_template(
                statement="2 つの文字列 S, T が与えられる。最長共通部分列の長さを求めよ。",
                input_format="1 行目に S。\n2 行目に T。",
                output_format="LCS の長さを出力する。",
                constraints="1 <= |S|, |T| <= 2000",
                examples=[{"input": "abcde\nace", "output": "3"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    s = input().strip()\n"
                    "    t = input().strip()\n"
                    "    dp = [0] * (len(t) + 1)\n"
                    "    for ch in s:\n"
                    "        prev = 0\n"
                    "        for j, tch in enumerate(t, start=1):\n"
                    "            saved = dp[j]\n"
                    "            if ch == tch:\n"
                    "                dp[j] = prev + 1\n"
                    "            else:\n"
                    "                dp[j] = max(dp[j], dp[j - 1])\n"
                    "            prev = saved\n"
                    "    print(dp[-1])\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-040":
            return _array_template(
                statement=(
                    "長さ N の正整数列 A が与えられる。"
                    " 隣り合う区間を順に併合するとき、併合コストを区間和とする。"
                    " 列全体を 1 つにする最小コストを求めよ。"
                ),
                input_format="1 行目に N。\n2 行目に A1..AN。",
                output_format="最小コストを出力する。",
                constraints="1 <= N <= 400\n1 <= Ai <= 10^9",
                examples=[{"input": "4\n4 1 3 2", "output": "20"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n = int(input())\n"
                    "    a = list(map(int, input().split()))\n"
                    "    prefix = [0]\n"
                    "    for value in a:\n"
                    "        prefix.append(prefix[-1] + value)\n"
                    "    dp = [[0] * n for _ in range(n)]\n"
                    "    for length in range(2, n + 1):\n"
                    "        for left in range(n - length + 1):\n"
                    "            right = left + length - 1\n"
                    "            total = prefix[right + 1] - prefix[left]\n"
                    "            best = 10 ** 30\n"
                    "            for mid in range(left, right):\n"
                    "                best = min(best, dp[left][mid] + dp[mid + 1][right] + total)\n"
                    "            dp[left][right] = best\n"
                    "    print(dp[0][n - 1])\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-041":
            return _array_template(
                statement="整数 N が与えられる。0 以上 N 以下で 10 進表記に数字 4 を含まない整数の個数を求めよ。",
                input_format="1 行目に N。",
                output_format="個数を出力する。",
                constraints="0 <= N <= 10^18",
                examples=[{"input": "20", "output": "19"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    n = input().strip()\n"
                    "    equal = 1\n"
                    "    less = 0\n"
                    "    for ch in n:\n"
                    "        digit = ord(ch) - ord('0')\n"
                    "        next_equal = 0\n"
                    "        next_less = less * 9\n"
                    "        for value in range(digit):\n"
                    "            if value != 4:\n"
                    "                next_less += equal\n"
                    "        if digit != 4:\n"
                    "            next_equal = equal\n"
                    "        equal = next_equal\n"
                    "        less = next_less\n"
                    "    print(equal + less)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-043":
            return _array_template(
                statement="木が与えられる。隣接頂点を同時に選ばないように頂点を選ぶとき、選べる頂点数の最大値を求めよ。",
                input_format="1 行目に N。\n続く N-1 行に辺 u v。",
                output_format="最大値を出力する。",
                constraints="1 <= N <= 2 * 10^5",
                examples=[{"input": "5\n1 2\n1 3\n3 4\n3 5", "output": "3"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    sys.setrecursionlimit(10 ** 7)\n"
                    "    input = sys.stdin.readline\n"
                    "    n = int(input())\n"
                    "    graph = [[] for _ in range(n)]\n"
                    "    for _ in range(n - 1):\n"
                    "        u, v = map(int, input().split())\n"
                    "        u -= 1\n"
                    "        v -= 1\n"
                    "        graph[u].append(v)\n"
                    "        graph[v].append(u)\n\n"
                    "    def dfs(node: int, parent: int) -> tuple[int, int]:\n"
                    "        take = 1\n"
                    "        skip = 0\n"
                    "        for nxt in graph[node]:\n"
                    "            if nxt == parent:\n"
                    "                continue\n"
                    "            child_take, child_skip = dfs(nxt, node)\n"
                    "            take += child_skip\n"
                    "            skip += max(child_take, child_skip)\n"
                    "        return take, skip\n\n"
                    "    take, skip = dfs(0, -1)\n"
                    "    print(max(take, skip))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-047":
            return _array_template(
                statement="コインを投げて表が出る確率 p が与えられる。初めて表が出るまでの期待手数を求めよ。",
                input_format="1 行目に p。",
                output_format="期待値を小数で出力する。",
                constraints="0 < p <= 1",
                examples=[{"input": "0.25", "output": "4.0"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    p = float(input())\n"
                    "    print(1.0 / p)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-048":
            return _array_template(
                statement=(
                    "石が N 個あり、1 回で 1 個または 3 個取れるゲームを考える。"
                    " 先手後手が最善を尽くすとして、先手が勝つなら First、負けるなら Second を出力せよ。"
                ),
                input_format="1 行目に N。",
                output_format="First / Second を出力する。",
                constraints="1 <= N <= 2 * 10^5",
                examples=[{"input": "2", "output": "Second"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    n = int(input())\n"
                    "    win = [False] * (max(4, n + 1))\n"
                    "    for stones in range(1, n + 1):\n"
                    "        for move in (1, 3):\n"
                    "            if stones >= move and not win[stones - move]:\n"
                    "                win[stones] = True\n"
                    "                break\n"
                    "    print('First' if win[n] else 'Second')\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if any(token in key for token in ("部分和", "ナップサック", "コイン", "DP")):
            return _array_template(
                statement=(
                    "N 個の正整数 A と目標値 S が与えられる。"
                    " いくつかを選んで合計をちょうど S にできるなら Yes、できなければ No を出力せよ。"
                ),
                input_format="1 行目に N S。\n2 行目に A1..AN。",
                output_format="Yes / No を出力する。",
                constraints="1 <= N <= 200\n1 <= S <= 2 * 10^5",
                examples=[{"input": "4 11\n2 5 9 4", "output": "Yes"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, s = map(int, input().split())\n"
                    "    a = list(map(int, input().split()))\n"
                    "    possible = [False] * (s + 1)\n"
                    "    possible[0] = True\n"
                    "    for value in a:\n"
                    "        for cur in range(s, value - 1, -1):\n"
                    "            if possible[cur - value]:\n"
                    "                possible[cur] = True\n"
                    "    print('Yes' if possible[s] else 'No')\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if any(token in key for token in ("GCD", "LCM", "素数", "約数", "CRT", "トーシェント", "メビウス")):
            return _array_template(
                statement="長さ N の整数列 A が与えられる。全要素の最大公約数を求めよ。",
                input_format="1 行目に N。\n2 行目に A1..AN。",
                output_format="最大公約数を出力する。",
                constraints="1 <= N <= 2 * 10^5\n1 <= Ai <= 10^9",
                examples=[{"input": "3\n12 18 30", "output": "6"}],
                reference_solution=(
                    "from math import gcd\n\n"
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    _ = int(input())\n"
                    "    a = list(map(int, input().split()))\n"
                    "    ans = 0\n"
                    "    for value in a:\n"
                    "        ans = gcd(ans, value)\n"
                    "    print(ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-076":
            return _array_template(
                statement=(
                    "文字列 S と N 個のパターン P_i が与えられる。"
                    " すべてのパターンについて、S の中での出現回数を求めよ。"
                ),
                input_format="1 行目に S。\n2 行目に N。\n続く N 行に P_i。",
                output_format="各パターンの出現回数を 1 行ずつ出力する。",
                constraints="1 <= |S| <= 2 * 10^5\n1 <= N <= 2 * 10^5\n各 P_i は英小文字",
                examples=[{"input": "abracadabra\n3\nabra\nra\na", "output": "2\n2\n5"}],
                reference_solution=(
                    "from collections import deque\n\n"
                    "class Node:\n"
                    "    def __init__(self) -> None:\n"
                    "        self.next = {}\n"
                    "        self.fail = 0\n"
                    "        self.out = []\n\n"
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    s = input().strip()\n"
                    "    n = int(input())\n"
                    "    trie = [Node()]\n"
                    "    pats = []\n"
                    "    for idx in range(n):\n"
                    "        pat = input().strip()\n"
                    "        pats.append(pat)\n"
                    "        node = 0\n"
                    "        for ch in pat:\n"
                    "            node = trie[node].next.setdefault(ch, len(trie))\n"
                    "            if node == len(trie):\n"
                    "                trie.append(Node())\n"
                    "        trie[node].out.append(idx)\n"
                    "    dq = deque()\n"
                    "    for ch, nxt in trie[0].next.items():\n"
                    "        dq.append(nxt)\n"
                    "    while dq:\n"
                    "        v = dq.popleft()\n"
                    "        for ch, nxt in trie[v].next.items():\n"
                    "            f = trie[v].fail\n"
                    "            while f and ch not in trie[f].next:\n"
                    "                f = trie[f].fail\n"
                    "            trie[nxt].fail = trie[f].next[ch] if ch in trie[f].next else 0\n"
                    "            trie[nxt].out.extend(trie[trie[nxt].fail].out)\n"
                    "            dq.append(nxt)\n"
                    "    ans = [0] * n\n"
                    "    node = 0\n"
                    "    for ch in s:\n"
                    "        while node and ch not in trie[node].next:\n"
                    "            node = trie[node].fail\n"
                    "        if ch in trie[node].next:\n"
                    "            node = trie[node].next[ch]\n"
                    "        for idx in trie[node].out:\n"
                    "            ans[idx] += 1\n"
                    "    print(*ans, sep='\\n')\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if any(token in key for token in ("KMP", "Z-algorithm", "ローリングハッシュ", "Aho-Corasick", "部分文字列")):
            return _array_template(
                statement="文字列 S と T が与えられる。T が S に何回現れるかを求めよ（重なりも数える）。",
                input_format="1 行目に S。\n2 行目に T。",
                output_format="出現回数を出力する。",
                constraints="1 <= |S| <= 2 * 10^5\n1 <= |T| <= |S|",
                examples=[{"input": "aaaa\naa", "output": "3"}],
                reference_solution=(
                    "def build_lps(pattern: str) -> list[int]:\n"
                    "    lps = [0] * len(pattern)\n"
                    "    length = 0\n"
                    "    i = 1\n"
                    "    while i < len(pattern):\n"
                    "        if pattern[i] == pattern[length]:\n"
                    "            length += 1\n"
                    "            lps[i] = length\n"
                    "            i += 1\n"
                    "        elif length:\n"
                    "            length = lps[length - 1]\n"
                    "        else:\n"
                    "            i += 1\n"
                    "    return lps\n\n"
                    "def solve() -> None:\n"
                    "    s = input().strip()\n"
                    "    t = input().strip()\n"
                    "    lps = build_lps(t)\n"
                    "    i = j = ans = 0\n"
                    "    while i < len(s):\n"
                    "        if s[i] == t[j]:\n"
                    "            i += 1\n"
                    "            j += 1\n"
                    "            if j == len(t):\n"
                    "                ans += 1\n"
                    "                j = lps[j - 1]\n"
                    "        elif j:\n"
                    "            j = lps[j - 1]\n"
                    "        else:\n"
                    "            i += 1\n"
                    "    print(ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "トライ" in key:
            return _array_template(
                statement="N 個の単語と Q 個の接頭辞が与えられる。各接頭辞について、その接頭辞を持つ単語数を求めよ。",
                input_format="1 行目に N Q。\n続く N 行に単語。\n続く Q 行に接頭辞。",
                output_format="各接頭辞ごとに単語数を 1 行ずつ出力する。",
                constraints="1 <= N, Q <= 2 * 10^5\n文字列は英小文字",
                examples=[{"input": "3 2\napple\napp\nbanana\napp\nba", "output": "2\n1"}],
                reference_solution=(
                    "class Node:\n"
                    "    __slots__ = ('children', 'count')\n"
                    "    def __init__(self) -> None:\n"
                    "        self.children = {}\n"
                    "        self.count = 0\n\n"
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, q = map(int, input().split())\n"
                    "    root = Node()\n"
                    "    for _ in range(n):\n"
                    "        word = input().strip()\n"
                    "        node = root\n"
                    "        for ch in word:\n"
                    "            node = node.children.setdefault(ch, Node())\n"
                    "            node.count += 1\n"
                    "    out = []\n"
                    "    for _ in range(q):\n"
                    "        prefix = input().strip()\n"
                    "        node = root\n"
                    "        ok = True\n"
                    "        for ch in prefix:\n"
                    "            if ch not in node.children:\n"
                    "                ok = False\n"
                    "                break\n"
                    "            node = node.children[ch]\n"
                    "        out.append(str(node.count if ok else 0))\n"
                    "    sys.stdout.write('\\n'.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-069":
            return _array_template(
                statement="文字列 S と T が与えられる。ローリングハッシュを用いて、T が S に何回現れるかを求めよ。",
                input_format="1 行目に S。\n2 行目に T。",
                output_format="出現回数を出力する。",
                constraints="1 <= |S| <= 2 * 10^5\n1 <= |T| <= |S|",
                examples=[{"input": "aaaa\naa", "output": "3"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    s = input().strip()\n"
                    "    t = input().strip()\n"
                    "    base = 911382323\n"
                    "    mod = 972663749\n"
                    "    n = len(s)\n"
                    "    m = len(t)\n"
                    "    power = [1] * (n + 1)\n"
                    "    prefix = [0] * (n + 1)\n"
                    "    for i, ch in enumerate(s, start=1):\n"
                    "        power[i] = power[i - 1] * base % mod\n"
                    "        prefix[i] = (prefix[i - 1] * base + ord(ch)) % mod\n"
                    "    target = 0\n"
                    "    for ch in t:\n"
                    "        target = (target * base + ord(ch)) % mod\n"
                    "    ans = 0\n"
                    "    for left in range(n - m + 1):\n"
                    "        right = left + m\n"
                    "        value = (prefix[right] - prefix[left] * power[m]) % mod\n"
                    "        if value == target and s[left:right] == t:\n"
                    "            ans += 1\n"
                    "    print(ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-070":
            return _array_template(
                statement="文字列 S と T が与えられる。KMP 法を用いて、T が S に何回現れるかを求めよ（重なりも数える）。",
                input_format="1 行目に S。\n2 行目に T。",
                output_format="出現回数を出力する。",
                constraints="1 <= |S| <= 2 * 10^5\n1 <= |T| <= |S|",
                examples=[{"input": "aaaa\naa", "output": "3"}],
                reference_solution=(
                    "def build_lps(pattern: str) -> list[int]:\n"
                    "    lps = [0] * len(pattern)\n"
                    "    length = 0\n"
                    "    i = 1\n"
                    "    while i < len(pattern):\n"
                    "        if pattern[i] == pattern[length]:\n"
                    "            length += 1\n"
                    "            lps[i] = length\n"
                    "            i += 1\n"
                    "        elif length:\n"
                    "            length = lps[length - 1]\n"
                    "        else:\n"
                    "            i += 1\n"
                    "    return lps\n\n"
                    "def solve() -> None:\n"
                    "    s = input().strip()\n"
                    "    t = input().strip()\n"
                    "    lps = build_lps(t)\n"
                    "    i = j = ans = 0\n"
                    "    while i < len(s):\n"
                    "        if s[i] == t[j]:\n"
                    "            i += 1\n"
                    "            j += 1\n"
                    "            if j == len(t):\n"
                    "                ans += 1\n"
                    "                j = lps[j - 1]\n"
                    "        elif j:\n"
                    "            j = lps[j - 1]\n"
                    "        else:\n"
                    "            i += 1\n"
                    "    print(ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-071":
            return _array_template(
                statement="文字列 S と T が与えられる。Z-algorithm を用いて、T が S に何回現れるかを求めよ（重なりも数える）。",
                input_format="1 行目に S。\n2 行目に T。",
                output_format="出現回数を出力する。",
                constraints="1 <= |S| <= 2 * 10^5\n1 <= |T| <= |S|",
                examples=[{"input": "aaaa\naa", "output": "3"}],
                reference_solution=(
                    "def z_algorithm(text: str) -> list[int]:\n"
                    "    z = [0] * len(text)\n"
                    "    left = right = 0\n"
                    "    for i in range(1, len(text)):\n"
                    "        if i <= right:\n"
                    "            z[i] = min(right - i + 1, z[i - left])\n"
                    "        while i + z[i] < len(text) and text[z[i]] == text[i + z[i]]:\n"
                    "            z[i] += 1\n"
                    "        if i + z[i] - 1 > right:\n"
                    "            left = i\n"
                    "            right = i + z[i] - 1\n"
                    "    z[0] = len(text)\n"
                    "    return z\n\n"
                    "def solve() -> None:\n"
                    "    s = input().strip()\n"
                    "    t = input().strip()\n"
                    "    merged = t + '$' + s\n"
                    "    z = z_algorithm(merged)\n"
                    "    ans = 0\n"
                    "    m = len(t)\n"
                    "    for value in z[m + 1:]:\n"
                    "        if value >= m:\n"
                    "            ans += 1\n"
                    "    print(ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-073":
            return _array_template(
                statement="文字列 S が与えられる。Suffix Array を構成し、各接尾辞の開始位置を 1-indexed で出力せよ。",
                input_format="1 行目に S。",
                output_format="開始位置を空白区切りで出力する。",
                constraints="1 <= |S| <= 2000",
                examples=[{"input": "banana", "output": "6 4 2 1 5 3"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    s = input().strip()\n"
                    "    order = sorted(range(len(s)), key=lambda i: s[i:])\n"
                    "    print(*[i + 1 for i in order])\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-077":
            return _array_template(
                statement="文字列 S が与えられる。異なる部分文字列の個数を求めよ。",
                input_format="1 行目に S。",
                output_format="異なる部分文字列の個数を出力する。",
                constraints="1 <= |S| <= 2000",
                examples=[{"input": "aba", "output": "5"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    s = input().strip()\n"
                    "    seen = set()\n"
                    "    for left in range(len(s)):\n"
                    "        for right in range(left + 1, len(s) + 1):\n"
                    "            seen.add(s[left:right])\n"
                    "    print(len(seen))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if "ランレングス圧縮" in key:
            return _array_template(
                statement="文字列 S をランレングス圧縮し、文字と個数を交互に出力せよ。",
                input_format="1 行目に S。",
                output_format="圧縮結果を 1 行で出力する。",
                constraints="1 <= |S| <= 2 * 10^5",
                examples=[{"input": "aaabbc", "output": "a3b2c1"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    s = input().strip()\n"
                    "    out = []\n"
                    "    i = 0\n"
                    "    while i < len(s):\n"
                    "        j = i\n"
                    "        while j < len(s) and s[j] == s[i]:\n"
                    "            j += 1\n"
                    "        out.append(f'{s[i]}{j - i}')\n"
                    "        i = j\n"
                    "    print(''.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if any(token in key for token in ("回文", "文字列")):
            return _array_template(
                statement="文字列 S が与えられる。S が回文なら Yes、そうでなければ No を出力せよ。",
                input_format="1 行目に文字列 S。",
                output_format="Yes / No を出力する。",
                constraints="1 <= |S| <= 2 * 10^5",
                examples=[{"input": "level", "output": "Yes"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    s = input().strip()\n"
                    "    print('Yes' if s == s[::-1] else 'No')\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-122":
            return _array_template(
                statement=(
                    "長さ 2^N の配列 A, B が与えられる。"
                    " OR 畳み込み C を `C[s] = Σ A[x]B[y] (x OR y = s)` で定義する。"
                    " すべての C[s] を求めよ。"
                ),
                input_format="1 行目に N。\n2 行目に A。\n3 行目に B。",
                output_format="C を空白区切りで出力する。",
                constraints="1 <= N <= 17\n0 <= Ai, Bi <= 10^9+7",
                examples=[{"input": "2\n1 2 3 4\n5 6 7 8", "output": "5 28 43 184"}],
                reference_solution=(
                    "def zeta(arr: list[int], n: int) -> None:\n"
                    "    for bit in range(n):\n"
                    "        for mask in range(1 << n):\n"
                    "            if not (mask >> bit & 1):\n"
                    "                arr[mask | (1 << bit)] += arr[mask]\n\n"
                    "def mobius(arr: list[int], n: int) -> None:\n"
                    "    for bit in range(n):\n"
                    "        for mask in range(1 << n):\n"
                    "            if not (mask >> bit & 1):\n"
                    "                arr[mask | (1 << bit)] -= arr[mask]\n\n"
                    "def solve() -> None:\n"
                    "    n = int(input())\n"
                    "    a = list(map(int, input().split()))\n"
                    "    b = list(map(int, input().split()))\n"
                    "    zeta(a, n)\n"
                    "    zeta(b, n)\n"
                    "    c = [x * y for x, y in zip(a, b, strict=False)]\n"
                    "    mobius(c, n)\n"
                    "    print(*c)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-115":
            return _array_template(
                statement=(
                    "非負整数 X と Q 個の操作が与えられる。"
                    " `1 k` は k bit を立てる、`2 k` は k bit を下ろす、`3 k` は k bit が立っていれば 1、そうでなければ 0 を出力せよ。"
                ),
                input_format="1 行目に X Q。\n続く Q 行に操作。",
                output_format="type=3 のたびに答えを 1 行ずつ出力する。",
                constraints="0 <= X < 2^60\n1 <= Q <= 2 * 10^5\n0 <= k < 60",
                examples=[{"input": "0 5\n1 2\n3 2\n2 2\n3 2\n3 1", "output": "1\n0\n0"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    x, q = map(int, input().split())\n"
                    "    out = []\n"
                    "    for _ in range(q):\n"
                    "        t, k = map(int, input().split())\n"
                    "        if t == 1:\n"
                    "            x |= 1 << k\n"
                    "        elif t == 2:\n"
                    "            x &= ~(1 << k)\n"
                    "        else:\n"
                    "            out.append(str((x >> k) & 1))\n"
                    "    print('\\n'.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-116":
            return _array_template(
                statement="長さ N の整数列 A が与えられる。すべての要素の XOR を求めよ。",
                input_format="1 行目に N。\n2 行目に A1..AN。",
                output_format="XOR を出力する。",
                constraints="1 <= N <= 2 * 10^5\n0 <= Ai < 2^60",
                examples=[{"input": "4\n1 2 3 4", "output": "4"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    input()\n"
                    "    ans = 0\n"
                    "    for value in map(int, input().split()):\n"
                    "        ans ^= value\n"
                    "    print(ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-118":
            return _array_template(
                statement="集合 A, B が与えられる。bit で表現し、和集合と共通部分の要素数を求めよ。",
                input_format="1 行目に NA NB。\n2 行目に A の要素。\n3 行目に B の要素。",
                output_format="1 行に `union_size intersection_size` を出力する。",
                constraints="0 <= 要素 < 60",
                examples=[{"input": "3 3\n1 3 5\n3 4 5", "output": "4 2"}],
                reference_solution=(
                    "def build_mask(values: list[int]) -> int:\n"
                    "    mask = 0\n"
                    "    for value in values:\n"
                    "        mask |= 1 << value\n"
                    "    return mask\n\n"
                    "def solve() -> None:\n"
                    "    na, nb = map(int, input().split())\n"
                    "    a = list(map(int, input().split())) if na else []\n"
                    "    b = list(map(int, input().split())) if nb else []\n"
                    "    ma = build_mask(a)\n"
                    "    mb = build_mask(b)\n"
                    "    print((ma | mb).bit_count(), (ma & mb).bit_count())\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-119":
            return _array_template(
                statement="長さ N の整数列 A が与えられる。全部分集合の和を小さい順に出力せよ。",
                input_format="1 行目に N。\n2 行目に A1..AN。",
                output_format="部分集合和を空白区切りで出力する。",
                constraints="1 <= N <= 20",
                examples=[{"input": "2\n1 3", "output": "0 1 3 4"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    n = int(input())\n"
                    "    a = list(map(int, input().split()))\n"
                    "    sums = []\n"
                    "    for mask in range(1 << n):\n"
                    "        total = 0\n"
                    "        for i in range(n):\n"
                    "            if mask >> i & 1:\n"
                    "                total += a[i]\n"
                    "        sums.append(total)\n"
                    "    sums.sort()\n"
                    "    print(*sums)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-120":
            return _array_template(
                statement="整数 X と Q 個の操作が与えられる。`1 k` は `X *= 2^k`、`2 k` は `X //= 2^k` とする。最後の X を出力せよ。",
                input_format="1 行目に X Q。\n続く Q 行に操作。",
                output_format="最終的な X を出力する。",
                constraints="0 <= X < 2^60\n1 <= Q <= 2 * 10^5",
                examples=[{"input": "3 3\n1 2\n2 1\n1 1", "output": "12"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    x, q = map(int, input().split())\n"
                    "    for _ in range(q):\n"
                    "        t, k = map(int, input().split())\n"
                    "        if t == 1:\n"
                    "            x <<= k\n"
                    "        else:\n"
                    "            x >>= k\n"
                    "    print(x)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-121":
            return _array_template(
                statement="非負整数 X が与えられる。最下位の立っているビットの値を出力せよ。X=0 のときは 0 を出力する。",
                input_format="1 行目に X。",
                output_format="答えを出力する。",
                constraints="0 <= X < 2^60",
                examples=[{"input": "12", "output": "4"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    x = int(input())\n"
                    "    print(x & -x if x else 0)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if any(token in key for token in ("ビット", "XOR", "ポップカウント")):
            return _array_template(
                statement="1 つの非負整数 X が与えられる。2 進表現で立っているビット数を求めよ。",
                input_format="1 行目に X。",
                output_format="ビット数を出力する。",
                constraints="0 <= X < 2^60",
                examples=[{"input": "13", "output": "3"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    x = int(input())\n"
                    "    print(x.bit_count())\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-123":
            return _array_template(
                statement="容量付き有向グラフが与えられる。頂点 1 から頂点 N への最大フローを Ford-Fulkerson 法で求めよ。",
                input_format="1 行目に N M。\n続く M 行に u v c。",
                output_format="最大フロー値を出力する。",
                constraints="2 <= N <= 100\n1 <= M <= 1000\n1 <= c <= 10^9",
                examples=[{"input": "4 5\n1 2 2\n1 3 1\n2 3 1\n2 4 1\n3 4 2", "output": "3"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    sys.setrecursionlimit(10 ** 7)\n"
                    "    input = sys.stdin.readline\n"
                    "    n, m = map(int, input().split())\n"
                    "    graph = [[] for _ in range(n)]\n\n"
                    "    def add_edge(u: int, v: int, cap: int) -> None:\n"
                    "        graph[u].append([v, cap, len(graph[v])])\n"
                    "        graph[v].append([u, 0, len(graph[u]) - 1])\n\n"
                    "    for _ in range(m):\n"
                    "        u, v, c = map(int, input().split())\n"
                    "        add_edge(u - 1, v - 1, c)\n\n"
                    "    def dfs(node: int, goal: int, flow: int, seen: list[bool]) -> int:\n"
                    "        if node == goal:\n"
                    "            return flow\n"
                    "        seen[node] = True\n"
                    "        for edge in graph[node]:\n"
                    "            nxt, cap, rev = edge\n"
                    "            if cap == 0 or seen[nxt]:\n"
                    "                continue\n"
                    "            pushed = dfs(nxt, goal, min(flow, cap), seen)\n"
                    "            if pushed:\n"
                    "                edge[1] -= pushed\n"
                    "                graph[nxt][rev][1] += pushed\n"
                    "                return pushed\n"
                    "        return 0\n\n"
                    "    ans = 0\n"
                    "    while True:\n"
                    "        pushed = dfs(0, n - 1, 10 ** 18, [False] * n)\n"
                    "        if pushed == 0:\n"
                    "            break\n"
                    "        ans += pushed\n"
                    "    print(ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-124":
            return _array_template(
                statement="容量付き有向グラフが与えられる。頂点 1 から頂点 N への最大フローを Dinic 法で求めよ。",
                input_format="1 行目に N M。\n続く M 行に u v c。",
                output_format="最大フロー値を出力する。",
                constraints="2 <= N <= 2 * 10^5\n1 <= M <= 2 * 10^5\n1 <= c <= 10^9",
                examples=[{"input": "4 5\n1 2 2\n1 3 1\n2 3 1\n2 4 1\n3 4 2", "output": "3"}],
                reference_solution=(
                    "from collections import deque\n\n"
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, m = map(int, input().split())\n"
                    "    graph = [[] for _ in range(n)]\n\n"
                    "    def add_edge(u: int, v: int, cap: int) -> None:\n"
                    "        graph[u].append([v, cap, len(graph[v])])\n"
                    "        graph[v].append([u, 0, len(graph[u]) - 1])\n\n"
                    "    for _ in range(m):\n"
                    "        u, v, c = map(int, input().split())\n"
                    "        add_edge(u - 1, v - 1, c)\n\n"
                    "    level = [0] * n\n"
                    "    it = [0] * n\n\n"
                    "    def bfs() -> bool:\n"
                    "        level[:] = [-1] * n\n"
                    "        dq = deque([0])\n"
                    "        level[0] = 0\n"
                    "        while dq:\n"
                    "            node = dq.popleft()\n"
                    "            for nxt, cap, _ in graph[node]:\n"
                    "                if cap > 0 and level[nxt] == -1:\n"
                    "                    level[nxt] = level[node] + 1\n"
                    "                    dq.append(nxt)\n"
                    "        return level[n - 1] != -1\n\n"
                    "    def dfs(node: int, flow: int) -> int:\n"
                    "        if node == n - 1:\n"
                    "            return flow\n"
                    "        while it[node] < len(graph[node]):\n"
                    "            edge = graph[node][it[node]]\n"
                    "            nxt, cap, rev = edge\n"
                    "            if cap > 0 and level[node] + 1 == level[nxt]:\n"
                    "                pushed = dfs(nxt, min(flow, cap))\n"
                    "                if pushed:\n"
                    "                    edge[1] -= pushed\n"
                    "                    graph[nxt][rev][1] += pushed\n"
                    "                    return pushed\n"
                    "            it[node] += 1\n"
                    "        return 0\n\n"
                    "    ans = 0\n"
                    "    while bfs():\n"
                    "        it[:] = [0] * n\n"
                    "        while True:\n"
                    "            pushed = dfs(0, 10 ** 18)\n"
                    "            if pushed == 0:\n"
                    "                break\n"
                    "            ans += pushed\n"
                    "    print(ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-125":
            return _array_template(
                statement="容量付き有向グラフが与えられる。頂点 1 から頂点 N への最小カット値を求めよ。",
                input_format="1 行目に N M。\n続く M 行に u v c。",
                output_format="最小カット値を出力する。",
                constraints="2 <= N <= 200\n1 <= M <= 2000\n1 <= c <= 10^9",
                examples=[{"input": "4 5\n1 2 2\n1 3 1\n2 3 1\n2 4 1\n3 4 2", "output": "3"}],
                reference_solution=(
                    "from collections import deque\n\n"
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, m = map(int, input().split())\n"
                    "    graph = [[] for _ in range(n)]\n\n"
                    "    def add_edge(u: int, v: int, cap: int) -> None:\n"
                    "        graph[u].append([v, cap, len(graph[v])])\n"
                    "        graph[v].append([u, 0, len(graph[u]) - 1])\n\n"
                    "    for _ in range(m):\n"
                    "        u, v, c = map(int, input().split())\n"
                    "        add_edge(u - 1, v - 1, c)\n\n"
                    "    level = [0] * n\n"
                    "    it = [0] * n\n\n"
                    "    def bfs() -> bool:\n"
                    "        level[:] = [-1] * n\n"
                    "        dq = deque([0])\n"
                    "        level[0] = 0\n"
                    "        while dq:\n"
                    "            node = dq.popleft()\n"
                    "            for nxt, cap, _ in graph[node]:\n"
                    "                if cap > 0 and level[nxt] == -1:\n"
                    "                    level[nxt] = level[node] + 1\n"
                    "                    dq.append(nxt)\n"
                    "        return level[n - 1] != -1\n\n"
                    "    def dfs(node: int, flow: int) -> int:\n"
                    "        if node == n - 1:\n"
                    "            return flow\n"
                    "        while it[node] < len(graph[node]):\n"
                    "            edge = graph[node][it[node]]\n"
                    "            nxt, cap, rev = edge\n"
                    "            if cap > 0 and level[node] + 1 == level[nxt]:\n"
                    "                pushed = dfs(nxt, min(flow, cap))\n"
                    "                if pushed:\n"
                    "                    edge[1] -= pushed\n"
                    "                    graph[nxt][rev][1] += pushed\n"
                    "                    return pushed\n"
                    "            it[node] += 1\n"
                    "        return 0\n\n"
                    "    ans = 0\n"
                    "    while bfs():\n"
                    "        it[:] = [0] * n\n"
                    "        while True:\n"
                    "            pushed = dfs(0, 10 ** 18)\n"
                    "            if pushed == 0:\n"
                    "                break\n"
                    "            ans += pushed\n"
                    "    print(ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-011":
            return _array_template(
                statement="長さ N の整数列 A が与えられる。バブルソートで昇順に並べ替えて出力せよ。",
                input_format="1 行目に N。\n2 行目に A1..AN。",
                output_format="昇順の列を空白区切りで出力する。",
                constraints="1 <= N <= 2000",
                examples=[{"input": "5\n4 1 5 2 3", "output": "1 2 3 4 5"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    n = int(input())\n"
                    "    a = list(map(int, input().split()))\n"
                    "    for i in range(n):\n"
                    "        for j in range(n - 1 - i):\n"
                    "            if a[j] > a[j + 1]:\n"
                    "                a[j], a[j + 1] = a[j + 1], a[j]\n"
                    "    print(*a)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-012":
            return _array_template(
                statement="長さ N の整数列 A が与えられる。選択ソートで昇順に並べ替えて出力せよ。",
                input_format="1 行目に N。\n2 行目に A1..AN。",
                output_format="昇順の列を空白区切りで出力する。",
                constraints="1 <= N <= 2000",
                examples=[{"input": "5\n4 1 5 2 3", "output": "1 2 3 4 5"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    n = int(input())\n"
                    "    a = list(map(int, input().split()))\n"
                    "    for i in range(n):\n"
                    "        best = i\n"
                    "        for j in range(i + 1, n):\n"
                    "            if a[j] < a[best]:\n"
                    "                best = j\n"
                    "        a[i], a[best] = a[best], a[i]\n"
                    "    print(*a)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-013":
            return _array_template(
                statement="長さ N の整数列 A が与えられる。挿入ソートで昇順に並べ替えて出力せよ。",
                input_format="1 行目に N。\n2 行目に A1..AN。",
                output_format="昇順の列を空白区切りで出力する。",
                constraints="1 <= N <= 2000",
                examples=[{"input": "5\n4 1 5 2 3", "output": "1 2 3 4 5"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    n = int(input())\n"
                    "    a = list(map(int, input().split()))\n"
                    "    for i in range(1, n):\n"
                    "        value = a[i]\n"
                    "        j = i - 1\n"
                    "        while j >= 0 and a[j] > value:\n"
                    "            a[j + 1] = a[j]\n"
                    "            j -= 1\n"
                    "        a[j + 1] = value\n"
                    "    print(*a)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-014":
            return _array_template(
                statement="長さ N の整数列 A が与えられる。マージソートで昇順に並べ替えて出力せよ。",
                input_format="1 行目に N。\n2 行目に A1..AN。",
                output_format="昇順の列を空白区切りで出力する。",
                constraints="1 <= N <= 2 * 10^5",
                examples=[{"input": "5\n4 1 5 2 3", "output": "1 2 3 4 5"}],
                reference_solution=(
                    "def merge_sort(arr: list[int]) -> list[int]:\n"
                    "    if len(arr) <= 1:\n"
                    "        return arr\n"
                    "    mid = len(arr) // 2\n"
                    "    left = merge_sort(arr[:mid])\n"
                    "    right = merge_sort(arr[mid:])\n"
                    "    out = []\n"
                    "    i = j = 0\n"
                    "    while i < len(left) and j < len(right):\n"
                    "        if left[i] <= right[j]:\n"
                    "            out.append(left[i]); i += 1\n"
                    "        else:\n"
                    "            out.append(right[j]); j += 1\n"
                    "    out.extend(left[i:])\n"
                    "    out.extend(right[j:])\n"
                    "    return out\n\n"
                    "def solve() -> None:\n"
                    "    input()\n"
                    "    a = list(map(int, input().split()))\n"
                    "    print(*merge_sort(a))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-015":
            return _array_template(
                statement="長さ N の整数列 A が与えられる。クイックソートで昇順に並べ替えて出力せよ。",
                input_format="1 行目に N。\n2 行目に A1..AN。",
                output_format="昇順の列を空白区切りで出力する。",
                constraints="1 <= N <= 2 * 10^5",
                examples=[{"input": "5\n4 1 5 2 3", "output": "1 2 3 4 5"}],
                reference_solution=(
                    "def quick_sort(arr: list[int]) -> list[int]:\n"
                    "    if len(arr) <= 1:\n"
                    "        return arr\n"
                    "    pivot = arr[len(arr) // 2]\n"
                    "    left = [x for x in arr if x < pivot]\n"
                    "    mid = [x for x in arr if x == pivot]\n"
                    "    right = [x for x in arr if x > pivot]\n"
                    "    return quick_sort(left) + mid + quick_sort(right)\n\n"
                    "def solve() -> None:\n"
                    "    input()\n"
                    "    a = list(map(int, input().split()))\n"
                    "    print(*quick_sort(a))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-016":
            return _array_template(
                statement="長さ N の整数列 A が与えられる。ヒープソートで昇順に並べ替えて出力せよ。",
                input_format="1 行目に N。\n2 行目に A1..AN。",
                output_format="昇順の列を空白区切りで出力する。",
                constraints="1 <= N <= 2 * 10^5",
                examples=[{"input": "5\n4 1 5 2 3", "output": "1 2 3 4 5"}],
                reference_solution=(
                    "import heapq\n\n"
                    "def solve() -> None:\n"
                    "    input()\n"
                    "    heap = list(map(int, input().split()))\n"
                    "    heapq.heapify(heap)\n"
                    "    out = [heapq.heappop(heap) for _ in range(len(heap))]\n"
                    "    print(*out)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-017":
            return _array_template(
                statement="長さ N の非負整数列 A が与えられる。計数ソートで昇順に並べ替えて出力せよ。",
                input_format="1 行目に N。\n2 行目に A1..AN。",
                output_format="昇順の列を空白区切りで出力する。",
                constraints="1 <= N <= 2 * 10^5\n0 <= Ai <= 10^6",
                examples=[{"input": "5\n4 1 5 2 3", "output": "1 2 3 4 5"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    input()\n"
                    "    a = list(map(int, input().split()))\n"
                    "    limit = max(a, default=0)\n"
                    "    cnt = [0] * (limit + 1)\n"
                    "    for value in a:\n"
                    "        cnt[value] += 1\n"
                    "    out = []\n"
                    "    for value, freq in enumerate(cnt):\n"
                    "        out.extend([value] * freq)\n"
                    "    print(*out)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-018":
            return _array_template(
                statement="長さ N の非負整数列 A が与えられる。基数ソートで昇順に並べ替えて出力せよ。",
                input_format="1 行目に N。\n2 行目に A1..AN。",
                output_format="昇順の列を空白区切りで出力する。",
                constraints="1 <= N <= 2 * 10^5\n0 <= Ai <= 10^9",
                examples=[{"input": "5\n4 1 5 2 3", "output": "1 2 3 4 5"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    input()\n"
                    "    a = list(map(int, input().split()))\n"
                    "    exp = 1\n"
                    "    while True:\n"
                    "        buckets = [[] for _ in range(10)]\n"
                    "        done = True\n"
                    "        for value in a:\n"
                    "            digit = (value // exp) % 10\n"
                    "            buckets[digit].append(value)\n"
                    "            if value // exp >= 10:\n"
                    "                done = False\n"
                    "        a = [value for bucket in buckets for value in bucket]\n"
                    "        if done:\n"
                    "            break\n"
                    "        exp *= 10\n"
                    "    print(*a)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-027":
            return _array_template(
                statement=(
                    "N 頂点 M 辺の有向非巡回グラフが与えられる。"
                    " 辞書順最小のトポロジカル順序を 1 つ出力せよ。"
                ),
                input_format="1 行目に N M。\n続く M 行に辺 u v。",
                output_format="トポロジカル順序を空白区切りで出力する。",
                constraints="1 <= N, M <= 2 * 10^5",
                examples=[{"input": "4 3\n1 2\n1 3\n3 4", "output": "1 2 3 4"}],
                reference_solution=(
                    "import heapq\n\n"
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, m = map(int, input().split())\n"
                    "    graph = [[] for _ in range(n)]\n"
                    "    indeg = [0] * n\n"
                    "    for _ in range(m):\n"
                    "        u, v = map(int, input().split())\n"
                    "        u -= 1\n"
                    "        v -= 1\n"
                    "        graph[u].append(v)\n"
                    "        indeg[v] += 1\n"
                    "    pq = [i for i, deg in enumerate(indeg) if deg == 0]\n"
                    "    heapq.heapify(pq)\n"
                    "    order = []\n"
                    "    while pq:\n"
                    "        node = heapq.heappop(pq)\n"
                    "        order.append(node + 1)\n"
                    "        for nxt in graph[node]:\n"
                    "            indeg[nxt] -= 1\n"
                    "            if indeg[nxt] == 0:\n"
                    "                heapq.heappush(pq, nxt)\n"
                    "    print(*order)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if any(token in key for token in ("ソート", "ヒープ")):
            return _array_template(
                statement="長さ N の整数列 A が与えられる。A を昇順に並べ替えて出力せよ。",
                input_format="1 行目に N。\n2 行目に A1..AN。",
                output_format="昇順に並べた列を空白区切りで出力する。",
                constraints="1 <= N <= 2 * 10^5",
                examples=[{"input": "5\n4 1 5 2 3", "output": "1 2 3 4 5"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    input()\n"
                    "    a = list(map(int, input().split()))\n"
                    "    a.sort()\n"
                    "    print(*a)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.category == "貪欲法":
            return _array_template(
                statement=(
                    "N 個の区間 [Li, Ri] が与えられる。互いに重ならないように選べる区間数の最大値を求めよ。"
                ),
                input_format="1 行目に N。\n続く N 行に Li Ri。",
                output_format="選べる区間数の最大値を出力する。",
                constraints="1 <= N <= 2 * 10^5",
                examples=[{"input": "4\n1 3\n2 5\n4 6\n6 7", "output": "3"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n = int(input())\n"
                    "    intervals = [tuple(map(int, input().split())) for _ in range(n)]\n"
                    "    intervals.sort(key=lambda item: item[1])\n"
                    "    ans = 0\n"
                    "    current_end = -10 ** 18\n"
                    "    for left, right in intervals:\n"
                    "        if left < current_end:\n"
                    "            continue\n"
                    "        ans += 1\n"
                    "        current_end = right\n"
                    "    print(ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.category == "幾何":
            return _array_template(
                statement="平面上の 3 点 A, B, C が与えられる。ベクトル AB と AC の外積を求めよ。",
                input_format="1 行目に ax ay bx by cx cy。",
                output_format="外積の値を出力する。",
                constraints="座標は整数",
                examples=[{"input": "0 0 1 0 0 1", "output": "1"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    ax, ay, bx, by, cx, cy = map(int, input().split())\n"
                    "    abx, aby = bx - ax, by - ay\n"
                    "    acx, acy = cx - ax, cy - ay\n"
                    "    print(abx * acy - aby * acx)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.category == "フロー・マッチング":
            return _array_template(
                statement="左側 N 頂点、右側 M 頂点の二部グラフが与えられる。最大マッチング数を求めよ。",
                input_format="1 行目に N M E。\n続く E 行に u v。",
                output_format="最大マッチング数を出力する。",
                constraints="1 <= N, M <= 200\n1 <= E <= 2 * 10^4",
                examples=[{"input": "2 2 3\n1 1\n1 2\n2 2", "output": "2"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, m, e = map(int, input().split())\n"
                    "    graph = [[] for _ in range(n)]\n"
                    "    for _ in range(e):\n"
                    "        u, v = map(int, input().split())\n"
                    "        graph[u - 1].append(v - 1)\n"
                    "    match_to = [-1] * m\n"
                    "    def dfs(v: int, seen: list[bool]) -> bool:\n"
                    "        for nxt in graph[v]:\n"
                    "            if seen[nxt]:\n"
                    "                continue\n"
                    "            seen[nxt] = True\n"
                    "            if match_to[nxt] == -1 or dfs(match_to[nxt], seen):\n"
                    "                match_to[nxt] = v\n"
                    "                return True\n"
                    "        return False\n"
                    "    ans = 0\n"
                    "    for v in range(n):\n"
                    "        if dfs(v, [False] * m):\n"
                    "            ans += 1\n"
                    "    print(ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.category == "探索":
            return _array_template(
                statement="長さ N の整数列 A と整数 x が与えられる。A に x が含まれるか判定せよ。",
                input_format="1 行目に N x。\n2 行目に A1..AN。",
                output_format="含まれるなら Yes、そうでなければ No。",
                constraints="1 <= N <= 2 * 10^5",
                examples=[{"input": "5 3\n1 4 3 7 9", "output": "Yes"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    n, x = map(int, input().split())\n"
                    "    a = list(map(int, input().split()))\n"
                    "    print('Yes' if x in a else 'No')\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-025":
            return _array_template(
                statement="重み付き無向連結グラフが与えられる。プリム法で最小全域木の重みを求めよ。",
                input_format="1 行目に N M。\n続く M 行に u v w。",
                output_format="最小全域木の重みを出力する。",
                constraints="1 <= N <= 2 * 10^5\nN-1 <= M <= 2 * 10^5",
                examples=[{"input": "4 5\n1 2 1\n1 3 4\n2 3 2\n2 4 5\n3 4 1", "output": "4"}],
                reference_solution=(
                    "import heapq\n\n"
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, m = map(int, input().split())\n"
                    "    graph = [[] for _ in range(n)]\n"
                    "    for _ in range(m):\n"
                    "        u, v, w = map(int, input().split())\n"
                    "        u -= 1\n"
                    "        v -= 1\n"
                    "        graph[u].append((w, v))\n"
                    "        graph[v].append((w, u))\n"
                    "    used = [False] * n\n"
                    "    pq = [(0, 0)]\n"
                    "    total = 0\n"
                    "    while pq:\n"
                    "        cost, node = heapq.heappop(pq)\n"
                    "        if used[node]:\n"
                    "            continue\n"
                    "        used[node] = True\n"
                    "        total += cost\n"
                    "        for edge_cost, nxt in graph[node]:\n"
                    "            if not used[nxt]:\n"
                    "                heapq.heappush(pq, (edge_cost, nxt))\n"
                    "    print(total)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-026":
            return _array_template(
                statement="重み付き無向連結グラフが与えられる。クラスカル法で最小全域木の重みを求めよ。",
                input_format="1 行目に N M。\n続く M 行に u v w。",
                output_format="最小全域木の重みを出力する。",
                constraints="1 <= N <= 2 * 10^5\nN-1 <= M <= 2 * 10^5",
                examples=[{"input": "4 5\n1 2 1\n1 3 4\n2 3 2\n2 4 5\n3 4 1", "output": "4"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, m = map(int, input().split())\n"
                    "    edges = []\n"
                    "    for _ in range(m):\n"
                    "        u, v, w = map(int, input().split())\n"
                    "        edges.append((w, u - 1, v - 1))\n"
                    "    edges.sort()\n"
                    "    parent = list(range(n))\n"
                    "    size = [1] * n\n\n"
                    "    def find(x: int) -> int:\n"
                    "        while parent[x] != x:\n"
                    "            parent[x] = parent[parent[x]]\n"
                    "            x = parent[x]\n"
                    "        return x\n\n"
                    "    total = 0\n"
                    "    for w, u, v in edges:\n"
                    "        ru = find(u)\n"
                    "        rv = find(v)\n"
                    "        if ru == rv:\n"
                    "            continue\n"
                    "        if size[ru] < size[rv]:\n"
                    "            ru, rv = rv, ru\n"
                    "        parent[rv] = ru\n"
                    "        size[ru] += size[rv]\n"
                    "        total += w\n"
                    "    print(total)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-029":
            return _array_template(
                statement="重みのない木が与えられる。木の直径の長さを求めよ。",
                input_format="1 行目に N。\n続く N-1 行に辺 u v。",
                output_format="直径の長さを出力する。",
                constraints="1 <= N <= 2 * 10^5",
                examples=[{"input": "5\n1 2\n2 3\n2 4\n4 5", "output": "3"}],
                reference_solution=(
                    "from collections import deque\n\n"
                    "def farthest(start: int, graph: list[list[int]]) -> tuple[int, int]:\n"
                    "    dist = [-1] * len(graph)\n"
                    "    dist[start] = 0\n"
                    "    dq = deque([start])\n"
                    "    while dq:\n"
                    "        node = dq.popleft()\n"
                    "        for nxt in graph[node]:\n"
                    "            if dist[nxt] != -1:\n"
                    "                continue\n"
                    "            dist[nxt] = dist[node] + 1\n"
                    "            dq.append(nxt)\n"
                    "    best = max(range(len(graph)), key=lambda idx: dist[idx])\n"
                    "    return best, dist[best]\n\n"
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n = int(input())\n"
                    "    graph = [[] for _ in range(n)]\n"
                    "    for _ in range(n - 1):\n"
                    "        u, v = map(int, input().split())\n"
                    "        u -= 1\n"
                    "        v -= 1\n"
                    "        graph[u].append(v)\n"
                    "        graph[v].append(u)\n"
                    "    node, _ = farthest(0, graph)\n"
                    "    _, diameter = farthest(node, graph)\n"
                    "    print(diameter)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-030":
            return _array_template(
                statement="根 1 の木と Q 個の問い合わせ u v が与えられる。各問い合わせについて最小共通祖先を求めよ。",
                input_format="1 行目に N Q。\n続く N-1 行に辺 u v。\n続く Q 行に u v。",
                output_format="各問い合わせの答えを 1 行ずつ出力する。",
                constraints="1 <= N, Q <= 2 * 10^5",
                examples=[{"input": "5 3\n1 2\n1 3\n3 4\n3 5\n2 4\n4 5\n2 5", "output": "1\n3\n1"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    sys.setrecursionlimit(10 ** 7)\n"
                    "    input = sys.stdin.readline\n"
                    "    n, q = map(int, input().split())\n"
                    "    graph = [[] for _ in range(n)]\n"
                    "    for _ in range(n - 1):\n"
                    "        u, v = map(int, input().split())\n"
                    "        u -= 1\n"
                    "        v -= 1\n"
                    "        graph[u].append(v)\n"
                    "        graph[v].append(u)\n"
                    "    log = n.bit_length()\n"
                    "    parent = [[-1] * n for _ in range(log)]\n"
                    "    depth = [0] * n\n\n"
                    "    def dfs(node: int, par: int) -> None:\n"
                    "        parent[0][node] = par\n"
                    "        for nxt in graph[node]:\n"
                    "            if nxt == par:\n"
                    "                continue\n"
                    "            depth[nxt] = depth[node] + 1\n"
                    "            dfs(nxt, node)\n\n"
                    "    dfs(0, -1)\n"
                    "    for k in range(1, log):\n"
                    "        for node in range(n):\n"
                    "            prev = parent[k - 1][node]\n"
                    "            parent[k][node] = -1 if prev == -1 else parent[k - 1][prev]\n\n"
                    "    def lca(u: int, v: int) -> int:\n"
                    "        if depth[u] < depth[v]:\n"
                    "            u, v = v, u\n"
                    "        diff = depth[u] - depth[v]\n"
                    "        for k in range(log):\n"
                    "            if diff >> k & 1:\n"
                    "                u = parent[k][u]\n"
                    "        if u == v:\n"
                    "            return u\n"
                    "        for k in range(log - 1, -1, -1):\n"
                    "            if parent[k][u] != parent[k][v]:\n"
                    "                u = parent[k][u]\n"
                    "                v = parent[k][v]\n"
                    "        return parent[0][u]\n\n"
                    "    out = []\n"
                    "    for _ in range(q):\n"
                    "        u, v = map(int, input().split())\n"
                    "        out.append(str(lca(u - 1, v - 1) + 1))\n"
                    "    sys.stdout.write('\\n'.join(out))\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-031":
            return _array_template(
                statement="有向グラフが与えられる。強連結成分の個数を求めよ。",
                input_format="1 行目に N M。\n続く M 行に辺 u v。",
                output_format="強連結成分の個数を出力する。",
                constraints="1 <= N, M <= 2 * 10^5",
                examples=[{"input": "5 6\n1 2\n2 1\n2 3\n3 4\n4 3\n4 5", "output": "3"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    sys.setrecursionlimit(10 ** 7)\n"
                    "    input = sys.stdin.readline\n"
                    "    n, m = map(int, input().split())\n"
                    "    graph = [[] for _ in range(n)]\n"
                    "    rev = [[] for _ in range(n)]\n"
                    "    for _ in range(m):\n"
                    "        u, v = map(int, input().split())\n"
                    "        u -= 1\n"
                    "        v -= 1\n"
                    "        graph[u].append(v)\n"
                    "        rev[v].append(u)\n"
                    "    order = []\n"
                    "    seen = [False] * n\n\n"
                    "    def dfs(node: int) -> None:\n"
                    "        seen[node] = True\n"
                    "        for nxt in graph[node]:\n"
                    "            if not seen[nxt]:\n"
                    "                dfs(nxt)\n"
                    "        order.append(node)\n\n"
                    "    def rdfs(node: int) -> None:\n"
                    "        seen[node] = True\n"
                    "        for nxt in rev[node]:\n"
                    "            if not seen[nxt]:\n"
                    "                rdfs(nxt)\n\n"
                    "    for node in range(n):\n"
                    "        if not seen[node]:\n"
                    "            dfs(node)\n"
                    "    seen = [False] * n\n"
                    "    count = 0\n"
                    "    for node in reversed(order):\n"
                    "        if seen[node]:\n"
                    "            continue\n"
                    "        rdfs(node)\n"
                    "        count += 1\n"
                    "    print(count)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.id == "algo-035":
            return _array_template(
                statement="無向グラフが与えられる。橋の本数を求めよ。",
                input_format="1 行目に N M。\n続く M 行に辺 u v。",
                output_format="橋の本数を出力する。",
                constraints="1 <= N, M <= 2 * 10^5",
                examples=[{"input": "5 5\n1 2\n2 3\n3 1\n3 4\n4 5", "output": "2"}],
                reference_solution=(
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    sys.setrecursionlimit(10 ** 7)\n"
                    "    input = sys.stdin.readline\n"
                    "    n, m = map(int, input().split())\n"
                    "    graph = [[] for _ in range(n)]\n"
                    "    for idx in range(m):\n"
                    "        u, v = map(int, input().split())\n"
                    "        u -= 1\n"
                    "        v -= 1\n"
                    "        graph[u].append((v, idx))\n"
                    "        graph[v].append((u, idx))\n"
                    "    order = [-1] * n\n"
                    "    low = [0] * n\n"
                    "    timer = 0\n"
                    "    bridges = 0\n\n"
                    "    def dfs(node: int, parent_edge: int) -> None:\n"
                    "        nonlocal timer, bridges\n"
                    "        order[node] = low[node] = timer\n"
                    "        timer += 1\n"
                    "        for nxt, edge_id in graph[node]:\n"
                    "            if edge_id == parent_edge:\n"
                    "                continue\n"
                    "            if order[nxt] == -1:\n"
                    "                dfs(nxt, edge_id)\n"
                    "                low[node] = min(low[node], low[nxt])\n"
                    "                if order[node] < low[nxt]:\n"
                    "                    bridges += 1\n"
                    "            else:\n"
                    "                low[node] = min(low[node], order[nxt])\n\n"
                    "    for node in range(n):\n"
                    "        if order[node] == -1:\n"
                    "            dfs(node, -1)\n"
                    "    print(bridges)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        if theme.category == "グラフ":
            return _array_template(
                statement="N 頂点 M 辺の無向グラフが与えられる。頂点 1 から到達できる頂点数を求めよ。",
                input_format="1 行目に N M。\n続く M 行に辺 u v。",
                output_format="到達できる頂点数を出力する。",
                constraints="1 <= N, M <= 2 * 10^5",
                examples=[{"input": "4 2\n1 2\n3 4", "output": "2"}],
                reference_solution=(
                    "from collections import deque\n\n"
                    "def solve() -> None:\n"
                    "    import sys\n"
                    "    input = sys.stdin.readline\n"
                    "    n, m = map(int, input().split())\n"
                    "    graph = [[] for _ in range(n)]\n"
                    "    for _ in range(m):\n"
                    "        u, v = map(int, input().split())\n"
                    "        u -= 1\n"
                    "        v -= 1\n"
                    "        graph[u].append(v)\n"
                    "        graph[v].append(u)\n"
                    "    seen = [False] * n\n"
                    "    dq = deque([0])\n"
                    "    seen[0] = True\n"
                    "    ans = 0\n"
                    "    while dq:\n"
                    "        node = dq.popleft()\n"
                    "        ans += 1\n"
                    "        for nxt in graph[node]:\n"
                    "            if seen[nxt]:\n"
                    "                continue\n"
                    "            seen[nxt] = True\n"
                    "            dq.append(nxt)\n"
                    "    print(ans)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
            )
        return _array_template(
            statement="長さ N の整数列 A が与えられる。異なる値の個数を求めよ。",
            input_format="1 行目に N。\n2 行目に A1..AN。",
            output_format="異なる値の個数を出力する。",
            constraints="1 <= N <= 2 * 10^5",
            examples=[{"input": "5\n1 2 3 2 1", "output": "3"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    input()\n"
                "    a = list(map(int, input().split()))\n"
                "    print(len(set(a)))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )

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

    def _validate_units(self) -> None:
        unit_ids = [unit["unit_id"] for unit in self._units]
        if len(unit_ids) != len(set(unit_ids)):
            raise AlgorithmFoundationCatalogError(
                error_code="duplicate_unit_id",
                message="algorithm foundations catalog contains duplicate unit_id",
            )
        counts = self.counts()
        if counts[0] < 300 or counts[1] < 1000:
            raise AlgorithmFoundationCatalogError(
                error_code="catalog_too_small",
                message=(
                    "algorithm foundations catalog must contain at least "
                    "300 units and 1000 problems"
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
