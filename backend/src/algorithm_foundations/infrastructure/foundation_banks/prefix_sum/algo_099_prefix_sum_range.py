from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-099-prefix-sum-range',
    title='累積和で区間和を求める',
    unit_kind='foundation',
    target_skill='累積和で区間和を求める',
    concept_overview='累積和を使うと、区間の和を「右端までの和 - 左端の手前までの和」で求められます。区間を差で取り出す形を身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-099-prefix-sum-range-p1',
            title='累積和で区間和を求める / 区間和をそのまま答える',
            problem_statement='長さ N の整数列 A と Q 個の区間 [L, R] が与えられる。各区間の和を求めよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に L R (1-indexed)。',
            output_format='各問い合わせの区間和を 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n|Ai| <= 10^9',
            examples=[
                {
                    'input': '5 3\n1 2 3 4 5\n1 3\n2 5\n4 4',
                    'output': '6\n14\n4',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    prefix = [0]\n    for value in a:\n        prefix.append(prefix[-1] + value)\n    out = []\n    for _ in range(q):\n        l, r = map(int, input().split())\n        out.append(str(prefix[r] - prefix[l - 1]))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-099-prefix-sum-range-p2',
            title='累積和で区間和を求める / 2 本の列で同じ区間の合計を比べる',
            problem_statement='長さ N の整数列 A, B と Q 個の区間 [L, R] が与えられる。各区間について、`sum(A[L..R])` が `sum(B[L..R])` より大きければ `A`、小さければ `B`、等しければ `Same` を出力せよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n3 行目に B1..BN。\n続く Q 行に L R (1-indexed)。',
            output_format='各問い合わせごとに `A` / `B` / `Same` を 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n|Ai|, |Bi| <= 10^9',
            examples=[
                {
                    'input': '5 3\n1 3 2 4 5\n2 1 2 4 1\n1 3\n2 4\n4 5',
                    'output': 'A\nA\nA',
                },
            ],
            canonical_reference_solution="def build_prefix(arr: list[int]) -> list[int]:\n    prefix = [0]\n    for value in arr:\n        prefix.append(prefix[-1] + value)\n    return prefix\n\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    prefix_a = build_prefix(list(map(int, input().split())))\n    prefix_b = build_prefix(list(map(int, input().split())))\n    out = []\n    for _ in range(q):\n        l, r = map(int, input().split())\n        sum_a = prefix_a[r] - prefix_a[l - 1]\n        sum_b = prefix_b[r] - prefix_b[l - 1]\n        if sum_a > sum_b:\n            out.append('A')\n        elif sum_a < sum_b:\n            out.append('B')\n        else:\n            out.append('Same')\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-099-prefix-sum-range-p3',
            title='累積和で区間和を求める / 長さ K の区間和を左からすべて出す',
            problem_statement='長さ N の整数列 A と整数 K が与えられる。長さ K の連続区間 `A[L..L+K-1]` の和を、L=1 から L=N-K+1 まで順に空白区切りで出力せよ。',
            input_format='1 行目に N K。\n2 行目に A1..AN。',
            output_format='長さ K の各区間和を左から順に空白区切りで出力する。',
            constraints='1 <= K <= N <= 2 * 10^5\n|Ai| <= 10^9',
            examples=[
                {
                    'input': '5 3\n1 2 3 4 5',
                    'output': '6 9 12',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    n, k = map(int, input().split())\n    a = list(map(int, input().split()))\n    prefix = [0]\n    for value in a:\n        prefix.append(prefix[-1] + value)\n    ans = []\n    for left in range(0, n - k + 1):\n        right = left + k\n        ans.append(str(prefix[right] - prefix[left]))\n    print(*ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-099-prefix-sum-range-p4',
            title='累積和で区間和を求める / 1 本の列の 2 区間和を同じ問い合わせで比べる',
            problem_statement='長さ N の整数列 A と Q 個の問い合わせ `(L, M, R)` が与えられる。各問い合わせについて、`sum(A[L..M])` が `sum(A[M+1..R])` より大きければ `Left`、小さければ `Right`、等しければ `Same` を出力せよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に L M R (1-indexed, L <= M < R)。',
            output_format='各問い合わせごとに `Left` / `Right` / `Same` を 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n|Ai| <= 10^9',
            examples=[
                {
                    'input': '6 3\n2 1 3 4 2 5\n1 2 4\n2 3 6\n1 4 6',
                    'output': 'Right\nRight\nLeft',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    prefix = [0]\n    for value in a:\n        prefix.append(prefix[-1] + value)\n    out = []\n    for _ in range(q):\n        l, m, r = map(int, input().split())\n        left_sum = prefix[m] - prefix[l - 1]\n        right_sum = prefix[r] - prefix[m]\n        if left_sum > right_sum:\n            out.append('Left')\n        elif left_sum < right_sum:\n            out.append('Right')\n        else:\n            out.append('Same')\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
