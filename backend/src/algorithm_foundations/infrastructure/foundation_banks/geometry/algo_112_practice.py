from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-112-practice',
    title='直線の交差判定 を素直に実装する',
    unit_kind='foundation',
    target_skill='直線の交差判定 を素直に実装する',
    concept_overview='平行判定に加えて、同じ直線そのものか、別の平行線か、1 点で交わるかまで分けると直線同士の位置関係を分類できます。ここでは 3 通りに分類します。',
    problem_bank=[
        problem(
            problem_id='algo-112-practice-p1',
            title='直線の交差判定 を素直に実装する / 一致・平行・交差の 3 通りに分類する',
            problem_statement='直線 AB と直線 CD が与えられる。2 直線が同一直線なら Same、平行だが一致しないなら Parallel、1 点で交わるなら Intersect を出力せよ。',
            input_format='1 行目に ax ay bx by cx cy dx dy。',
            output_format='Same / Parallel / Intersect のいずれかを出力する。',
            constraints='-10^9 <= 座標 <= 10^9\nA != B\nC != D',
            examples=[{'input': '0 0 2 2 1 1 3 3', 'output': 'Same'}],
            canonical_reference_solution="def solve() -> None:\n    ax, ay, bx, by, cx, cy, dx, dy = map(int, input().split())\n    vx1, vy1 = bx - ax, by - ay\n    vx2, vy2 = dx - cx, dy - cy\n    cross_dir = vx1 * vy2 - vy1 * vx2\n    if cross_dir != 0:\n        print('Intersect')\n        return\n    cross_pos = vx1 * (cy - ay) - vy1 * (cx - ax)\n    print('Same' if cross_pos == 0 else 'Parallel')\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
