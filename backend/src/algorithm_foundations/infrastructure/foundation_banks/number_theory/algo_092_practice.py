from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-092-practice',
    title='メビウス関数 μ(N) を素直に実装する',
    unit_kind='foundation',
    target_skill='メビウス関数 の平方因子判定を数え上げへ使う',
    concept_overview='メビウス関数の土台は「平方因子を持つか」と「異なる素因数を何種類持つか」です。ここでは μ(N) 自体ではなく、その判定を使って square-free な約数の個数を数えます。',
    problem_bank=[
        problem(
            problem_id='algo-092-practice-p1',
            title='メビウス関数 の平方因子判定を数え上げへ使う / N の square-free な正の約数の個数を求める',
            problem_statement='整数 N が与えられる。N の正の約数のうち、square-free なものの個数を求めよ。ここで正の整数 d が square-free であるとは、どの素数 p に対しても p^2 が d を割り切らないことをいう。',
            input_format='1 行目に N。',
            output_format='square-free な正の約数の個数を出力する。',
            constraints='1 <= N <= 10^12',
            examples=[{'input': '12', 'output': '4'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    x = n\n    distinct = 0\n    p = 2\n    while p * p <= x:\n        if x % p == 0:\n            distinct += 1\n            while x % p == 0:\n                x //= p\n        p += 1\n    if x > 1:\n        distinct += 1\n    print(1 << distinct)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
