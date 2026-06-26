from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-050-practice',
    title='配るDP・もらうDP を素直に実装する',
    unit_kind='foundation',
    target_skill='配るDP・もらうDP を素直に実装する',
    concept_overview='次は「今ある値を次の状態へ配る」配るDPを使います。壊れたマスがあるときでも、行ける先だけに値を足していけば数え上げできます。',
    problem_bank=[
        problem(
            problem_id='algo-050-practice-p1',
            title='配るDP・もらうDP を素直に実装する / 配るDPで壊れたマスつきの到達方法数を数える',
            problem_statement='長さ N のマス列があり、1 番目のマスから始める。各手番で +1 マスまたは +2 マス進めるが、壊れたマスには止まれない。N 番目のマスに到達する方法数を 10^9+7 で割った余りで求めよ。',
            input_format='1 行目に N M。\nM > 0 のとき 2 行目に壊れたマス番号 b_1..b_M。M = 0 のとき 2 行目は存在しない。',
            output_format='到達方法数を出力する。',
            constraints='1 <= N <= 2 * 10^5\nN = 1 のとき M = 0\nN >= 2 のとき 0 <= M <= N - 2\n2 <= b_i <= N - 1 (M > 0 のとき)',
            examples=[{'input': '6 1\n4', 'output': '2'}],
            canonical_reference_solution="MOD = 10 ** 9 + 7\n\ndef solve() -> None:\n    n, m = map(int, input().split())\n    blocked = set()\n    if m:\n        blocked = set(map(int, input().split()))\n    dp = [0] * (n + 2)\n    dp[1] = 1\n    for pos in range(1, n + 1):\n        if pos in blocked or dp[pos] == 0:\n            continue\n        for nxt in (pos + 1, pos + 2):\n            if nxt <= n and nxt not in blocked:\n                dp[nxt] = (dp[nxt] + dp[pos]) % MOD\n    print(dp[n])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
