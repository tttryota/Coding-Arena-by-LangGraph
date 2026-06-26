from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-082-basic',
    title='素因数分解 の基本',
    unit_kind='foundation',
    target_skill='素因数分解 の基本',
    concept_overview='素因数分解は、整数を素数の積へ分けて、その数がどの素数を何回含むかを調べる知識です。小さい候補から試し割りし、割れる間は回数を数える基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-082-basic-p1',
            title='素因数分解 の基本 / 素因数分解し、素因数 指数 を素因数の昇順で出力せよ',
            problem_statement='整数 N が与えられる。素因数分解し、`素因数 指数` を素因数の昇順で出力せよ。',
            input_format='1 行目に N。',
            output_format='各行に `p e` を出力する。',
            constraints='2 <= N <= 10^12',
            examples=[{'input': '72', 'output': '2 3\n3 2'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    out = []\n    d = 2\n    while d * d <= n:\n        if n % d == 0:\n            cnt = 0\n            while n % d == 0:\n                n //= d\n                cnt += 1\n            out.append(f'{d} {cnt}')\n        d += 1\n    if n > 1:\n        out.append(f'{n} 1')\n    print('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
