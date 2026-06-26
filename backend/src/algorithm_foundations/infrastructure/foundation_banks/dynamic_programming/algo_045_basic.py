from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-045-basic',
    title='コイン問題（最小枚数） の基本',
    unit_kind='foundation',
    target_skill='コイン問題（最小枚数） の基本',
    concept_overview='コイン問題では、金額 x を作る最小枚数を小さい金額から更新し、既知の最小値を次の金額へ配ります。到達できる金額の最良値を前から伸ばす DP の基本を身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-045-basic-p1',
            title='コイン問題（最小枚数） の基本 / 目標金額を作る最小枚数を求める',
            problem_statement='M 種類のコインの額面 c_i と目標金額 X が与えられる。各コインは何枚でも使えるとして、合計をちょうど X にする最小枚数を求めよ。できなければ -1 を出力せよ。',
            input_format='1 行目に M X。\n2 行目に c_1..c_M。',
            output_format='最小枚数、できなければ -1 を出力する。',
            constraints='1 <= M <= 50\n1 <= X <= 10^5\n1 <= c_i <= 10^5',
            examples=[{'input': '3 11\n1 5 7', 'output': '3'}],
            canonical_reference_solution="def solve() -> None:\n    m, x = map(int, input().split())\n    coins = list(map(int, input().split()))\n    inf = 10 ** 18\n    dp = [inf] * (x + 1)\n    dp[0] = 0\n    for total in range(x + 1):\n        if dp[total] == inf:\n            continue\n        for coin in coins:\n            nxt = total + coin\n            if nxt <= x:\n                dp[nxt] = min(dp[nxt], dp[total] + 1)\n    print(-1 if dp[x] == inf else dp[x])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
