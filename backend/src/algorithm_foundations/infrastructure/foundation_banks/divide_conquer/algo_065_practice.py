from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-065-practice',
    title='平面走査と分割統治の組み合わせ を素直に実装する',
    unit_kind='foundation',
    target_skill='平面走査と分割統治の組み合わせ を素直に実装する',
    concept_overview='全体の個数だけでなく、各点ごとに「左下に何点あるか」を出したいときも、x でまとめて走査しながら y を管理できます。点ごとの寄与を順に記録する形を実装で確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-065-practice-p1',
            title='平面走査と分割統治の組み合わせ を素直に実装する / 各点の左下にある点数を求める',
            problem_statement='平面上の N 個の点 (x_i, y_i) が与えられる。各点 j について、x_i < x_j かつ y_i < y_j を満たす点 i の個数を求めよ。入力順に N 個出力せよ。',
            input_format='1 行目に N。\n続く N 行に x_i y_i。',
            output_format='各点についての個数を空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5\n-10^9 <= x_i, y_i <= 10^9',
            examples=[{'input': '4\n1 1\n2 3\n3 2\n4 4', 'output': '0 1 1 3'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    points = []\n    ys = []\n    for idx in range(n):\n        x, y = map(int, input().split())\n        points.append((x, y, idx))\n        ys.append(y)\n    ys = sorted(set(ys))\n    index = {y: i + 1 for i, y in enumerate(ys)}\n    points.sort()\n    bit = [0] * (len(ys) + 2)\n    answer = [0] * n\n\n    def add(pos: int, value: int) -> None:\n        while pos < len(bit):\n            bit[pos] += value\n            pos += pos & -pos\n\n    def sum_prefix(pos: int) -> int:\n        total = 0\n        while pos > 0:\n            total += bit[pos]\n            pos -= pos & -pos\n        return total\n\n    i = 0\n    while i < n:\n        j = i\n        while j < n and points[j][0] == points[i][0]:\n            j += 1\n        for k in range(i, j):\n            x, y, idx = points[k]\n            answer[idx] = sum_prefix(index[y] - 1)\n        for k in range(i, j):\n            add(index[points[k][1]], 1)\n        i = j\n    print(*answer)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
