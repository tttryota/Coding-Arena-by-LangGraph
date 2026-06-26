from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-042-practice',
    title='bitDP（集合に対するDP） を素直に実装する',
    unit_kind='foundation',
    target_skill='bitDP（集合に対するDP） を素直に実装する',
    concept_overview='bitDP に禁止条件が入っても、集合状態から「次に置けるものだけ」へ遷移する形は変わりません。ここでは割り当て不可の組を飛ばしながら最小値を作ります。',
    problem_bank=[
        problem(
            problem_id='algo-042-practice-p1',
            title='bitDP（集合に対するDP） を素直に実装する / 禁止割当つきで最小コストを求める',
            problem_statement='N 人の作業者と N 個の仕事があり、cost[i][j] は作業者 i を仕事 j に割り当てるコストである。ただし cost[i][j] = -1 の組み合わせは割り当て禁止を表す。全員に異なる仕事を 1 つずつ割り当てる最小総コストを求め、無理なら -1 を出力せよ。',
            input_format='1 行目に N。\n続く N 行に cost[i][1..N]。',
            output_format='最小総コスト、無理なら -1 を出力する。',
            constraints='1 <= N <= 16\n-1 <= cost[i][j] <= 10^9',
            examples=[{'input': '3\n4 -1 3\n2 0 5\n-1 2 2', 'output': '6'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    cost = [list(map(int, input().split())) for _ in range(n)]\n    inf = 10 ** 18\n    dp = [inf] * (1 << n)\n    dp[0] = 0\n    for mask in range(1 << n):\n        i = mask.bit_count()\n        if i == n or dp[mask] == inf:\n            continue\n        for job in range(n):\n            if mask >> job & 1:\n                continue\n            if cost[i][job] == -1:\n                continue\n            nxt = mask | (1 << job)\n            cand = dp[mask] + cost[i][job]\n            if cand < dp[nxt]:\n                dp[nxt] = cand\n    print(-1 if dp[-1] == inf else dp[-1])\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
