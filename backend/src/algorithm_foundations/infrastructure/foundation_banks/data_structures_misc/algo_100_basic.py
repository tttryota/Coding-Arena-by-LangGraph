from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-100-basic',
    title='いもす法 の基本',
    unit_kind='foundation',
    target_skill='いもす法 の基本',
    concept_overview='いもす法は、区間への加算を差分として記録し、最後に累積して各位置の値を復元する考え方です。まずは更新をまとめて記録し、最終配列を復元する基本形を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-100-basic-p1',
            title='いもす法 の基本 / すべて適用した後の配列を求める',
            problem_statement='長さ N の配列に対して Q 個の加算操作 `[l, r] に x を足す` が与えられる。 すべて適用した後の配列を出力せよ。',
            input_format='1 行目に N Q。\n続く Q 行に l r x。',
            output_format='最終的な配列を空白区切りで出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n-10^9 <= x <= 10^9\n1 <= l <= r <= N',
            examples=[{'input': '5 3\n1 3 2\n2 5 1\n4 4 -2', 'output': '2 3 3 -1 1'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    diff = [0] * (n + 1)\n    for _ in range(q):\n        l, r, x = map(int, input().split())\n        diff[l - 1] += x\n        if r < n:\n            diff[r] -= x\n    ans = []\n    cur = 0\n    for i in range(n):\n        cur += diff[i]\n        ans.append(cur)\n    print(*ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
