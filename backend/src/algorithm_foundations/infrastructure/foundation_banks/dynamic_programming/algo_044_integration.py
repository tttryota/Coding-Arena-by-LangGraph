from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-044-integration',
    title='部分和問題 の総合演習',
    unit_kind='integration',
    target_skill='部分和問題 の総合演習',
    concept_overview='部分和問題は、「何個選んだか」という条件を状態に足すと別の練習になります。ここではちょうど K 個選んで S を作れるかを判定します。',
    problem_bank=[
        problem(
            problem_id='algo-044-integration-p1',
            title='部分和問題 の総合演習 / ちょうど K 個選んで S を作れるか判定する',
            problem_statement='N 個の正整数 A と整数 K, S が与えられる。ちょうど K 個の要素を選んで合計を S にできるなら Yes、できなければ No を出力せよ。',
            input_format='1 行目に N K S。\n2 行目に A1..AN。',
            output_format='Yes / No を出力する。',
            constraints='1 <= N <= 100\n0 <= K <= N\n1 <= S <= 2 * 10^5',
            examples=[{'input': '5 2 11\n2 5 9 4 7', 'output': 'Yes'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, k, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    dp = [[False] * (s + 1) for _ in range(k + 1)]\n    dp[0][0] = True\n    for value in a:\n        for cnt in range(k - 1, -1, -1):\n            for total in range(s - value + 1):\n                if dp[cnt][total]:\n                    dp[cnt + 1][total + value] = True\n    print('Yes' if dp[k][s] else 'No')\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
