from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-040-practice',
    title='区間DP を素直に実装する',
    unit_kind='foundation',
    target_skill='区間DP を素直に実装する',
    concept_overview='区間DPは、列の併合だけでなく、行列積の掛ける順番最適化にもそのまま現れます。ここでは分割点を試して最小計算量を求めます。',
    problem_bank=[
        problem(
            problem_id='algo-040-practice-p1',
            title='区間DP を素直に実装する / 行列積の掛ける順番を最適化する',
            problem_statement='N 個の行列 A1, A2, ..., AN があり、Ai のサイズは r_i x c_i である。行列積 A1A2...AN を計算するときのスカラー乗算回数を最小にせよ。ただし入力は必ず連鎖積が可能なように与えられる。',
            input_format='1 行目に N。\n続く N 行に r_i c_i。',
            output_format='最小のスカラー乗算回数を出力する。',
            constraints='1 <= N <= 400\n1 <= r_i, c_i <= 10^6',
            examples=[{'input': '3\n10 30\n30 5\n5 60', 'output': '4500'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    rows = [0] * n\n    cols = [0] * n\n    for i in range(n):\n        rows[i], cols[i] = map(int, input().split())\n    inf = 10 ** 30\n    dp = [[0] * n for _ in range(n)]\n    for length in range(2, n + 1):\n        for left in range(n - length + 1):\n            right = left + length - 1\n            best = inf\n            for mid in range(left, right):\n                cost = dp[left][mid] + dp[mid + 1][right] + rows[left] * cols[mid] * cols[right]\n                if cost < best:\n                    best = cost\n            dp[left][right] = best\n    print(dp[0][n - 1])\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
