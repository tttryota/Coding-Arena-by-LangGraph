from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-112-basic',
    title='直線の交差判定 の基本',
    unit_kind='foundation',
    target_skill='直線の交差判定 の基本',
    concept_overview='2 本の直線が平行かどうかは、方向ベクトルの外積が 0 かどうかで判定できます。まずは平行か、それ以外かの 2 択だけを扱います。',
    problem_bank=[
        problem(
            problem_id='algo-112-basic-p1',
            title='直線の交差判定 の基本 / 直線 AB と直線 CD が平行なら Parallel、そうでなければ Intersect を求める',
            problem_statement='直線 AB と直線 CD が平行なら Parallel、そうでなければ Intersect を出力せよ。',
            input_format='1 行目に ax ay bx by cx cy dx dy。',
            output_format='Parallel または Intersect を出力する。',
            constraints='-10^9 <= 座標 <= 10^9\nA != B\nC != D',
            examples=[{'input': '0 0 1 1 0 1 1 2', 'output': 'Parallel'}],
            canonical_reference_solution="def solve() -> None:\n    ax, ay, bx, by, cx, cy, dx, dy = map(int, input().split())\n    cross = (bx - ax) * (dy - cy) - (by - ay) * (dx - cx)\n    print('Parallel' if cross == 0 else 'Intersect')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
