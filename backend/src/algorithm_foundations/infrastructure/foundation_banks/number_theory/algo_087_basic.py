from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-087-basic',
    title='包除原理 の基本',
    unit_kind='foundation',
    target_skill='包除原理 の基本',
    concept_overview='包除原理は、重なって数えた分を引き戻して「A または B」の個数を正しく数える知識です。まずは倍数の個数を足してから最小公倍数の倍数を引く 2 集合の基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-087-basic-p1',
            title='包除原理 の基本 / 1 以上 N 以下で A または B の倍数である整数の個数を求める',
            problem_statement='整数 N, A, B が与えられる。1 以上 N 以下で A または B の倍数である整数の個数を求めよ。',
            input_format='1 行目に N A B。',
            output_format='条件を満たす個数を出力する。',
            constraints='1 <= N, A, B <= 10^18',
            examples=[{'input': '20 4 6', 'output': '7'}],
            canonical_reference_solution="from math import gcd\n\ndef solve() -> None:\n    n, a, b = map(int, input().split())\n    lcm = a // gcd(a, b) * b\n    ans = n // a + n // b - n // lcm\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
