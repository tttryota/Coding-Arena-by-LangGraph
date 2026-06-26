from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-097-basic',
    title='遅延評価セグメント木 の基本',
    unit_kind='foundation',
    target_skill='遅延評価セグメント木 の基本',
    concept_overview='遅延評価セグメント木は、区間更新の情報を今すぐ全部配らずに持っておき、必要になったときだけ反映する知識です。まずは区間加算をしたあとに 1 点の値を取り出す基本形を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-097-basic-p1',
            title='遅延評価セグメント木 の基本 / 区間加算後の 1 点の値を求める',
            problem_statement='長さ N の整数列 A と Q 個の操作が与えられる。`1 l r x` は区間 [l, r] の全要素に x を加算し、`2 i` は A_i の現在値を求めよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に操作。',
            output_format='type=2 のたびに現在の値を 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n-10^9 <= A_i, x <= 10^9\n1 <= l <= r <= N\n1 <= i <= N\n操作は 1 l r x または 2 i の形式',
            examples=[{'input': '5 5\n5 2 8 1 4\n2 3\n1 2 4 3\n2 3\n1 5 5 -2\n2 5', 'output': '8\n11\n2'}],
            canonical_reference_solution="class LazySegTree:\n    def __init__(self, arr: list[int]) -> None:\n        self.n = 1\n        while self.n < len(arr):\n            self.n <<= 1\n        self.data = [0] * (2 * self.n)\n        self.lazy = [0] * (2 * self.n)\n        for i, value in enumerate(arr):\n            self.data[self.n + i] = value\n\n    def _push(self, idx: int) -> None:\n        if self.lazy[idx] == 0:\n            return\n        for child in (idx * 2, idx * 2 + 1):\n            self.data[child] += self.lazy[idx]\n            self.lazy[child] += self.lazy[idx]\n        self.lazy[idx] = 0\n\n    def _range_add(self, left: int, right: int, value: int, idx: int, seg_l: int, seg_r: int) -> None:\n        if right < seg_l or seg_r < left:\n            return\n        if left <= seg_l and seg_r <= right:\n            self.data[idx] += value\n            self.lazy[idx] += value\n            return\n        self._push(idx)\n        mid = (seg_l + seg_r) // 2\n        self._range_add(left, right, value, idx * 2, seg_l, mid)\n        self._range_add(left, right, value, idx * 2 + 1, mid + 1, seg_r)\n\n    def range_add(self, left: int, right: int, value: int) -> None:\n        self._range_add(left, right, value, 1, 0, self.n - 1)\n\n    def point_get(self, pos: int) -> int:\n        idx = 1\n        seg_l = 0\n        seg_r = self.n - 1\n        while seg_l != seg_r:\n            self._push(idx)\n            mid = (seg_l + seg_r) // 2\n            if pos <= mid:\n                idx = idx * 2\n                seg_r = mid\n            else:\n                idx = idx * 2 + 1\n                seg_l = mid + 1\n        return self.data[idx]\n\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    seg = LazySegTree(a)\n    out = []\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        if parts[0] == 1:\n            _, l, r, x = parts\n            seg.range_add(l - 1, r - 1, x)\n        else:\n            _, i = parts\n            out.append(str(seg.point_get(i - 1)))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
