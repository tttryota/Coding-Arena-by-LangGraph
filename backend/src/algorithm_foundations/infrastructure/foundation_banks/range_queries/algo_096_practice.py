from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-096-practice',
    title='セグメント木 を素直に実装する',
    unit_kind='foundation',
    target_skill='セグメント木 を素直に実装する',
    concept_overview='セグメント木に区間和を持たせると、和を求めるだけでなく「prefix 和が初めてしきい値以上になる位置」を木を下りながら探せます。集約値を境界探索に使う別視点を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-096-practice-p1',
            title='セグメント木 を素直に実装する / prefix 和が初めて x 以上になる位置を求める',
            problem_statement='長さ N の非負整数列 A と Q 個の操作が与えられる。`1 i x` は A_i を x に更新し、`2 x` は prefix 和 `A_1 + ... + A_i` が初めて x 以上になる最小の i を求めよ。そのような i が存在しなければ -1 を出力せよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に操作。',
            output_format='type=2 のたびに答えを 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n0 <= A_i, x <= 10^9\n1 <= i <= N\n操作は 1 i x または 2 x の形式',
            examples=[{'input': '5 5\n2 1 3 4 2\n2 5\n1 2 5\n2 7\n1 5 10\n2 15', 'output': '3\n2\n5'}],
            canonical_reference_solution="class SegTree:\n    def __init__(self, arr: list[int]) -> None:\n        self.size = len(arr)\n        self.n = 1\n        while self.n < self.size:\n            self.n <<= 1\n        self.data = [0] * (2 * self.n)\n        for i, value in enumerate(arr):\n            self.data[self.n + i] = value\n        for i in range(self.n - 1, 0, -1):\n            self.data[i] = self.data[i * 2] + self.data[i * 2 + 1]\n\n    def update(self, idx: int, value: int) -> None:\n        idx += self.n\n        self.data[idx] = value\n        idx >>= 1\n        while idx:\n            self.data[idx] = self.data[idx * 2] + self.data[idx * 2 + 1]\n            idx >>= 1\n\n    def lower_bound_prefix(self, target: int) -> int:\n        if target <= 0:\n            return 0\n        if self.data[1] < target:\n            return -1\n        idx = 1\n        while idx < self.n:\n            if self.data[idx * 2] >= target:\n                idx = idx * 2\n            else:\n                target -= self.data[idx * 2]\n                idx = idx * 2 + 1\n        pos = idx - self.n\n        return pos if pos < self.size else -1\n\n\ndef solve() -> None:\n    import sys\n\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    seg = SegTree(a)\n    out = []\n\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        if parts[0] == 1:\n            _, i, x = parts\n            seg.update(i - 1, x)\n        else:\n            _, x = parts\n            pos = seg.lower_bound_prefix(x)\n            out.append(str(pos + 1 if pos != -1 else -1))\n\n    sys.stdout.write('\\n'.join(out))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
