from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-109-basic',
    title='点と直線の距離 の基本',
    unit_kind='foundation',
    target_skill='点と直線の距離 の基本',
    concept_overview='点から直線への距離は、平行四辺形の面積を表す外積を底辺の長さで割ると求められます。まずは無限に延びる直線への距離を計算します。',
    problem_bank=[
        problem(
            problem_id='algo-109-basic-p1',
            title='点と直線の距離 の基本 / P から直線 AB への距離を求める',
            problem_statement='点 P と直線 AB が与えられる。P から直線 AB への距離を求めよ。',
            input_format='1 行目に px py ax ay bx by。',
            output_format='距離を出力する。絶対誤差または相対誤差 10^-6 まで許す。',
            constraints='-10^9 <= 座標 <= 10^9\nA != B',
            examples=[{'input': '0 2 -1 0 1 0', 'output': '2.0'}],
            canonical_reference_solution="import math\n\ndef solve() -> None:\n    px, py, ax, ay, bx, by = map(int, input().split())\n    cross = abs((bx - ax) * (py - ay) - (by - ay) * (px - ax))\n    length = math.hypot(bx - ax, by - ay)\n    print(cross / length)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
