from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-082-practice',
    title='素因数分解 から種類数を読む',
    unit_kind='foundation',
    target_skill='素因数分解 から種類数を読む',
    concept_overview='素因数分解では、整数を割り切る素数が何種類現れるかも分かります。ここでは指数そのものではなく、分解結果に含まれる異なる素因数の個数を読み取る練習をします。',
    problem_bank=[
        problem(
            problem_id='algo-082-practice-p1',
            title='素因数分解 から種類数を読む / 異なる素因数の種類数を求める',
            problem_statement='整数 N が与えられる。N を素因数分解したときに現れる異なる素因数の種類数を求めよ。',
            input_format='1 行目に N。',
            output_format='異なる素因数の種類数を出力する。',
            constraints='2 <= N <= 10^12',
            examples=[{'input': '72', 'output': '2'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    kinds = 0\n    d = 2\n    while d * d <= n:\n        if n % d == 0:\n            kinds += 1\n            while n % d == 0:\n                n //= d\n        d += 1\n    if n > 1:\n        kinds += 1\n    print(kinds)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
