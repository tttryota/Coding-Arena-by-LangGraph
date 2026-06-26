from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-100-integration',
    title='いもす法 の総合演習',
    unit_kind='integration',
    target_skill='いもす法 の総合演習',
    concept_overview='いもす法は 2 次元にも広げられます。長方形更新を差分として記録し、縦横に累積して盤面を復元したあと、さらに 2 次元累積和を重ねると長方形和の問い合わせまで処理できます。',
    problem_bank=[
        problem(
            problem_id='algo-100-integration-p1',
            title='いもす法 の総合演習 / 長方形加算後の盤面に対する長方形和問い合わせを処理する',
            problem_statement='H 行 W 列の盤面に対して Q 個の加算操作が与えられる。`r1 c1 r2 c2 x` は長方形 `[r1, r2] x [c1, c2]` のすべてのマスに x を足す。すべての更新を適用したあと、M 個の問い合わせ `[r1, r2] x [c1, c2]` それぞれについて、その長方形内の総和を求めよ。',
            input_format='1 行目に H W Q M。\n続く Q 行に r1 c1 r2 c2 x。\n続く M 行に r1 c1 r2 c2。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='1 <= H, W <= 500\n1 <= Q, M <= 2 * 10^5\n-10^9 <= x <= 10^9\n1 <= r1 <= r2 <= H\n1 <= c1 <= c2 <= W',
            examples=[{'input': '3 4 2 3\n1 1 2 3 1\n2 2 3 4 2\n1 1 2 3\n2 2 3 4\n1 4 3 4', 'output': '10\n14\n4'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n\n    input = sys.stdin.readline\n    h, w, q, m = map(int, input().split())\n    diff = [[0] * (w + 2) for _ in range(h + 2)]\n\n    for _ in range(q):\n        r1, c1, r2, c2, x = map(int, input().split())\n        diff[r1][c1] += x\n        diff[r1][c2 + 1] -= x\n        diff[r2 + 1][c1] -= x\n        diff[r2 + 1][c2 + 1] += x\n\n    for r in range(1, h + 1):\n        for c in range(1, w + 1):\n            diff[r][c] += diff[r][c - 1]\n    for c in range(1, w + 1):\n        for r in range(1, h + 1):\n            diff[r][c] += diff[r - 1][c]\n\n    prefix = [[0] * (w + 1) for _ in range(h + 1)]\n    for r in range(1, h + 1):\n        row_sum = 0\n        for c in range(1, w + 1):\n            row_sum += diff[r][c]\n            prefix[r][c] = prefix[r - 1][c] + row_sum\n\n    out = []\n    for _ in range(m):\n        r1, c1, r2, c2 = map(int, input().split())\n        ans = prefix[r2][c2] - prefix[r1 - 1][c2] - prefix[r2][c1 - 1] + prefix[r1 - 1][c1 - 1]\n        out.append(str(ans))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
