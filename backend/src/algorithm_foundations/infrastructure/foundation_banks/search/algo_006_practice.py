from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-006-practice',
    title='bit全探索 を素直に実装する',
    unit_kind='foundation',
    target_skill='bit全探索 を素直に実装する',
    concept_overview='bit 全探索では、条件を満たすかどうかだけでなく、全部試した中から最良の値を選ぶこともできます。ここでは S 以下で最大の部分集合和を探します。',
    problem_bank=[
        problem(
            problem_id='algo-006-practice-p1',
            title='bit全探索 を素直に実装する / S 以下で最大の部分集合和を求める',
            problem_statement='長さ N の非負整数列 A と目標値 S が与えられる。bit 全探索を用いて、部分集合の和のうち S 以下で最大の値を求めよ。',
            input_format='1 行目に N S。\n2 行目に A1..AN。',
            output_format='求める最大値を出力する。',
            constraints='1 <= N <= 20\n0 <= A_i <= 10^9\n0 <= S <= 10^18',
            examples=[{'input': '4 11\n2 5 9 4', 'output': '11'}],
            canonical_reference_solution="def solve() -> None:\n    n, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    ans = 0\n    for mask in range(1 << n):\n        total = 0\n        for i in range(n):\n            if mask >> i & 1:\n                total += a[i]\n        if total <= s and total > ans:\n            ans = total\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
