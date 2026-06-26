from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-101-basic',
    title='順序つき集合の境界検索 の基本',
    unit_kind='foundation',
    target_skill='順序つき集合の境界検索 の基本',
    concept_overview='順序つき集合では、値を昇順で保ちながら「x 以上で最小の値」を探せます。この unit では値を順位に圧縮し、個数の累積から lower_bound を復元する形で境界検索の基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-101-basic-p1',
            title='順序つき集合の境界検索 の基本 / x 以上で最小の値を求める',
            problem_statement='Q 個の操作が与えられる。`1 x` は x を集合に追加し、`2 x` は x を集合から削除し、`3 x` は現在の集合に含まれる値のうち x 以上で最小の値を出力せよ。そのような値が存在しなければ -1 を出力せよ。集合なので、同じ値を複数回追加しても 1 個だけ持つものとする。',
            input_format='1 行目に Q。\n続く Q 行に操作。',
            output_format='type=3 のたびに答えを 1 行ずつ出力する。',
            constraints='1 <= Q <= 2 * 10^5\n0 <= x <= 10^9',
            examples=[{'input': '7\n1 5\n1 2\n3 3\n2 5\n3 3\n1 4\n3 4', 'output': '5\n-1\n4'}],
            canonical_reference_solution="from bisect import bisect_left\n\n\nclass FenwickTree:\n    def __init__(self, n: int) -> None:\n        self.n = n\n        self.data = [0] * (n + 1)\n\n    def add(self, idx: int, value: int) -> None:\n        idx += 1\n        while idx <= self.n:\n            self.data[idx] += value\n            idx += idx & -idx\n\n    def sum(self, idx: int) -> int:\n        total = 0\n        while idx > 0:\n            total += self.data[idx]\n            idx -= idx & -idx\n        return total\n\n    def range_sum(self, left: int, right: int) -> int:\n        return self.sum(right) - self.sum(left)\n\n    def kth(self, k: int) -> int:\n        idx = 0\n        bit = 1 << (self.n.bit_length() - 1)\n        while bit:\n            nxt = idx + bit\n            if nxt <= self.n and self.data[nxt] < k:\n                k -= self.data[nxt]\n                idx = nxt\n            bit >>= 1\n        return idx\n\n\ndef solve() -> None:\n    import sys\n\n    input = sys.stdin.readline\n    q = int(input())\n    ops = [tuple(map(int, input().split())) for _ in range(q)]\n    coords = sorted({op[1] for op in ops})\n    index = {x: i for i, x in enumerate(coords)}\n    bit = FenwickTree(len(coords))\n    present = [False] * len(coords)\n    out = []\n\n    for t, x in ops:\n        idx = index[x]\n        if t == 1:\n            if not present[idx]:\n                present[idx] = True\n                bit.add(idx, 1)\n        elif t == 2:\n            if present[idx]:\n                present[idx] = False\n                bit.add(idx, -1)\n        else:\n            left = bisect_left(coords, x)\n            count_before = bit.sum(left)\n            total = bit.sum(len(coords))\n            if count_before == total:\n                out.append('-1')\n            else:\n                pos = bit.kth(count_before + 1)\n                out.append(str(coords[pos]))\n\n    sys.stdout.write('\\n'.join(out))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
