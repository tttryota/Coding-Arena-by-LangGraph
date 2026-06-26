from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-046-basic',
    title='グリッドDP（経路数え上げ） の基本',
    unit_kind='foundation',
    target_skill='グリッドDP（経路数え上げ） の基本',
    concept_overview='グリッドDPでは、各マスへの到達方法数を上と左から受け取り、通れないマスを飛ばしながら表を埋めます。二次元の表でここまでの通り数を積み上げる基本を身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-046-basic-p1',
            title='グリッドDP（経路数え上げ） の基本 / 障害物つきグリッドの経路数を数える',
            problem_statement='H 行 W 列のグリッドがあり、`.` は通行可能、`#` は障害物を表す。左上から右下へ、右または下に 1 マスずつ動くとき、到達方法数を 10^9+7 で割った余りで求めよ。',
            input_format='1 行目に H W。\n続く H 行にグリッド。',
            output_format='到達方法数を出力する。',
            constraints='1 <= H, W <= 1000',
            examples=[{'input': '3 4\n...#\n....\n#...', 'output': '8'}],
            canonical_reference_solution="MOD = 10 ** 9 + 7\n\ndef solve() -> None:\n    h, w = map(int, input().split())\n    grid = [input().strip() for _ in range(h)]\n    dp = [[0] * w for _ in range(h)]\n    if grid[0][0] == '.':\n        dp[0][0] = 1\n    for i in range(h):\n        for j in range(w):\n            if grid[i][j] == '#':\n                continue\n            if i > 0:\n                dp[i][j] += dp[i - 1][j]\n            if j > 0:\n                dp[i][j] += dp[i][j - 1]\n            dp[i][j] %= MOD\n    print(dp[h - 1][w - 1])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
