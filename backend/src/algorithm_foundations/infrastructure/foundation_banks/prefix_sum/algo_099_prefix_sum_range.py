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
            title='累積和で区間和を求める / 区間の和が非負かを判定する',
            problem_statement='長さ N の整数列 A と Q 個の区間 [L, R] が与えられる。各区間について、区間和が 0 以上なら Yes、そうでなければ No を出力せよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に L R (1-indexed)。',
            output_format='各問い合わせごとに Yes / No を 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n|Ai| <= 10^9',
            examples=[
                {
                    'input': '5 3\n2 -5 4 1 -1\n1 2\n2 4\n3 5',
                    'output': 'No\nYes\nYes',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    prefix = [0]\n    for value in a:\n        prefix.append(prefix[-1] + value)\n    out = []\n    for _ in range(q):\n        l, r = map(int, input().split())\n        total = prefix[r] - prefix[l - 1]\n        out.append('Yes' if total >= 0 else 'No')\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-099-prefix-sum-range-p3',
            title='累積和で区間和を求める / 最も和が大きい問い合わせを選ぶ',
            problem_statement='長さ N の整数列 A と Q 個の区間 [L, R] が与えられる。区間和が最大になる問い合わせ番号を 1-indexed で出力せよ。最大が複数あるときは最小の番号を選べ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に L R (1-indexed)。',
            output_format='条件を満たす問い合わせ番号を出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n|Ai| <= 10^9',
            examples=[
                {
                    'input': '5 4\n1 2 3 4 5\n1 1\n1 3\n2 5\n4 5',
                    'output': '3',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    prefix = [0]\n    for value in a:\n        prefix.append(prefix[-1] + value)\n    best_sum = None\n    best_idx = 1\n    for idx in range(1, q + 1):\n        l, r = map(int, input().split())\n        total = prefix[r] - prefix[l - 1]\n        if best_sum is None or total > best_sum:\n            best_sum = total\n            best_idx = idx\n    print(best_idx)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-099-prefix-sum-range-p4',
            title='累積和で区間和を求める / 0-indexed の区間を差で取り出す',
            problem_statement='長さ N の整数列 A と Q 個の区間 [L, R] が与えられる。L, R は 0-indexed であり、両端を含む。各区間の和を求めよ。',
            input_format='1 行目に N Q。\n2 行目に A0..A(N-1)。\n続く Q 行に L R (0-indexed)。',
            output_format='各問い合わせの区間和を 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n|Ai| <= 10^9\n0 <= L <= R < N',
            examples=[
                {
                    'input': '5 3\n1 2 3 4 5\n0 2\n1 4\n3 3',
                    'output': '6\n14\n4',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    prefix = [0]\n    for value in a:\n        prefix.append(prefix[-1] + value)\n    out = []\n    for _ in range(q):\n        l, r = map(int, input().split())\n        out.append(str(prefix[r + 1] - prefix[l]))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-099-prefix-sum-range-p5',
            title='累積和で区間和を求める / しきい値以上の区間数を数える',
            problem_statement='長さ N の整数列 A と Q 個の問い合わせ `(L, R, X)` が与えられる。区間 [L, R] の和が X 以上である問い合わせの個数を求めよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に L R X (1-indexed)。',
            output_format='条件を満たす問い合わせ数を出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n|Ai| <= 10^9\n|X| <= 10^18',
            examples=[
                {
                    'input': '5 4\n1 2 3 4 5\n1 3 6\n2 5 15\n4 5 10\n1 5 20',
                    'output': '2',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    prefix = [0]\n    for value in a:\n        prefix.append(prefix[-1] + value)\n    ans = 0\n    for _ in range(q):\n        l, r, x = map(int, input().split())\n        total = prefix[r] - prefix[l - 1]\n        if total >= x:\n            ans += 1\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-099-prefix-sum-range-p6',
            title='累積和で区間和を求める / 2 つの区間和の差を答える',
            problem_statement='長さ N の整数列 A と Q 個の問い合わせ `(L1, R1, L2, R2)` が与えられる。`sum(L1..R1) - sum(L2..R2)` を各問い合わせについて求めよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に L1 R1 L2 R2 (1-indexed)。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n|Ai| <= 10^9',
            examples=[
                {
                    'input': '5 3\n1 2 3 4 5\n1 3 4 5\n2 4 1 1\n3 5 2 3',
                    'output': '-3\n8\n7',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    prefix = [0]\n    for value in a:\n        prefix.append(prefix[-1] + value)\n    out = []\n    for _ in range(q):\n        l1, r1, l2, r2 = map(int, input().split())\n        total1 = prefix[r1] - prefix[l1 - 1]\n        total2 = prefix[r2] - prefix[l2 - 1]\n        out.append(str(total1 - total2))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
