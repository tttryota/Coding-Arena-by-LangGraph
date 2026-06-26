from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-050-basic',
    title='配るDP・もらうDP の基本',
    unit_kind='foundation',
    target_skill='配るDP・もらうDP の基本',
    concept_overview='配るDP・もらうDPのうち、まずは「前の状態から今の値を受け取る」もらうDPを練習します。単純な +1 / +2 遷移なら、各マスは直前 2 マスから受け取れます。',
    problem_bank=[
        problem(
            problem_id='algo-050-basic-p1',
            title='配るDP・もらうDP の基本 / もらうDPで到達方法数を数える',
            problem_statement='長さ N のマス列があり、1 番目のマスから始める。各手番で +1 マスまたは +2 マス進む。壊れたマスはないとして、N 番目のマスに到達する方法数を 10^9+7 で割った余りで求めよ。',
            input_format='1 行目に N。',
            output_format='到達方法数を出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[{'input': '6', 'output': '8'}],
            canonical_reference_solution="MOD = 10 ** 9 + 7\n\n\ndef solve() -> None:\n    n = int(input())\n    dp = [0] * (n + 2)\n    dp[1] = 1\n    for pos in range(2, n + 1):\n        dp[pos] = (dp[pos - 1] + dp[pos - 2]) % MOD\n    print(dp[n])\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
