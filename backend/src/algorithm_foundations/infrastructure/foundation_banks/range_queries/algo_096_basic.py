from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-096-basic',
    title='セグメント木 の基本',
    unit_kind='foundation',
    target_skill='セグメント木 の基本',
    concept_overview='セグメント木は、配列を区間ごとにまとめて持ち、部分区間の情報を合体して答えを作る知識です。まずは点更新と区間和を扱う最も素直な形で、木の合成の流れを押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-096-basic-p1',
            title='セグメント木 の基本 / 1 i x は A_i を x に更新し、2 l r は区間 [l, r] の総和を求める',
            problem_statement='長さ N の整数列 A と Q 個の操作が与えられる。`1 i x` は A_i を x に更新し、`2 l r` は区間 [l, r] の総和を求めよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に操作。',
            output_format='type=2 のたびに、区間和を 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n-10^9 <= A_i, x <= 10^9\n1 <= i <= N\n1 <= l <= r <= N',
            examples=[{'input': '5 4\n5 2 8 1 4\n2 2 4\n1 3 0\n2 1 3\n2 3 5', 'output': '11\n7\n5'}],
            canonical_reference_solution="class SegTree:\n    def __init__(self, arr: list[int]) -> None:\n        self.n = 1\n        while self.n < len(arr):\n            self.n <<= 1\n        self.data = [0] * (2 * self.n)\n        for i, value in enumerate(arr):\n            self.data[self.n + i] = value\n        for i in range(self.n - 1, 0, -1):\n            self.data[i] = self.data[i * 2] + self.data[i * 2 + 1]\n\n    def update(self, idx: int, value: int) -> None:\n        idx += self.n\n        self.data[idx] = value\n        idx >>= 1\n        while idx:\n            self.data[idx] = self.data[idx * 2] + self.data[idx * 2 + 1]\n            idx >>= 1\n\n    def query(self, left: int, right: int) -> int:\n        left += self.n\n        right += self.n\n        ans = 0\n        while left <= right:\n            if left & 1:\n                ans += self.data[left]\n                left += 1\n            if not (right & 1):\n                ans += self.data[right]\n                right -= 1\n            left >>= 1\n            right >>= 1\n        return ans\n\n\ndef solve() -> None:\n    import sys\n\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    seg = SegTree(a)\n    out = []\n\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        if parts[0] == 1:\n            _, i, x = parts\n            seg.update(i - 1, x)\n        else:\n            _, l, r = parts\n            out.append(str(seg.query(l - 1, r - 1)))\n\n    sys.stdout.write('\\n'.join(out))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
