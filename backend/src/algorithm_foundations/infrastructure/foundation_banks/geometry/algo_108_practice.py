from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-108-practice',
    title='線分の交差判定 を素直に実装する',
    unit_kind='foundation',
    target_skill='線分の交差判定 を素直に実装する',
    concept_overview='内部交差の判定に加えて、端点での接触や一直線上での重なりも正しく扱うと、一般の線分交差判定になります。ここでは境界ケースを含めて交差の有無を判定します。',
    problem_bank=[
        problem(
            problem_id='algo-108-practice-p1',
            title='線分の交差判定 を素直に実装する / 接触や重なりも含めて交差するかを判定する',
            problem_statement='線分 AB と線分 CD が与えられる。2 本の線分が 1 点でも共有するなら Yes、そうでなければ No を出力せよ。端点で接する場合や、一直線上で一部が重なる場合も Yes とする。',
            input_format='1 行目に ax ay bx by cx cy dx dy。',
            output_format='Yes / No を出力する。',
            constraints='-10^9 <= 座標 <= 10^9\nA != B\nC != D',
            examples=[{'input': '0 0 4 0 4 0 4 3', 'output': 'Yes'}],
            canonical_reference_solution="def cross(ax: int, ay: int, bx: int, by: int, cx: int, cy: int) -> int:\n    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)\n\n\ndef on_segment(ax: int, ay: int, bx: int, by: int, px: int, py: int) -> bool:\n    if cross(ax, ay, bx, by, px, py) != 0:\n        return False\n    return min(ax, bx) <= px <= max(ax, bx) and min(ay, by) <= py <= max(ay, by)\n\n\ndef solve() -> None:\n    ax, ay, bx, by, cx, cy, dx, dy = map(int, input().split())\n    c1 = cross(ax, ay, bx, by, cx, cy)\n    c2 = cross(ax, ay, bx, by, dx, dy)\n    c3 = cross(cx, cy, dx, dy, ax, ay)\n    c4 = cross(cx, cy, dx, dy, bx, by)\n    if c1 == 0 and on_segment(ax, ay, bx, by, cx, cy):\n        print('Yes')\n        return\n    if c2 == 0 and on_segment(ax, ay, bx, by, dx, dy):\n        print('Yes')\n        return\n    if c3 == 0 and on_segment(cx, cy, dx, dy, ax, ay):\n        print('Yes')\n        return\n    if c4 == 0 and on_segment(cx, cy, dx, dy, bx, by):\n        print('Yes')\n        return\n    print('Yes' if c1 * c2 < 0 and c3 * c4 < 0 else 'No')\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
