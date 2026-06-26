from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-113-practice',
    title='回転・平行移動（アフィン変換） を素直に実装する',
    unit_kind='foundation',
    target_skill='回転・平行移動（アフィン変換） を素直に実装する',
    concept_overview='回転と平行移動の更新則が分かれば、1 点だけでなく複数の点にも同じ操作列を適用できます。ここでは各点に対して同じ手順を繰り返し使い、点の集合をまとめて更新する実装へ広げます。',
    problem_bank=[
        problem(
            problem_id='algo-113-practice-p1',
            title='回転・平行移動（アフィン変換） を素直に実装する / 同じ操作列を複数の点へ適用する',
            problem_statement='平面上の N 個の点と Q 個の操作が与えられる。各操作は `T dx dy` は平行移動、`R` は原点まわりに 90 度反時計回り回転を表す。すべての操作を同じ順にすべての点へ適用した後の座標を、入力順に出力せよ。',
            input_format='1 行目に N。\n続く N 行に xi yi。\n次の 1 行に Q。\n続く Q 行に操作。',
            output_format='N 行出力せよ。i 行目に i 番目の点の最終座標を `x y` で出力する。',
            constraints='1 <= N, Q <= 2000\n座標は整数',
            examples=[{'input': '3\n1 2\n0 1\n-2 0\n3\nT 1 0\nR\nT 0 -1', 'output': '-2 1\n-1 0\n0 -2'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    points = [list(map(int, input().split())) for _ in range(n)]\n    q = int(input())\n    ops = [input().split() for _ in range(q)]\n\n    for point in points:\n        x, y = point\n        for op in ops:\n            if op[0] == 'T':\n                x += int(op[1])\n                y += int(op[2])\n            else:\n                x, y = -y, x\n        print(x, y)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
