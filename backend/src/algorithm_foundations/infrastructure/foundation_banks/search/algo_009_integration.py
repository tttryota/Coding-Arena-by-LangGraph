from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-009-integration',
    title='尺取り法 の総合演習',
    unit_kind='integration',
    target_skill='尺取り法 の総合演習',
    concept_overview='尺取り法では、各右端について条件を満たす左端の範囲が分かると、最短や最長だけでなく区間数まで数えられます。ここでは「総和が S 以下の区間が何個あるか」を数え上げます。',
    problem_bank=[
        problem(
            problem_id='algo-009-integration-p1',
            title='尺取り法 の総合演習 / 総和が S 以下となる連続部分列の個数を数える',
            problem_statement='長さ N の正整数列 A と整数 S が与えられる。総和が S 以下となる連続部分列の個数を求めよ。',
            input_format='1 行目に N S。\n2 行目に A1..AN。',
            output_format='条件を満たす連続部分列の個数を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= Ai, S <= 10^9',
            examples=[{'input': '6 7\n2 3 1 2 4 3', 'output': '14'}],
            canonical_reference_solution="def solve() -> None:\n    n, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    total = 0\n    left = 0\n    ans = 0\n    for right, value in enumerate(a):\n        total += value\n        while total > s:\n            total -= a[left]\n            left += 1\n        ans += right - left + 1\n    print(ans)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
