from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-111-basic',
    title='点の多角形内包判定 の基本',
    unit_kind='foundation',
    target_skill='点の多角形内包判定 の基本',
    concept_overview='凸多角形では、点がすべての辺の同じ側にあれば内部にあります。まずは 1 点だけを対象に、外積の符号が全辺でそろうかと辺上判定を O(N) で確認する基本を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-111-basic-p1',
            title='点の多角形内包判定 の基本 / 凸多角形の内部または辺上に点があるかを判定する',
            problem_statement='反時計回り順に頂点が与えられる凸多角形と点 P が与えられる。P が多角形の内部または辺上なら Yes、外部なら No を出力せよ。',
            input_format='1 行目に N。\n続く N 行に xi yi。\n最後に px py。',
            output_format='Yes / No を出力する。',
            constraints='3 <= N <= 2 * 10^5\n-10^9 <= x_i, y_i, p_x, p_y <= 10^9\n多角形は反時計回り順の凸多角形',
            examples=[{'input': '4\n0 0\n4 0\n4 4\n0 4\n2 2', 'output': 'Yes'}],
            canonical_reference_solution="def cross(ax: int, ay: int, bx: int, by: int, cx: int, cy: int) -> int:\n    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)\n\n\ndef on_segment(ax: int, ay: int, bx: int, by: int, px: int, py: int) -> bool:\n    if cross(ax, ay, bx, by, px, py) != 0:\n        return False\n    return min(ax, bx) <= px <= max(ax, bx) and min(ay, by) <= py <= max(ay, by)\n\n\ndef solve() -> None:\n    n = int(input())\n    pts = [tuple(map(int, input().split())) for _ in range(n)]\n    px, py = map(int, input().split())\n    sign = 0\n    for i in range(n):\n        ax, ay = pts[i]\n        bx, by = pts[(i + 1) % n]\n        if on_segment(ax, ay, bx, by, px, py):\n            print('Yes')\n            return\n        value = cross(ax, ay, bx, by, px, py)\n        if value == 0:\n            continue\n        current = 1 if value > 0 else -1\n        if sign == 0:\n            sign = current\n        elif sign != current:\n            print('No')\n            return\n    print('Yes')\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
