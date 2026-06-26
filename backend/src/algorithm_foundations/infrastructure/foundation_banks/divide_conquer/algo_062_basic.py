from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-062-basic',
    title='最近点対（closest pair） の基本',
    unit_kind='foundation',
    target_skill='最近点対（closest pair） の基本',
    concept_overview='最近点対は、近い点どうしだけを候補として残しながら最小距離を探す知識です。まずは 1 次元で「並べると隣どうしだけ見ればよい」形から考え方をつかみます。',
    problem_bank=[
        problem(
            problem_id='algo-062-basic-p1',
            title='最近点対（closest pair） の基本 / 数直線上の点で最小距離を求める',
            problem_statement='数直線上の N 個の点の座標 x_1, x_2, ..., x_N が与えられる。異なる 2 点の距離 |x_i - x_j| の最小値を求めよ。',
            input_format='1 行目に N。\n2 行目に x_1..x_N。',
            output_format='最小距離を出力する。',
            constraints='2 <= N <= 2 * 10^5\n-10^9 <= x_i <= 10^9',
            examples=[{'input': '5\n8 1 6 3 10', 'output': '2'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    xs = list(map(int, input().split()))\n    xs.sort()\n    ans = min(xs[i + 1] - xs[i] for i in range(n - 1))\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
