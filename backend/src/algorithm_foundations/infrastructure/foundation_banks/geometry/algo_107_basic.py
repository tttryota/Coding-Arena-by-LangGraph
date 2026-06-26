from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-107-basic',
    title='凸包（Convex Hull） の基本',
    unit_kind='foundation',
    target_skill='凸包（Convex Hull） の基本',
    concept_overview='凸包は、点集合を外側から輪ゴムで包んだときの外周です。点を x 座標順に並べ、外側へ曲がる頂点だけを残していくと凸包の頂点列を作れます。まずは外周に残る頂点数を求めます。',
    problem_bank=[
        problem(
            problem_id='algo-107-basic-p1',
            title='凸包（Convex Hull） の基本 / 凸包の頂点数を求める',
            problem_statement='平面上の N 点が与えられる。凸包の頂点数を求めよ。辺の途中にある共線点は頂点数に含めない。',
            input_format='1 行目に N。\n続く N 行に xi yi。',
            output_format='凸包の頂点数を出力する。',
            constraints='3 <= N <= 2 * 10^5\n-10^9 <= x_i, y_i <= 10^9\n入力点は相異なる',
            examples=[{'input': '5\n0 0\n2 0\n2 2\n0 2\n1 1', 'output': '4'}],
            canonical_reference_solution="def cross(o: tuple[int, int], a: tuple[int, int], b: tuple[int, int]) -> int:\n    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])\n\ndef solve() -> None:\n    n = int(input())\n    pts = sorted({tuple(map(int, input().split())) for _ in range(n)})\n    if len(pts) <= 1:\n        print(len(pts))\n        return\n    lower = []\n    for p in pts:\n        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:\n            lower.pop()\n        lower.append(p)\n    upper = []\n    for p in reversed(pts):\n        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:\n            upper.pop()\n        upper.append(p)\n    hull = lower[:-1] + upper[:-1]\n    print(len(hull))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
