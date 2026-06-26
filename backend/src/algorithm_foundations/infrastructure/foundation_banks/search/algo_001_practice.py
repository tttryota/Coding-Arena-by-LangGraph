from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-001-practice',
    title='全探索（ブルートフォース） を素直に実装する',
    unit_kind='foundation',
    target_skill='全探索（ブルートフォース） を素直に実装する',
    concept_overview='連続部分列を全部試す全探索では、存在判定だけでなく「条件を満たす中で最良の値」を選ぶこともできます。ここでは S 以下の最大和を探します。',
    problem_bank=[
        problem(
            problem_id='algo-001-practice-p1',
            title='全探索（ブルートフォース） を素直に実装する / S 以下で最大の連続部分列和を求める',
            problem_statement='長さ N の正整数列 A と整数 S が与えられる。連続部分列の総和のうち、S 以下で最大の値を求めよ。存在しなければ 0 を出力せよ。',
            input_format='1 行目に N S。\n2 行目に A1..AN。',
            output_format='求める最大値を出力する。',
            constraints='1 <= N <= 2000\n1 <= A_i, S <= 10^9',
            examples=[{'input': '5 11\n2 5 4 9 1', 'output': '11'}],
            canonical_reference_solution="def solve() -> None:\n    n, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    ans = 0\n    for left in range(n):\n        total = 0\n        for right in range(left, n):\n            total += a[right]\n            if total <= s and total > ans:\n                ans = total\n    print(ans)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
