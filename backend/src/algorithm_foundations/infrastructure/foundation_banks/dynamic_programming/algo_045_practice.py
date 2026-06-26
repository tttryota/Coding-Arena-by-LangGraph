from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-045-practice',
    title='コイン問題（最小枚数） を素直に実装する',
    unit_kind='foundation',
    target_skill='コイン問題（最小枚数） を素直に実装する',
    concept_overview='無制限に使えるコインの最小枚数が分かったら、次は「各額面を何枚まで使えるか」という上限つきにも進めます。ここでは coin type ごとに使える枚数制限を持たせ、最小枚数 DP を 2 次元で組み立てます。',
    problem_bank=[
        problem(
            problem_id='algo-045-practice-p1',
            title='コイン問題（最小枚数） を素直に実装する / 枚数上限つきで目標金額を作る最小枚数を求める',
            problem_statement='M 種類のコインの額面 c_i、使える枚数上限 a_i、目標金額 X が与えられる。各種類 i のコインは高々 a_i 枚まで使えるとして、合計をちょうど X にする最小枚数を求めよ。できなければ -1 を出力せよ。',
            input_format='1 行目に M X。\n2 行目に c_1..c_M。\n3 行目に a_1..a_M。',
            output_format='最小枚数、できなければ -1 を出力する。',
            constraints='1 <= M <= 50\n1 <= X <= 10^4\n1 <= c_i <= 10^4\n0 <= a_i <= 50',
            examples=[{'input': '3 11\n1 5 7\n1 2 1', 'output': '3'}],
            canonical_reference_solution="def solve() -> None:\n    m, x = map(int, input().split())\n    coins = list(map(int, input().split()))\n    limits = list(map(int, input().split()))\n    inf = 10 ** 18\n    dp = [inf] * (x + 1)\n    dp[0] = 0\n    for coin, limit in zip(coins, limits, strict=False):\n        nxt = dp[:]\n        for total in range(x + 1):\n            if dp[total] == inf:\n                continue\n            for count in range(1, limit + 1):\n                value = total + coin * count\n                if value > x:\n                    break\n                cand = dp[total] + count\n                if cand < nxt[value]:\n                    nxt[value] = cand\n        dp = nxt\n    print(-1 if dp[x] == inf else dp[x])\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
