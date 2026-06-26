from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-107-practice',
    title='凸包（Convex Hull） を素直に実装する',
    unit_kind='foundation',
    target_skill='凸包（Convex Hull） を素直に実装する',
    concept_overview='凸包の頂点列が作れたら、その列を一周して外周の長さも求められます。ここでは凸包を構成したあと、隣り合う頂点間の距離を足して周長を計算します。',
    problem_bank=[
        problem(
            problem_id='algo-107-practice-p1',
            title='凸包（Convex Hull） を素直に実装する / 凸包の周長を求める',
            problem_statement='平面上の N 点が与えられる。これらの点の凸包を作ったときの周長を求めよ。辺の途中にある共線点は頂点として数えない。',
            input_format='1 行目に N。\n続く N 行に xi yi。',
            output_format='周長を出力する。絶対誤差または相対誤差 10^-6 まで許す。',
            constraints='3 <= N <= 2 * 10^5\n-10^9 <= x_i, y_i <= 10^9\n入力点は相異なる\n少なくとも 3 点は同一直線上にない',
            examples=[{'input': '5\n0 0\n2 0\n2 2\n0 2\n1 1', 'output': '8.0'}],
            canonical_reference_solution="import math\n\n\ndef cross(o: tuple[int, int], a: tuple[int, int], b: tuple[int, int]) -> int:\n    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])\n\n\ndef solve() -> None:\n    n = int(input())\n    pts = sorted(tuple(map(int, input().split())) for _ in range(n))\n    lower = []\n    for p in pts:\n        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:\n            lower.pop()\n        lower.append(p)\n    upper = []\n    for p in reversed(pts):\n        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:\n            upper.pop()\n        upper.append(p)\n    hull = lower[:-1] + upper[:-1]\n    ans = 0.0\n    for i in range(len(hull)):\n        x1, y1 = hull[i]\n        x2, y2 = hull[(i + 1) % len(hull)]\n        ans += math.hypot(x1 - x2, y1 - y2)\n    print(ans)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
