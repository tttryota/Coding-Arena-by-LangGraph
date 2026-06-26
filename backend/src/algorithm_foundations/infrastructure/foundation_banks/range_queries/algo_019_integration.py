from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-019-integration',
    title='座標圧縮 の総合演習',
    unit_kind='integration',
    target_skill='座標圧縮 の総合演習',
    concept_overview='座標圧縮は、軸ごとに別々に適用することもできます。ここでは 2 次元の点集合に対して x 座標と y 座標を独立に圧縮します。',
    problem_bank=[
        problem(
            problem_id='algo-019-integration-p1',
            title='座標圧縮 の総合演習 / 2 次元の点を x 座標と y 座標で別々に圧縮する',
            problem_statement='N 個の点 (x_i, y_i) が与えられる。x 座標どうし、y 座標どうしをそれぞれ独立に座標圧縮し、各点の圧縮後の座標を入力順に出力せよ。',
            input_format='1 行目に N。\n続く N 行に x_i y_i。',
            output_format='各点について、圧縮後の x_i\' と y_i\' を 1 行ずつ出力する。',
            constraints='1 <= N <= 2 * 10^5\n-10^18 <= x_i, y_i <= 10^18',
            examples=[{'input': '3\n100 1000\n50 200\n100 200', 'output': '1 1\n0 0\n1 0'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    points = [tuple(map(int, input().split())) for _ in range(n)]\n    xs = {value: idx for idx, value in enumerate(sorted({x for x, _ in points}))}\n    ys = {value: idx for idx, value in enumerate(sorted({y for _, y in points}))}\n    out = [f\"{xs[x]} {ys[y]}\" for x, y in points]\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
