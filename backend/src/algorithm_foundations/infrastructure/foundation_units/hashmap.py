"""Hashmap family definitions for algorithm foundations."""

from __future__ import annotations

from typing import Final

from .common import ProblemTemplate, SpecialThemeUnitDef, array_template

SPECIAL_THEME_UNITS: Final[tuple[SpecialThemeUnitDef, ...]] = (
    ("algo-102", 0, "hashmap-exists", "存在判定をハッシュで高速化", "foundation"),
    ("algo-102", 1, "hashmap-duplicate", "重複検出をハッシュで行う", "foundation"),
    ("algo-102", 2, "hashmap-count", "出現回数カウント", "foundation"),
    ("algo-102", 3, "hashmap-index", "値から位置を引く対応表", "foundation"),
    ("algo-102", 4, "hashmap-match", "2配列の照合をハッシュで処理", "integration"),
)

SPECIAL_UNIT_CONCEPT_OVERVIEWS: Final[dict[str, str]] = {
    "algo-102-hashmap-exists": "値を見たかどうかをハッシュ集合に記録し、あとで同じ値があるかをすぐ調べる考え方です。探索を繰り返さず membership 判定で済ませる形を身につけます。",
    "algo-102-hashmap-duplicate": "見た値をハッシュ集合に入れながら進み、すでに入っているかで重複を判定する考え方です。1 回の走査で重複を見つける流れを押さえます。",
    "algo-102-hashmap-count": "値ごとの出現回数を連想配列にため、あとで必要な回数をすぐ取り出せるようにする考え方です。数え上げを map の更新に置き換える形を身につけます。",
    "algo-102-hashmap-index": "値をキーにして位置や番号を保存しておき、必要になったときに逆引きする考え方です。『探す』を『表から引く』に変える練習をします。",
    "algo-102-hashmap-match": "片方の情報をハッシュにまとめ、もう片方を見ながら一致や不足を判定する考え方です。照合を全組合せではなく表引きで処理する形を学びます。",
}


def build_problem_template(unit_id: str) -> ProblemTemplate | None:
    if unit_id == "algo-102-hashmap-exists":
        return array_template(
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
    if unit_id == "algo-102-hashmap-duplicate":
        return array_template(
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
    if unit_id == "algo-102-hashmap-count":
        return array_template(
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
    if unit_id == "algo-102-hashmap-index":
        return array_template(
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
    if unit_id == "algo-102-hashmap-match":
        return array_template(
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
    return None
