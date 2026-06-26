from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-049-practice',
    title='累積和を用いたDP高速化 を素直に実装する',
    unit_kind='foundation',
    target_skill='累積和を用いたDP高速化 を素直に実装する',
    concept_overview='累積和で DP を速くするときも、壊れたマスや禁止位置が入っても同じです。ここでは通れない位置を飛ばしつつ、区間和で遷移数をまとめます。',
    problem_bank=[
        problem(
            problem_id='algo-049-practice-p1',
            title='累積和を用いたDP高速化 を素直に実装する / 壊れたマスを避けて N に到達する方法数を数える',
            problem_statement='1 から N まで番号の付いたマス列がある。マス 1 から始め、1 回で 1 以上 K 以下進める。壊れたマスには止まれないとして、マス N に到達する方法数を 10^9+7 で割った余りで求めよ。',
            input_format='1 行目に N K M。\nM > 0 のとき 2 行目に壊れたマス番号 b_1..b_M。M = 0 のとき 2 行目は存在しない。',
            output_format='方法数を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= K <= 2 * 10^5\n0 <= M <= N - 1\n2 <= b_i <= N',
            examples=[{'input': '6 2 1\n4', 'output': '2'}],
            canonical_reference_solution="MOD = 10 ** 9 + 7\n\n\ndef solve() -> None:\n    n, k, m = map(int, input().split())\n    blocked = set(map(int, input().split())) if m else set()\n    dp = [0] * (n + 1)\n    pref = [0] * (n + 2)\n    dp[1] = 1\n    pref[2] = 1\n    for i in range(2, n + 1):\n        if i in blocked:\n            pref[i + 1] = pref[i]\n            continue\n        left = max(1, i - k)\n        dp[i] = (pref[i] - pref[left]) % MOD\n        pref[i + 1] = (pref[i] + dp[i]) % MOD\n    print(dp[n])\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
