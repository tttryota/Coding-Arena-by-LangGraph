from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-046-practice',
    title='グリッドDP（経路数え上げ） を素直に実装する',
    unit_kind='foundation',
    target_skill='グリッドDP（経路数え上げ） を素直に実装する',
    concept_overview='グリッドDPの表が作れると、ある通過点を必ず通る経路数も求められます。ここでは始点からの表と終点への表を組み合わせ、指定マスを経由する経路数を数えます。',
    problem_bank=[
        problem(
            problem_id='algo-046-practice-p1',
            title='グリッドDP（経路数え上げ） を素直に実装する / 指定マスを必ず通る経路数を数える',
            problem_statement='H 行 W 列のグリッドがあり、`.` は通行可能、`#` は障害物を表す。左上から右下へ、右または下に 1 マスずつ動く。指定されたマス `(R, C)` を必ず通る経路数を 10^9+7 で割った余りで求めよ。指定マスが障害物なら答えは 0 である。',
            input_format='1 行目に H W R C。\n続く H 行にグリッド。',
            output_format='条件を満たす経路数を出力する。',
            constraints='1 <= H, W <= 1000',
            examples=[{'input': '3 4 2 3\n...#\n....\n#...', 'output': '6'}],
            canonical_reference_solution="MOD = 10 ** 9 + 7\n\n\ndef solve() -> None:\n    h, w, r, c = map(int, input().split())\n    r -= 1\n    c -= 1\n    grid = [input().strip() for _ in range(h)]\n    if grid[r][c] == '#':\n        print(0)\n        return\n\n    from_start = [[0] * w for _ in range(h)]\n    if grid[0][0] == '.':\n        from_start[0][0] = 1\n    for i in range(h):\n        for j in range(w):\n            if grid[i][j] == '#':\n                continue\n            if i > 0:\n                from_start[i][j] += from_start[i - 1][j]\n            if j > 0:\n                from_start[i][j] += from_start[i][j - 1]\n            from_start[i][j] %= MOD\n\n    to_goal = [[0] * w for _ in range(h)]\n    if grid[h - 1][w - 1] == '.':\n        to_goal[h - 1][w - 1] = 1\n    for i in range(h - 1, -1, -1):\n        for j in range(w - 1, -1, -1):\n            if grid[i][j] == '#':\n                continue\n            if i + 1 < h:\n                to_goal[i][j] += to_goal[i + 1][j]\n            if j + 1 < w:\n                to_goal[i][j] += to_goal[i][j + 1]\n            to_goal[i][j] %= MOD\n\n    print(from_start[r][c] * to_goal[r][c] % MOD)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
