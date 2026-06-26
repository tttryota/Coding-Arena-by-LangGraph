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
            title='二次元累積和で長方形和を求める / 長方形の和が K 以上か判定する',
            problem_statement='H 行 W 列の整数表 A と Q 個の問い合わせ `(r1, c1, r2, c2, K)` が与えられる。各長方形の和が K 以上なら Yes、そうでなければ No を出力せよ。',
            input_format='1 行目に H W Q。\n続く H 行に各行の値。\n続く Q 行に r1 c1 r2 c2 K (1-indexed)。',
            output_format='各問い合わせごとに Yes / No を 1 行ずつ出力する。',
            constraints='1 <= H, W, Q <= 2 * 10^3\n|Aij| <= 10^9\n|K| <= 10^18',
            examples=[
                {
                    'input': '3 3 3\n1 2 3\n4 5 6\n7 8 9\n1 1 2 2 12\n2 2 3 3 30\n1 3 3 3 20',
                    'output': 'Yes\nYes\nNo',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    h, w, q = map(int, input().split())\n    prefix = [[0] * (w + 1) for _ in range(h + 1)]\n    for i in range(1, h + 1):\n        row = list(map(int, input().split()))\n        for j in range(1, w + 1):\n            prefix[i][j] = prefix[i - 1][j] + prefix[i][j - 1] - prefix[i - 1][j - 1] + row[j - 1]\n    out = []\n    for _ in range(q):\n        r1, c1, r2, c2, k = map(int, input().split())\n        total = prefix[r2][c2] - prefix[r1 - 1][c2] - prefix[r2][c1 - 1] + prefix[r1 - 1][c1 - 1]\n        out.append('Yes' if total >= k else 'No')\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-099-prefix-sum-2d-p3',
            title='二次元累積和で長方形和を求める / 最も和が大きい長方形を選ぶ',
            problem_statement='H 行 W 列の整数表 A と Q 個の長方形が与えられる。長方形の和が最大になる問い合わせ番号を 1-indexed で出力せよ。最大が複数あるときは最小の番号を選べ。',
            input_format='1 行目に H W Q。\n続く H 行に各行の値。\n続く Q 行に r1 c1 r2 c2 (1-indexed)。',
            output_format='条件を満たす問い合わせ番号を出力する。',
            constraints='1 <= H, W, Q <= 2 * 10^3\n|Aij| <= 10^9',
            examples=[
                {
                    'input': '3 3 3\n1 2 3\n4 5 6\n7 8 9\n1 1 1 3\n1 1 2 2\n2 1 3 3',
                    'output': '3',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    h, w, q = map(int, input().split())\n    prefix = [[0] * (w + 1) for _ in range(h + 1)]\n    for i in range(1, h + 1):\n        row = list(map(int, input().split()))\n        for j in range(1, w + 1):\n            prefix[i][j] = prefix[i - 1][j] + prefix[i][j - 1] - prefix[i - 1][j - 1] + row[j - 1]\n    best_sum = None\n    best_idx = 1\n    for idx in range(1, q + 1):\n        r1, c1, r2, c2 = map(int, input().split())\n        total = prefix[r2][c2] - prefix[r1 - 1][c2] - prefix[r2][c1 - 1] + prefix[r1 - 1][c1 - 1]\n        if best_sum is None or total > best_sum:\n            best_sum = total\n            best_idx = idx\n    print(best_idx)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
