from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-110-basic',
    title='多角形の面積（シューレースの公式） の基本',
    unit_kind='foundation',
    target_skill='多角形の面積（シューレースの公式） の基本',
    concept_overview='シューレースの公式は、隣り合う頂点の外積を足し合わせて面積を求める方法です。まずは 3 点だけの三角形で、面積が外積の半分になる形を確認します。',
    problem_bank=[
        problem(
            problem_id='algo-110-basic-p1',
            title='多角形の面積（シューレースの公式） の基本 / 3 点で囲まれる三角形の面積を求める',
            problem_statement='平面上の 3 点 A, B, C が与えられる。三角形 ABC の面積を求めよ。',
            input_format='1 行目に ax ay bx by cx cy。',
            output_format='面積を出力する。',
            constraints='-10^9 <= 座標 <= 10^9\n3 点は同一直線上にない\n絶対誤差または相対誤差 10^-6 まで許す',
            examples=[{'input': '0 0 4 0 1 3', 'output': '6.0'}],
            canonical_reference_solution="def solve() -> None:\n    ax, ay, bx, by, cx, cy = map(int, input().split())\n    area2 = abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax))\n    print(area2 / 2)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
