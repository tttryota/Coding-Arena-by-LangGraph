from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-009-basic',
    title='尺取り法 の基本',
    unit_kind='foundation',
    target_skill='尺取り法 の基本',
    concept_overview='尺取り法は、左右の端を動かしながら連続区間を保ち、条件を満たす最短・最長・個数を求める考え方です。区間を伸ばすときと縮めるときの役割分担を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-009-basic-p1',
            title='尺取り法 の基本 / 総和が S 以上となる最短区間を求める',
            problem_statement='長さ N の正整数列 A と整数 S が与えられる。 総和が S 以上となる連続部分列のうち、長さの最小値を求めよ。存在しなければ 0 を出力せよ。',
            input_format='1 行目に N S。\n2 行目に A1..AN。',
            output_format='最小長を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= Ai, S <= 10^9',
            examples=[{'input': '6 11\n2 3 1 2 4 3', 'output': '5'}],
            canonical_reference_solution="def solve() -> None:\n    n, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    ans = n + 1\n    total = 0\n    left = 0\n    for right, value in enumerate(a):\n        total += value\n        while total >= s:\n            ans = min(ans, right - left + 1)\n            total -= a[left]\n            left += 1\n    print(0 if ans == n + 1 else ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
