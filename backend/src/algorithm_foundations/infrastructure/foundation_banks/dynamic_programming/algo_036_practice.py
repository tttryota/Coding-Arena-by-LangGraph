from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-036-practice',
    title='ナップサック問題 を素直に実装する',
    unit_kind='foundation',
    target_skill='ナップサック問題 を素直に実装する',
    concept_overview='ナップサック DP は、最大価値だけでなく「どの品物を選んだか」も復元できます。ここでは最適値を作る品物集合をたどり直します。',
    problem_bank=[
        problem(
            problem_id='algo-036-practice-p1',
            title='ナップサック問題 を素直に実装する / 最適な品物集合を復元する',
            problem_statement='N 個の品物があり、品物 i の重さは w_i、価値は v_i である。重さの合計を W 以下にして選ぶとき、得られる価値の最大値と、その最大値を達成する品物番号の集合を 1 つ求めよ。',
            input_format='1 行目に N W。\n続く N 行に w_i v_i。',
            output_format='1 行目に価値の最大値、2 行目に選んだ品物数 K、3 行目に選んだ品物番号を昇順で空白区切りにして出力する。K = 0 のとき 3 行目は空行でよい。',
            constraints='1 <= N <= 100\n1 <= W <= 5000\n1 <= w_i <= W\n1 <= v_i <= 10^9',
            examples=[{'input': '4 9\n3 30\n4 50\n5 60\n2 10', 'output': '110\n2\n2 3'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, w_limit = map(int, input().split())\n    items = [tuple(map(int, input().split())) for _ in range(n)]\n    dp = [[0] * (w_limit + 1) for _ in range(n + 1)]\n    for i, (weight, value) in enumerate(items, start=1):\n        prev = dp[i - 1]\n        cur = dp[i]\n        for w in range(w_limit + 1):\n            best = prev[w]\n            if w >= weight:\n                cand = prev[w - weight] + value\n                if cand > best:\n                    best = cand\n            cur[w] = best\n    best_weight = max(range(w_limit + 1), key=lambda w: dp[n][w])\n    ans = dp[n][best_weight]\n    chosen = []\n    w = best_weight\n    for i in range(n, 0, -1):\n        if dp[i][w] == dp[i - 1][w]:\n            continue\n        chosen.append(i)\n        w -= items[i - 1][0]\n    chosen.reverse()\n    print(ans)\n    print(len(chosen))\n    print(*chosen)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
