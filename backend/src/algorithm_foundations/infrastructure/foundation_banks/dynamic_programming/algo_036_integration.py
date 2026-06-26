from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-036-integration',
    title='ナップサック問題 の総合演習',
    unit_kind='integration',
    target_skill='ナップサック問題 の総合演習',
    concept_overview='ナップサック DP を 1 回作れば、複数の重さ上限に対する最適値もすぐ答えられます。ここでは同じ品物集合に対して複数の容量質問に答えます。',
    problem_bank=[
        problem(
            problem_id='algo-036-integration-p1',
            title='ナップサック問題 の総合演習 / 重さ上限ごとの最適価値を答える',
            problem_statement='N 個の品物があり、品物 i の重さは w_i、価値は v_i である。Q 個の問い合わせ c_j が与えられるので、重さの合計を c_j 以下にして選ぶときの価値の最大値を各問い合わせについて求めよ。',
            input_format='1 行目に N W Q。\n続く N 行に w_i v_i。\n続く Q 行に c_j。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='1 <= N <= 100\n1 <= W <= 10^5\n1 <= Q <= 2 * 10^5\n1 <= w_i <= W\n1 <= v_i <= 10^9\n0 <= c_j <= W',
            examples=[{'input': '4 9 4\n3 30\n4 50\n5 60\n2 10\n3\n4\n8\n9', 'output': '30\n50\n90\n110'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, w_limit, q = map(int, input().split())\n    dp = [0] * (w_limit + 1)\n    for _ in range(n):\n        weight, value = map(int, input().split())\n        for w in range(w_limit, weight - 1, -1):\n            cand = dp[w - weight] + value\n            if cand > dp[w]:\n                dp[w] = cand\n    for w in range(1, w_limit + 1):\n        if dp[w - 1] > dp[w]:\n            dp[w] = dp[w - 1]\n    out = []\n    for _ in range(q):\n        cap = int(input())\n        out.append(str(dp[cap]))\n    print('\\n'.join(out))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
