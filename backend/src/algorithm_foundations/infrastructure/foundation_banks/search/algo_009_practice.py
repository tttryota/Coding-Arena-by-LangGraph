from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-009-practice',
    title='尺取り法 を素直に実装する',
    unit_kind='foundation',
    target_skill='尺取り法 を素直に実装する',
    concept_overview='尺取り法では、「条件を満たさない間は右を伸ばし、満たしすぎたら左を縮める」を使って最長長さも求められます。ここでは和が S 以下の最長区間を探します。',
    problem_bank=[
        problem(
            problem_id='algo-009-practice-p1',
            title='尺取り法 を素直に実装する / 総和が S 以下となる最長区間を求める',
            problem_statement='長さ N の正整数列 A と整数 S が与えられる。総和が S 以下となる連続部分列のうち、長さの最大値を求めよ。存在しなければ 0 を出力せよ。',
            input_format='1 行目に N S。\n2 行目に A1..AN。',
            output_format='最大長を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= Ai, S <= 10^9',
            examples=[{'input': '6 7\n2 3 1 2 4 3', 'output': '3'}],
            canonical_reference_solution="def solve() -> None:\n    n, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    ans = 0\n    total = 0\n    left = 0\n    for right, value in enumerate(a):\n        total += value\n        while total > s:\n            total -= a[left]\n            left += 1\n        ans = max(ans, right - left + 1)\n    print(ans)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
