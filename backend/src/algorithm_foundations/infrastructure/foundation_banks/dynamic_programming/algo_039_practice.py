from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-039-practice',
    title='編集距離（レーベンシュタイン距離） を素直に実装する',
    unit_kind='foundation',
    target_skill='編集距離（レーベンシュタイン距離） を素直に実装する',
    concept_overview='編集距離 DP は、操作ごとのコストを変えても同じ形で使えます。ここでは挿入・削除・置換の重みつき最小コストを求めます。',
    problem_bank=[
        problem(
            problem_id='algo-039-practice-p1',
            title='編集距離（レーベンシュタイン距離） を素直に実装する / 操作コストつき編集距離を求める',
            problem_statement='2 つの文字列 S, T と、挿入コスト A、削除コスト B、置換コスト C が与えられる。S を T に変える最小コストを求めよ。',
            input_format='1 行目に A B C。\n2 行目に S。\n3 行目に T。',
            output_format='最小コストを出力する。',
            constraints='1 <= |S|, |T| <= 2000\n1 <= A, B, C <= 10^9',
            examples=[{'input': '1 1 2\nkitten\nsitting', 'output': '5'}],
            canonical_reference_solution="def solve() -> None:\n    add_cost, del_cost, rep_cost = map(int, input().split())\n    s = input().strip()\n    t = input().strip()\n    n, m = len(s), len(t)\n    dp = [[0] * (m + 1) for _ in range(n + 1)]\n    for i in range(1, n + 1):\n        dp[i][0] = i * del_cost\n    for j in range(1, m + 1):\n        dp[0][j] = j * add_cost\n    for i in range(1, n + 1):\n        for j in range(1, m + 1):\n            keep_or_replace = dp[i - 1][j - 1] + (0 if s[i - 1] == t[j - 1] else rep_cost)\n            dp[i][j] = min(\n                dp[i - 1][j] + del_cost,\n                dp[i][j - 1] + add_cost,\n                keep_or_replace,\n            )\n    print(dp[n][m])\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
