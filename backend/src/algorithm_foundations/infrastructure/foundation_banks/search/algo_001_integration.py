from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-001-integration',
    title='全探索（ブルートフォース） の総合演習',
    unit_kind='integration',
    target_skill='全探索（ブルートフォース） の総合演習',
    concept_overview='連続部分列を全部試す全探索では、条件を満たす区間の個数までそのまま数えられます。ここでは総和がちょうど S の区間数を数えます。',
    problem_bank=[
        problem(
            problem_id='algo-001-integration-p1',
            title='全探索（ブルートフォース） の総合演習 / 総和がちょうど S の連続部分列の個数を数える',
            problem_statement='長さ N の正整数列 A と整数 S が与えられる。総和がちょうど S になる連続部分列の個数を求めよ。',
            input_format='1 行目に N S。\n2 行目に A1..AN。',
            output_format='個数を出力する。',
            constraints='1 <= N <= 2000\n1 <= A_i, S <= 10^9',
            examples=[{'input': '5 5\n1 2 3 2 2', 'output': '2'}],
            canonical_reference_solution="def solve() -> None:\n    n, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    ans = 0\n    for left in range(n):\n        total = 0\n        for right in range(left, n):\n            total += a[right]\n            if total == s:\n                ans += 1\n    print(ans)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
