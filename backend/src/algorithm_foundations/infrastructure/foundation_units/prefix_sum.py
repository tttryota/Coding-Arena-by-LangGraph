"""Prefix-sum family definitions for algorithm foundations."""

from __future__ import annotations

from typing import Final

from .common import ProblemTemplate, SpecialThemeUnitDef, array_template

SPECIAL_THEME_UNITS: Final[tuple[SpecialThemeUnitDef, ...]] = (
    ("algo-099", 0, "prefix-sum-1d", "一次元累積和の基本", "foundation"),
    ("algo-099", 1, "prefix-sum-range", "累積和で区間和を求める", "foundation"),
    ("algo-099", 2, "prefix-sum-2d", "二次元累積和で長方形和を求める", "integration"),
)

SPECIAL_UNIT_CONCEPT_OVERVIEWS: Final[dict[str, str]] = {
    "algo-099-prefix-sum-1d": "累積和は、左から順に和をためておき、途中までの合計をすぐ取り出せるようにする考え方です。まずは prefix sum 配列を作るところから押さえます。",
    "algo-099-prefix-sum-range": "累積和を使うと、区間の和を『右端までの和 - 左端の手前までの和』で求められます。区間を差で取り出す形を身につけます。",
    "algo-099-prefix-sum-2d": "二次元累積和は、長方形の和を四隅の足し引きに変えて素早く求める考え方です。表を前計算し、問い合わせを定数時間で処理する練習をします。",
}


def build_problem_template(unit_id: str) -> ProblemTemplate | None:
    if unit_id == "algo-099-prefix-sum-1d":
        return array_template(
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
    if unit_id == "algo-099-prefix-sum-2d":
        return array_template(
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
    if unit_id == "algo-099-prefix-sum-range":
        return array_template(
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
    return None
