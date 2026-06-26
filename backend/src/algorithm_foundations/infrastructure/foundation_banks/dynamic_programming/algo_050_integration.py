from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-050-integration',
    title='配るDP・もらうDP の総合演習',
    unit_kind='integration',
    target_skill='配るDP・もらうDP の総合演習',
    concept_overview='配るDP・もらうDPは、遷移先や受け取り元が少し増えても同じ考え方で拡張できます。ここでは壊れたマスつきで、+1・+2・+3 の 3 通りの遷移をもらうDPで数えます。',
    problem_bank=[
        problem(
            problem_id='algo-050-integration-p1',
            title='配るDP・もらうDP の総合演習 / 壊れたマスつきで +1・+2・+3 遷移の到達方法数を数える',
            problem_statement='長さ N のマス列があり、1 番目のマスから始める。各手番で +1 マス、+2 マス、+3 マス進めるが、壊れたマスには止まれない。N 番目のマスに到達する方法数を 10^9+7 で割った余りで求めよ。',
            input_format='1 行目に N M。\nM > 0 のとき 2 行目に壊れたマス番号 b_1..b_M。M = 0 のとき 2 行目は存在しない。',
            output_format='到達方法数を出力する。',
            constraints='1 <= N <= 2 * 10^5\nN = 1 のとき M = 0\nN >= 2 のとき 0 <= M <= N - 2\n2 <= b_i <= N - 1 (M > 0 のとき)',
            examples=[{'input': '6 1\n4', 'output': '5'}],
            canonical_reference_solution="MOD = 10 ** 9 + 7\n\n\ndef solve() -> None:\n    n, m = map(int, input().split())\n    blocked = set(map(int, input().split())) if m else set()\n    dp = [0] * (n + 3)\n    dp[1] = 1\n    for pos in range(2, n + 1):\n        if pos in blocked:\n            continue\n        for step in (1, 2, 3):\n            prev = pos - step\n            if prev >= 1:\n                dp[pos] += dp[prev]\n        dp[pos] %= MOD\n    print(dp[n])\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
