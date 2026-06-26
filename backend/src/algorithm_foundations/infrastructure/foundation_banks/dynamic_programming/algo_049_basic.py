from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-049-basic',
    title='累積和を用いたDP高速化 の基本',
    unit_kind='foundation',
    target_skill='累積和を用いたDP高速化 の基本',
    concept_overview='この unit では、累積和を DP の遷移和に使って 1 状態ごとの全探索を省きます。まずは「直前 K 個の dp の和」を prefix でまとめる基本形を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-049-basic-p1',
            title='累積和を用いたDP高速化 の基本 / 1 歩で 1 以上 K 以下進めるとき、 ちょうど N に到達する方法数を 10^9+7 で割った余りで求めよ',
            problem_statement='整数 N, K が与えられる。1 歩で 1 以上 K 以下進めるとき、 ちょうど N に到達する方法数を 10^9+7 で割った余りで求めよ。',
            input_format='1 行目に N K。',
            output_format='方法数を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= K <= 2 * 10^5',
            examples=[{'input': '4 2', 'output': '5'}],
            canonical_reference_solution="MOD = 10 ** 9 + 7\n\ndef solve() -> None:\n    n, k = map(int, input().split())\n    dp = [0] * (n + 1)\n    pref = [0] * (n + 2)\n    dp[0] = 1\n    pref[1] = 1\n    for i in range(1, n + 1):\n        left = max(0, i - k)\n        dp[i] = (pref[i] - pref[left]) % MOD\n        pref[i + 1] = (pref[i] + dp[i]) % MOD\n    print(dp[n])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
