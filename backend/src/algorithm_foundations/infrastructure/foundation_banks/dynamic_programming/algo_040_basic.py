from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-040-basic',
    title='区間DP の基本',
    unit_kind='foundation',
    target_skill='区間DP の基本',
    concept_overview='区間DPでは、区間 [l, r] をどう処理し終えるかを状態にし、分割点を全探索して左右の答えを結合します。長さの短い区間から順に埋める流れを身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-040-basic-p1',
            title='区間DP の基本 / 列全体を 1 つにする最小コストを求める',
            problem_statement='長さ N の正整数列 A が与えられる。 隣り合う区間を順に併合するとき、併合コストを区間和とする。 列全体を 1 つにする最小コストを求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='最小コストを出力する。',
            constraints='1 <= N <= 400\n1 <= Ai <= 10^9',
            examples=[{'input': '4\n4 1 3 2', 'output': '20'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    a = list(map(int, input().split()))\n    prefix = [0]\n    for value in a:\n        prefix.append(prefix[-1] + value)\n    dp = [[0] * n for _ in range(n)]\n    for length in range(2, n + 1):\n        for left in range(n - length + 1):\n            right = left + length - 1\n            total = prefix[right + 1] - prefix[left]\n            best = 10 ** 30\n            for mid in range(left, right):\n                best = min(best, dp[left][mid] + dp[mid + 1][right] + total)\n            dp[left][right] = best\n    print(dp[0][n - 1])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
