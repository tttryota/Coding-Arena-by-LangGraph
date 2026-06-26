from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-114-basic',
    title='円と直線の交点 の基本',
    unit_kind='foundation',
    target_skill='円と直線の交点 の基本',
    concept_overview='円と直線の交点では、まず円の中心から直線へ下ろした垂線の長さを求め、半径との大小比較で交点数を判定します。式に直した距離判定で 0 個・1 個・2 個を見分ける基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-114-basic-p1',
            title='円と直線の交点 の基本 / 交点の個数を 0, 1, 2 のいずれかで出力せよ',
            problem_statement='円の中心 C と半径 r、直線 AB が与えられる。円と直線 AB の交点の個数を 0, 1, 2 のいずれかで出力せよ。',
            input_format='1 行目に cx cy r ax ay bx by。',
            output_format='交点の個数を出力する。',
            constraints='座標と半径は整数\nA と B は異なる点',
            examples=[{'input': '0 0 5 -10 0 10 0', 'output': '2'}],
            canonical_reference_solution="def solve() -> None:\n    import math\n    cx, cy, r, ax, ay, bx, by = map(int, input().split())\n    cross = abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax))\n    length = math.hypot(bx - ax, by - ay)\n    dist = cross / length\n    if dist > r:\n        print(0)\n    elif abs(dist - r) < 1e-9:\n        print(1)\n    else:\n        print(2)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
