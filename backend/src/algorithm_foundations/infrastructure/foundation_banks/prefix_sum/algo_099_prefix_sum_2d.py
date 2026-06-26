from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-099-prefix-sum-2d',
    title='二次元累積和で長方形和を求める',
    unit_kind='integration',
    target_skill='二次元累積和で長方形和を求める',
    concept_overview='二次元累積和は、長方形の和を四隅の足し引きに変えて素早く求める考え方です。表を前計算し、問い合わせを定数時間で処理する練習をします。',
    problem_bank=[
        problem(
            problem_id='algo-099-prefix-sum-2d-p1',
            title='二次元累積和で長方形和を求める / 長方形ごとの和を順に答える',
            problem_statement='H 行 W 列の整数表 A と Q 個の長方形が与えられる。各問い合わせについて、左上 (r1, c1)、右下 (r2, c2) に囲まれる長方形の総和を求めよ。',
            input_format='1 行目に H W Q。\n続く H 行に各行の値。\n続く Q 行に r1 c1 r2 c2 (1-indexed)。',
            output_format='各問い合わせの長方形和を 1 行ずつ出力する。',
            constraints='1 <= H, W, Q <= 2 * 10^3\n|Aij| <= 10^9',
            examples=[
                {
                    'input': '2 3 2\n1 2 3\n4 5 6\n1 1 2 2\n2 2 2 3',
                    'output': '12\n11',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    h, w, q = map(int, input().split())\n    prefix = [[0] * (w + 1) for _ in range(h + 1)]\n    for i in range(1, h + 1):\n        row = list(map(int, input().split()))\n        for j in range(1, w + 1):\n            prefix[i][j] = prefix[i - 1][j] + prefix[i][j - 1] - prefix[i - 1][j - 1] + row[j - 1]\n    out = []\n    for _ in range(q):\n        r1, c1, r2, c2 = map(int, input().split())\n        total = prefix[r2][c2] - prefix[r1 - 1][c2] - prefix[r2][c1 - 1] + prefix[r1 - 1][c1 - 1]\n        out.append(str(total))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-099-prefix-sum-2d-p2',
            title='二次元累積和で長方形和を求める / 二次元累積和表をそのまま作る',
            problem_statement='H 行 W 列の整数表 A が与えられる。二次元累積和 P を `P[i][j] = A[1][1]` から `A[i][j]` までの長方形和と定義する。P の各行を出力せよ。',
            input_format='1 行目に H W。\n続く H 行に各行の値。',
            output_format='H 行にわたり、二次元累積和表 P の各行を空白区切りで出力する。',
            constraints='1 <= H, W <= 2 * 10^3\n|Aij| <= 10^9',
            examples=[
                {
                    'input': '3 3\n1 2 3\n4 5 6\n7 8 9',
                    'output': '1 3 6\n5 12 21\n12 27 45',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    h, w = map(int, input().split())\n    prefix = [[0] * (w + 1) for _ in range(h + 1)]\n    for i in range(1, h + 1):\n        row = list(map(int, input().split()))\n        for j in range(1, w + 1):\n            prefix[i][j] = prefix[i - 1][j] + prefix[i][j - 1] - prefix[i - 1][j - 1] + row[j - 1]\n    for i in range(1, h + 1):\n        print(*prefix[i][1:])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-099-prefix-sum-2d-p3',
            title='二次元累積和で長方形和を求める / 二次元累積和表から元の表を復元する',
            problem_statement='H 行 W 列の整数表 P が与えられる。P[i][j] は、ある整数表 A の左上 `(1, 1)` から `(i, j)` までの長方形和を表している。元の表 A を復元して出力せよ。',
            input_format='1 行目に H W。\n続く H 行に P の各行。',
            output_format='H 行にわたり、復元した表 A の各行を空白区切りで出力する。',
            constraints='1 <= H, W <= 2 * 10^3\n|Pij| <= 10^18',
            examples=[
                {
                    'input': '3 3\n1 3 6\n5 12 21\n12 27 45',
                    'output': '1 2 3\n4 5 6\n7 8 9',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    h, w = map(int, input().split())\n    prefix = [[0] * (w + 1)]\n    for _ in range(h):\n        prefix.append([0] + list(map(int, input().split())))\n    for i in range(1, h + 1):\n        row = []\n        for j in range(1, w + 1):\n            value = prefix[i][j] - prefix[i - 1][j] - prefix[i][j - 1] + prefix[i - 1][j - 1]\n            row.append(str(value))\n        print(' '.join(row))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
