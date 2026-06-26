from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-065-basic',
    title='平面走査と分割統治の組み合わせ の基本',
    unit_kind='foundation',
    target_skill='平面走査と分割統治の組み合わせ の基本',
    concept_overview='平面上の点の関係は、x 方向に並べてから y 方向の情報を持つと数えやすくなります。まずは「左下にある点の組数」を数える形で、走査の軸の取り方を確認します。',
    problem_bank=[
        problem(
            problem_id='algo-065-basic-p1',
            title='平面走査と分割統治の組み合わせ の基本 / 左下にある点の組数を数える',
            problem_statement='平面上の N 個の点 (x_i, y_i) が与えられる。x_i < x_j かつ y_i < y_j を満たす組 (i, j) の個数を求めよ。',
            input_format='1 行目に N。\n続く N 行に x_i y_i。',
            output_format='条件を満たす組数を出力する。',
            constraints='1 <= N <= 2 * 10^5\n-10^9 <= x_i, y_i <= 10^9',
            examples=[{'input': '4\n1 1\n2 3\n3 2\n4 4', 'output': '5'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    points = [tuple(map(int, input().split())) for _ in range(n)]\n    ys = sorted({y for _, y in points})\n    index = {y: i + 1 for i, y in enumerate(ys)}\n    points.sort()\n    bit = [0] * (len(ys) + 2)\n\n    def add(pos: int, value: int) -> None:\n        while pos < len(bit):\n            bit[pos] += value\n            pos += pos & -pos\n\n    def sum_prefix(pos: int) -> int:\n        total = 0\n        while pos > 0:\n            total += bit[pos]\n            pos -= pos & -pos\n        return total\n\n    ans = 0\n    i = 0\n    while i < n:\n        j = i\n        while j < n and points[j][0] == points[i][0]:\n            j += 1\n        for k in range(i, j):\n            ans += sum_prefix(index[points[k][1]] - 1)\n        for k in range(i, j):\n            add(index[points[k][1]], 1)\n        i = j\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
