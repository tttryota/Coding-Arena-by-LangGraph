from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-047-basic',
    title='確率DP・期待値DP の基本',
    unit_kind='foundation',
    target_skill='確率DP・期待値DP の基本',
    concept_overview='確率DPでは、何回目まで見たかと成功回数のような状態ごとの確率を更新します。1 回の試行結果を次の表へ配り、起こりやすさを積み上げる基本を身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-047-basic-p1',
            title='確率DP・期待値DP の基本 / N 回のコイン投げでちょうど K 回表が出る確率を求める',
            problem_statement='N 枚のコインを順に投げる。コイン i が表になる確率は p_i である。表がちょうど K 回出る確率を求めよ。',
            input_format='1 行目に N K。\n2 行目に p_1..p_N。',
            output_format='確率を小数で出力する。絶対誤差または相対誤差 1e-9 まで許容する。',
            constraints='1 <= N <= 200\n0 <= K <= N\n0.0 <= p_i <= 1.0',
            examples=[{'input': '2 1\n0.5 0.5', 'output': '0.5'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, k = map(int, input().split())\n    probs = list(map(float, input().split()))\n    dp = [0.0] * (k + 1)\n    dp[0] = 1.0\n    for p in probs:\n        nxt = [0.0] * (k + 1)\n        for heads in range(k + 1):\n            nxt[heads] += dp[heads] * (1.0 - p)\n            if heads + 1 <= k:\n                nxt[heads + 1] += dp[heads] * p\n        dp = nxt\n    print(dp[k])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
