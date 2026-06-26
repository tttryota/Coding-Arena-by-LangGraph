from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-090-basic',
    title='約数列挙 の基本',
    unit_kind='foundation',
    target_skill='約数列挙 の基本',
    concept_overview='約数列挙は、d が約数なら N/d も約数になる対応を使って、平方根までの探索で全約数を集める知識です。小さい側と大きい側を分けて持つ基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-090-basic-p1',
            title='約数列挙 の基本 / N の正の約数を小さい順にすべて出力せよ',
            problem_statement='整数 N が与えられる。N の正の約数を小さい順にすべて出力せよ。',
            input_format='1 行目に N。',
            output_format='正の約数を空白区切りで出力する。',
            constraints='1 <= N <= 10^12',
            examples=[{'input': '12', 'output': '1 2 3 4 6 12'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    small = []\n    large = []\n    d = 1\n    while d * d <= n:\n        if n % d == 0:\n            small.append(d)\n            if d * d != n:\n                large.append(n // d)\n        d += 1\n    print(*(small + large[::-1]))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
