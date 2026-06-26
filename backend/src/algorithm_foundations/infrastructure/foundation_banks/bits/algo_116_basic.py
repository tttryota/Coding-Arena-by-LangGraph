from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-116-basic',
    title='XORの性質と応用 の基本',
    unit_kind='foundation',
    target_skill='XORの性質と応用 の基本',
    concept_overview='XOR は左から順に畳み込めて、各 bit ごとの偶奇だけが結果に残る演算です。まずは配列全体の XOR を 1 本の走査で求める基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-116-basic-p1',
            title='XORの性質と応用 の基本 / すべての要素の XOR を求める',
            problem_statement='長さ N の整数列 A が与えられる。すべての要素の XOR を求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='XOR を出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai < 2^60',
            examples=[{'input': '4\n1 2 3 4', 'output': '4'}],
            canonical_reference_solution="def solve() -> None:\n    input()\n    ans = 0\n    for value in map(int, input().split()):\n        ans ^= value\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
