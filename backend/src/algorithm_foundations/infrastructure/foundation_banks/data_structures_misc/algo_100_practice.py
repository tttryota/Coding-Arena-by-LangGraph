from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-100-practice',
    title='いもす法 を素直に実装する',
    unit_kind='foundation',
    target_skill='いもす法 を素直に実装する',
    concept_overview='いもす法で更新後の配列を復元できたら、その配列に対する区間和も扱えるようにしたいです。ここでは「更新を差分でまとめる累積」と「復元後の配列に対する累積和」を 2 段で使います。',
    problem_bank=[
        problem(
            problem_id='algo-100-practice-p1',
            title='いもす法 を素直に実装する / 更新後配列に対する区間和問い合わせを処理する',
            problem_statement='長さ N の配列に対して Q 個の加算操作 `[l, r] に x を足す` が与えられる。すべての更新を適用したあと、M 個の問い合わせ `[l, r]` それぞれについて、その区間の総和を求めよ。',
            input_format='1 行目に N Q M。\n続く Q 行に l r x。\n続く M 行に l r。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='1 <= N, Q, M <= 2 * 10^5\n-10^9 <= x <= 10^9\n1 <= l <= r <= N',
            examples=[{'input': '5 3 3\n1 3 2\n2 5 1\n4 4 -2\n1 3\n2 5\n4 4', 'output': '8\n6\n-1'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n\n    input = sys.stdin.readline\n    n, q, m = map(int, input().split())\n    diff = [0] * (n + 1)\n    for _ in range(q):\n        l, r, x = map(int, input().split())\n        diff[l - 1] += x\n        if r < n:\n            diff[r] -= x\n\n    values = [0] * n\n    cur = 0\n    for i in range(n):\n        cur += diff[i]\n        values[i] = cur\n\n    prefix = [0] * (n + 1)\n    for i, value in enumerate(values, start=1):\n        prefix[i] = prefix[i - 1] + value\n\n    out = []\n    for _ in range(m):\n        l, r = map(int, input().split())\n        out.append(str(prefix[r] - prefix[l - 1]))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
