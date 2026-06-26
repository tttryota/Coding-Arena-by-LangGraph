from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-109-practice',
    title='点と直線の距離 を素直に実装する',
    unit_kind='foundation',
    target_skill='点と直線の距離 を素直に実装する',
    concept_overview='投影点が線分の外に出るときは、最も近い点は端点になります。ここでは直線への距離を土台に、点から線分への最短距離へ広げます。',
    problem_bank=[
        problem(
            problem_id='algo-109-practice-p1',
            title='点と直線の距離 を素直に実装する / P から線分 AB への最短距離を求める',
            problem_statement='点 P と線分 AB が与えられる。P から線分 AB への最短距離を求めよ。',
            input_format='1 行目に px py ax ay bx by。',
            output_format='距離を出力する。絶対誤差または相対誤差 10^-6 まで許す。',
            constraints='-10^9 <= 座標 <= 10^9\nA != B',
            examples=[{'input': '3 1 0 0 2 0', 'output': '1.4142135623730951'}],
            canonical_reference_solution="import math\n\n\ndef solve() -> None:\n    px, py, ax, ay, bx, by = map(int, input().split())\n    abx = bx - ax\n    aby = by - ay\n    apx = px - ax\n    apy = py - ay\n    bpx = px - bx\n    bpy = py - by\n    if abx * apx + aby * apy <= 0:\n        print(math.hypot(apx, apy))\n        return\n    if (-abx) * bpx + (-aby) * bpy <= 0:\n        print(math.hypot(bpx, bpy))\n        return\n    cross = abs(abx * apy - aby * apx)\n    length = math.hypot(abx, aby)\n    print(cross / length)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
