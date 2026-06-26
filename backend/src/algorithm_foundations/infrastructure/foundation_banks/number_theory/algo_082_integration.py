from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-082-integration',
    title='素因数分解 の総合演習',
    unit_kind='integration',
    target_skill='素因数分解 の総合演習',
    concept_overview='素因数分解で指数の偶奇まで分かると、「あと何を掛ければ平方数になるか」のような条件も扱えます。指数の余り方に注目する使い方を確認します。',
    problem_bank=[
        problem(
            problem_id='algo-082-integration-p1',
            title='素因数分解 の総合演習 / 何を掛ければ完全平方数になるか最小値を求める',
            problem_statement='整数 N が与えられる。`N x M` が完全平方数になるような最小の正整数 M を求めよ。',
            input_format='1 行目に N。',
            output_format='最小の M を出力する。',
            constraints='2 <= N <= 10^12',
            examples=[{'input': '72', 'output': '2'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    ans = 1\n    d = 2\n    while d * d <= n:\n        cnt = 0\n        while n % d == 0:\n            n //= d\n            cnt += 1\n        if cnt % 2 == 1:\n            ans *= d\n        d += 1\n    if n > 1:\n        ans *= n\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
