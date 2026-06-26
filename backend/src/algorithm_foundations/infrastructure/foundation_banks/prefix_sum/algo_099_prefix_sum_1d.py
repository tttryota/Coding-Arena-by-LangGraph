from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-099-prefix-sum-1d',
    title='一次元累積和の基本',
    unit_kind='foundation',
    target_skill='一次元累積和の基本',
    concept_overview='累積和は、左から順に和をためておき、途中までの合計をすぐ取り出せるようにする考え方です。まずは prefix sum 配列を作るところから押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-099-prefix-sum-1d-p1',
            title='一次元累積和の基本 / 累積和配列をそのまま作る',
            problem_statement='長さ N の整数列 A が与えられる。累積和 P を `P0=0, Pi=A1+...+Ai` と定義し、P0 から PN までを出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='P0..PN を空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5\n|Ai| <= 10^9',
            examples=[
                {
                    'input': '4\n3 1 4 1',
                    'output': '0 3 4 8 9',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    input()\n    a = list(map(int, input().split()))\n    prefix = [0]\n    for value in a:\n        prefix.append(prefix[-1] + value)\n    print(*prefix)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-099-prefix-sum-1d-p2',
            title='一次元累積和の基本 / 合計が X 以上になる最初の位置を探す',
            problem_statement='長さ N の整数列 A と整数 X が与えられる。`A1+...+Ai >= X` となる最小の 1-indexed の i を求め、存在しなければ -1 を出力せよ。',
            input_format='1 行目に N X。\n2 行目に A1..AN。',
            output_format='条件を満たす最小の i、存在しなければ -1 を出力する。',
            constraints='1 <= N <= 2 * 10^5\n|Ai| <= 10^9\n|X| <= 10^18',
            examples=[
                {
                    'input': '5 8\n2 1 3 4 2',
                    'output': '4',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    n, x = map(int, input().split())\n    a = list(map(int, input().split()))\n    total = 0\n    for idx, value in enumerate(a, start=1):\n        total += value\n        if total >= x:\n            print(idx)\n            return\n    print(-1)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-099-prefix-sum-1d-p3',
            title='一次元累積和の基本 / 非負な累積和がいくつあるか数える',
            problem_statement='長さ N の整数列 A が与えられる。累積和 `P0=0, Pi=A1+...+Ai` のうち、0 以上であるものの個数を求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='条件を満たす累積和の個数を出力する。',
            constraints='1 <= N <= 2 * 10^5\n|Ai| <= 10^9',
            examples=[
                {
                    'input': '5\n3 -5 4 -1 2',
                    'output': '4',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    input()\n    a = list(map(int, input().split()))\n    total = 0\n    ans = 1\n    for value in a:\n        total += value\n        if total >= 0:\n            ans += 1\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-099-prefix-sum-1d-p4',
            title='一次元累積和の基本 / 累積和配列から元の配列を復元する',
            problem_statement='長さ N+1 の数列 `P0, P1, ..., PN` が与えられる。`P0=0` であり、ある整数列 A の累積和になっている。元の A1..AN を復元して出力せよ。',
            input_format='1 行目に N。\n2 行目に P0..PN。',
            output_format='A1..AN を空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5\n|Pi| <= 10^18',
            examples=[
                {
                    'input': '4\n0 3 4 8 9',
                    'output': '3 1 4 1',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    input()\n    prefix = list(map(int, input().split()))\n    ans = []\n    for i in range(1, len(prefix)):\n        ans.append(prefix[i] - prefix[i - 1])\n    print(*ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-099-prefix-sum-1d-p5',
            title='一次元累積和の基本 / 複数の位置までの和を答える',
            problem_statement='長さ N の整数列 A と Q 個の位置 r が与えられる。各問い合わせについて `A1+...+Ar` を出力せよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に r。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n|Ai| <= 10^9\n1 <= r <= N',
            examples=[
                {
                    'input': '5 3\n2 1 3 4 2\n1\n4\n5',
                    'output': '2\n10\n12',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    prefix = [0]\n    for value in a:\n        prefix.append(prefix[-1] + value)\n    out = []\n    for _ in range(q):\n        r = int(input())\n        out.append(str(prefix[r]))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-099-prefix-sum-1d-p6',
            title='一次元累積和の基本 / 最大の累積和を求める',
            problem_statement='長さ N の整数列 A が与えられる。累積和 `P0=0, Pi=A1+...+Ai` の最大値を求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='累積和の最大値を出力する。',
            constraints='1 <= N <= 2 * 10^5\n|Ai| <= 10^9',
            examples=[
                {
                    'input': '5\n3 -2 5 -10 4',
                    'output': '6',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    input()\n    a = list(map(int, input().split()))\n    total = 0\n    best = 0\n    for value in a:\n        total += value\n        best = max(best, total)\n    print(best)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
