from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-036-basic',
    title='ナップサック問題 の基本',
    unit_kind='foundation',
    target_skill='ナップサック問題 の基本',
    concept_overview='ナップサック問題では、品物を取る・取らないの 2 通りを重さ制限つきで積み上げ、重さごとの最良価値を更新します。何個目まで見たかと今の重さを状態にする基本を身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-036-basic-p1',
            title='ナップサック問題 の基本 / 重さ制限つきで価値の最大値を求める',
            problem_statement='N 個の品物があり、品物 i の重さは w_i、価値は v_i である。重さの合計を W 以下にして選ぶとき、得られる価値の最大値を求めよ。',
            input_format='1 行目に N W。\n続く N 行に w_i v_i。',
            output_format='価値の最大値を出力する。',
            constraints='1 <= N <= 100\n1 <= W <= 10^5\n1 <= w_i <= W\n1 <= v_i <= 10^9',
            examples=[{'input': '3 8\n3 30\n4 50\n5 60', 'output': '90'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, w = map(int, input().split())\n    dp = [0] * (w + 1)\n    for _ in range(n):\n        weight, value = map(int, input().split())\n        for cur in range(w, weight - 1, -1):\n            dp[cur] = max(dp[cur], dp[cur - weight] + value)\n    print(max(dp))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
