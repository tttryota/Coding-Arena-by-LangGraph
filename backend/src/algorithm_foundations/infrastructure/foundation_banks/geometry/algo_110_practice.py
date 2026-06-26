from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-110-practice',
    title='多角形の面積（シューレースの公式） を素直に実装する',
    unit_kind='foundation',
    target_skill='多角形の面積（シューレースの公式） を素直に実装する',
    concept_overview='三角形の面積が分かれば、頂点を順にたどる多角形でも隣り合う辺の寄与を全部足して面積を求められます。ここでは一般の単純多角形へ広げます。',
    problem_bank=[
        problem(
            problem_id='algo-110-practice-p1',
            title='多角形の面積（シューレースの公式） を素直に実装する / 頂点が順に与えられる多角形の面積を求める',
            problem_statement='頂点が順に与えられる多角形の面積を求めよ。',
            input_format='1 行目に N。\n続く N 行に xi yi。',
            output_format='面積を出力する。',
            constraints='3 <= N <= 2 * 10^5\n-10^9 <= x_i, y_i <= 10^9\n頂点は順に単純多角形をなす\n絶対誤差または相対誤差 10^-6 まで許す',
            examples=[{'input': '4\n0 0\n2 0\n2 1\n0 1', 'output': '2.0'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    points = [tuple(map(int, input().split())) for _ in range(n)]\n    total = 0\n    for i in range(n):\n        x1, y1 = points[i]\n        x2, y2 = points[(i + 1) % n]\n        total += x1 * y2 - y1 * x2\n    print(abs(total) / 2)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
