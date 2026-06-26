from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-039-basic',
    title='編集距離（レーベンシュタイン距離） の基本',
    unit_kind='foundation',
    target_skill='編集距離（レーベンシュタイン距離） の基本',
    concept_overview='編集距離では、挿入・削除・置換の 3 操作を prefix 同士の表で比較し、1 文字ずつ合わせる最小コストを求めます。左・上・左上から遷移する DP の読み方を身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-039-basic-p1',
            title='編集距離（レーベンシュタイン距離） の基本 / 編集距離を求める',
            problem_statement='2 つの文字列 S, T が与えられる。編集距離を求めよ。',
            input_format='1 行目に S。\n2 行目に T。',
            output_format='編集距離を出力する。',
            constraints='1 <= |S|, |T| <= 2000',
            examples=[{'input': 'kitten\nsitting', 'output': '3'}],
            canonical_reference_solution="def solve() -> None:\n    s = input().strip()\n    t = input().strip()\n    dp = [[0] * (len(t) + 1) for _ in range(len(s) + 1)]\n    for i in range(len(s) + 1):\n        dp[i][0] = i\n    for j in range(len(t) + 1):\n        dp[0][j] = j\n    for i, ch in enumerate(s, start=1):\n        for j, tch in enumerate(t, start=1):\n            cost = 0 if ch == tch else 1\n            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)\n    print(dp[-1][-1])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
