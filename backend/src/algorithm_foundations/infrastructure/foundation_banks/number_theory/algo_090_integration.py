from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-090-integration',
    title='約数列挙 の総合演習',
    unit_kind='integration',
    target_skill='約数列挙 の総合演習',
    concept_overview='約数列挙では、小さい側と大きい側に分かれる約数の並びを意識すると、順序付きの問い合わせにも対応できます。ここでは平方根境界と昇順の何番目かを結び付けて扱います。',
    problem_bank=[
        problem(
            problem_id='algo-090-integration-p1',
            title='約数列挙 の総合演習 / N の正の約数のうち K 番目に小さいものを求めよ',
            problem_statement='整数 N, K が与えられる。N の正の約数を小さい順に並べたとき、K 番目に小さいものを出力せよ。正の約数が K 個未満なら -1 を出力せよ。',
            input_format='1 行目に N K。',
            output_format='答えを出力する。',
            constraints='1 <= N <= 10^12\n1 <= K <= 10^6',
            examples=[{'input': '36 5', 'output': '6'}],
            canonical_reference_solution="def solve() -> None:\n    n, k = map(int, input().split())\n    small = []\n    large = []\n    d = 1\n    while d * d <= n:\n        if n % d == 0:\n            small.append(d)\n            if d * d != n:\n                large.append(n // d)\n        d += 1\n    divisors = small + large[::-1]\n    if k > len(divisors):\n        print(-1)\n    else:\n        print(divisors[k - 1])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
