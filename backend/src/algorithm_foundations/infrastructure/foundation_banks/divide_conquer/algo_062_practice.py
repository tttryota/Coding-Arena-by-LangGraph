from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-062-practice',
    title='最近点対（closest pair） を素直に実装する',
    unit_kind='foundation',
    target_skill='最近点対（closest pair） を素直に実装する',
    concept_overview='2 次元の最近点対では、点を左右に分けてそれぞれの答えを求め、中央付近だけを見直します。分割統治で比較すべき候補を大きく減らす流れを実装で確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-062-practice-p1',
            title='最近点対（closest pair） を素直に実装する / 平面上の点の最小距離の二乗を求める',
            problem_statement='平面上の N 個の点 (x_i, y_i) が与えられる。異なる 2 点間のユークリッド距離の二乗の最小値を求めよ。',
            input_format='1 行目に N。\n続く N 行に x_i y_i。',
            output_format='最小距離の二乗を出力する。',
            constraints='2 <= N <= 2 * 10^5\n-10^9 <= x_i, y_i <= 10^9',
            examples=[{'input': '4\n0 0\n5 5\n2 1\n7 8', 'output': '5'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    points = [tuple(map(int, input().split())) for _ in range(n)]\n    points.sort()\n\n    def dist2(a: tuple[int, int], b: tuple[int, int]) -> int:\n        dx = a[0] - b[0]\n        dy = a[1] - b[1]\n        return dx * dx + dy * dy\n\n    def rec(ps: list[tuple[int, int]]) -> tuple[int, list[tuple[int, int]]]:\n        m = len(ps)\n        if m <= 3:\n            best = 10 ** 30\n            for i in range(m):\n                for j in range(i + 1, m):\n                    best = min(best, dist2(ps[i], ps[j]))\n            return best, sorted(ps, key=lambda p: p[1])\n        mid = m // 2\n        mid_x = ps[mid][0]\n        best_l, ys_l = rec(ps[:mid])\n        best_r, ys_r = rec(ps[mid:])\n        best = min(best_l, best_r)\n        merged = []\n        i = 0\n        j = 0\n        while i < len(ys_l) and j < len(ys_r):\n            if ys_l[i][1] <= ys_r[j][1]:\n                merged.append(ys_l[i])\n                i += 1\n            else:\n                merged.append(ys_r[j])\n                j += 1\n        merged.extend(ys_l[i:])\n        merged.extend(ys_r[j:])\n        strip = [p for p in merged if (p[0] - mid_x) * (p[0] - mid_x) < best]\n        for i in range(len(strip)):\n            j = i + 1\n            while j < len(strip) and (strip[j][1] - strip[i][1]) * (strip[j][1] - strip[i][1]) < best:\n                best = min(best, dist2(strip[i], strip[j]))\n                j += 1\n        return best, merged\n\n    answer, _ = rec(points)\n    print(answer)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
