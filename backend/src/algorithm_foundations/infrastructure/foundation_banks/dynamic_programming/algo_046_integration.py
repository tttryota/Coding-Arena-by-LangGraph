from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-046-integration',
    title='グリッドDP（経路数え上げ） の総合演習',
    unit_kind='integration',
    target_skill='グリッドDP（経路数え上げ） の総合演習',
    concept_overview='グリッドDPは、遷移を 1 種類増やしても同じ考え方で拡張できます。ここでは右・下に加えて右下斜めも許す形で通り数を数えます。',
    problem_bank=[
        problem(
            problem_id='algo-046-integration-p1',
            title='グリッドDP（経路数え上げ） の総合演習 / 右・下・右下で進む通り数を数える',
            problem_statement='H 行 W 列のグリッドがあり、`.` は通行可能、`#` は障害物を表す。左上から右下へ、右・下・右下の 3 通りで 1 マスずつ動くとき、到達方法数を 10^9+7 で割った余りで求めよ。',
            input_format='1 行目に H W。\n続く H 行にグリッド。',
            output_format='到達方法数を出力する。',
            constraints='1 <= H, W <= 1000',
            examples=[{'input': '3 4\n...#\n....\n#...', 'output': '23'}],
            canonical_reference_solution="MOD = 10 ** 9 + 7\n\n\ndef solve() -> None:\n    h, w = map(int, input().split())\n    grid = [input().strip() for _ in range(h)]\n    dp = [[0] * w for _ in range(h)]\n    if grid[0][0] == '.':\n        dp[0][0] = 1\n    for i in range(h):\n        for j in range(w):\n            if grid[i][j] == '#':\n                continue\n            if i > 0:\n                dp[i][j] += dp[i - 1][j]\n            if j > 0:\n                dp[i][j] += dp[i][j - 1]\n            if i > 0 and j > 0:\n                dp[i][j] += dp[i - 1][j - 1]\n            dp[i][j] %= MOD\n    print(dp[h - 1][w - 1])\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
