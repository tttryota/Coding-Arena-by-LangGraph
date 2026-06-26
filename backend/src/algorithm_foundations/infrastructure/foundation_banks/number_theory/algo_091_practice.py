from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-091-practice',
    title='オイラーのトーシェント関数 を素直に実装する',
    unit_kind='foundation',
    target_skill='オイラーのトーシェント関数 を分数の個数として使う',
    concept_overview='φ(N) は整数の個数としてだけでなく、分母を N に固定した既約真分数の個数としても読めます。同じ式を使いながら、1 以上 N 未満という境界の意味を確認します。',
    problem_bank=[
        problem(
            problem_id='algo-091-practice-p1',
            title='オイラーのトーシェント関数 を分数の個数として使う / 分母 N の既約真分数の個数を求める',
            problem_statement='整数 N が与えられる。分母が N の既約真分数 a/N (0 < a/N < 1) は何個あるか求めよ。ここで a は整数で、a/N が既約であるとは gcd(a, N)=1 であることをいう。',
            input_format='1 行目に N。',
            output_format='条件を満たす分数の個数を出力する。',
            constraints='1 <= N <= 10^12',
            examples=[{'input': '12', 'output': '4'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    if n == 1:\n        print(0)\n        return\n    x = n\n    ans = n\n    p = 2\n    while p * p <= x:\n        if x % p == 0:\n            while x % p == 0:\n                x //= p\n            ans -= ans // p\n        p += 1\n    if x > 1:\n        ans -= ans // x\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
