from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-098-basic',
    title='Binary Indexed Tree（BIT/Fenwick木） の基本',
    unit_kind='foundation',
    target_skill='Binary Indexed Tree（BIT/Fenwick木） の基本',
    concept_overview='Binary Indexed Tree（BIT/Fenwick木）は、配列の値を少しずつまとめて持ち、更新しながら区間和を素早く求める知識です。1 点更新と累積和の対応を使う基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-098-basic-p1',
            title='Binary Indexed Tree（BIT/Fenwick木） の基本 / 1 i x は A_i に x を加算し、2 l r は区間 [l, r] の総和を求める',
            problem_statement='長さ N の整数列 A と Q 個の操作が与えられる。 `1 i x` は A_i に x を加算し、`2 l r` は区間 [l, r] の総和を求めよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に操作。',
            output_format='type=2 のたびに区間和を 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n|Ai|, |x| <= 10^9',
            examples=[{'input': '5 4\n1 2 3 4 5\n2 2 4\n1 3 10\n2 1 3\n2 3 5', 'output': '9\n16\n22'}],
            canonical_reference_solution="class Fenwick:\n    def __init__(self, n: int) -> None:\n        self.n = n\n        self.data = [0] * (n + 1)\n\n    def add(self, idx: int, value: int) -> None:\n        while idx <= self.n:\n            self.data[idx] += value\n            idx += idx & -idx\n\n    def sum(self, idx: int) -> int:\n        total = 0\n        while idx > 0:\n            total += self.data[idx]\n            idx -= idx & -idx\n        return total\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    bit = Fenwick(n)\n    for i, value in enumerate(a, start=1):\n        bit.add(i, value)\n    out = []\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        if parts[0] == 1:\n            _, i, x = parts\n            bit.add(i, x)\n        else:\n            _, l, r = parts\n            out.append(str(bit.sum(r) - bit.sum(l - 1)))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
