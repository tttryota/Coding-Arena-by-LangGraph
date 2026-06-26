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
    concept_overview='遅延評価セグメント木は、区間更新の情報を今すぐ全部配らずに持っておき、必要になったときだけ反映する知識です。広い区間への更新と問い合わせを両立する基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-097-basic-p1',
            title='遅延評価セグメント木 の基本 / 1 ケースをそのまま解く',
            problem_statement='長さ N の整数列 A と Q 個の操作が与えられる。 `1 l r x` は区間 [l, r] の全要素に x を加算し、`2 l r` は区間 [l, r] の最小値を求めよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に操作。',
            output_format='type=2 のたびに区間最小値を 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n|Ai|, |x| <= 10^9',
            examples=[
                {
                    'input': '5 5\n5 2 8 1 4\n2 1 5\n1 2 4 3\n2 1 3\n1 5 5 -2\n2 4 5',
                    'output': '1\n5\n2',
                },
            ],
            canonical_reference_solution="class LazySegTree:\n    def __init__(self, arr: list[int]) -> None:\n        self.n = 1\n        while self.n < len(arr):\n            self.n <<= 1\n        self.data = [10 ** 18] * (2 * self.n)\n        self.lazy = [0] * (2 * self.n)\n        for i, value in enumerate(arr):\n            self.data[self.n + i] = value\n        for i in range(self.n - 1, 0, -1):\n            self.data[i] = min(self.data[i * 2], self.data[i * 2 + 1])\n\n    def _push(self, idx: int) -> None:\n        if self.lazy[idx] == 0:\n            return\n        for child in (idx * 2, idx * 2 + 1):\n            self.data[child] += self.lazy[idx]\n            self.lazy[child] += self.lazy[idx]\n        self.lazy[idx] = 0\n\n    def _range_add(self, left: int, right: int, value: int, idx: int, seg_l: int, seg_r: int) -> None:\n        if right < seg_l or seg_r < left:\n            return\n        if left <= seg_l and seg_r <= right:\n            self.data[idx] += value\n            self.lazy[idx] += value\n            return\n        self._push(idx)\n        mid = (seg_l + seg_r) // 2\n        self._range_add(left, right, value, idx * 2, seg_l, mid)\n        self._range_add(left, right, value, idx * 2 + 1, mid + 1, seg_r)\n        self.data[idx] = min(self.data[idx * 2], self.data[idx * 2 + 1])\n\n    def range_add(self, left: int, right: int, value: int) -> None:\n        self._range_add(left, right, value, 1, 0, self.n - 1)\n\n    def _range_min(self, left: int, right: int, idx: int, seg_l: int, seg_r: int) -> int:\n        if right < seg_l or seg_r < left:\n            return 10 ** 18\n        if left <= seg_l and seg_r <= right:\n            return self.data[idx]\n        self._push(idx)\n        mid = (seg_l + seg_r) // 2\n        return min(\n            self._range_min(left, right, idx * 2, seg_l, mid),\n            self._range_min(left, right, idx * 2 + 1, mid + 1, seg_r),\n        )\n\n    def range_min(self, left: int, right: int) -> int:\n        return self._range_min(left, right, 1, 0, self.n - 1)\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    seg = LazySegTree(a)\n    out = []\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        if parts[0] == 1:\n            _, l, r, x = parts\n            seg.range_add(l - 1, r - 1, x)\n        else:\n            _, l, r = parts\n            out.append(str(seg.range_min(l - 1, r - 1)))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-097-basic-p2',
            title='遅延評価セグメント木 の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A と Q 個の操作が与えられる。 `1 l r x` は区間 [l, r] の全要素に x を加算し、`2 l r` は区間 [l, r] の最小値を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に操作。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n|Ai|, |x| <= 10^9\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n5 5\n5 2 8 1 4\n2 1 5\n1 2 4 3\n2 1 3\n1 5 5 -2\n2 4 5\n5 5\n5 2 8 1 4\n2 1 5\n1 2 4 3\n2 1 3\n1 5 5 -2\n2 4 5',
                    'output': '1\n5\n2\n1\n5\n2',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nclass LazySegTree:\n    def __init__(self, arr: list[int]) -> None:\n        self.n = 1\n        while self.n < len(arr):\n            self.n <<= 1\n        self.data = [10 ** 18] * (2 * self.n)\n        self.lazy = [0] * (2 * self.n)\n        for i, value in enumerate(arr):\n            self.data[self.n + i] = value\n        for i in range(self.n - 1, 0, -1):\n            self.data[i] = min(self.data[i * 2], self.data[i * 2 + 1])\n\n    def _push(self, idx: int) -> None:\n        if self.lazy[idx] == 0:\n            return\n        for child in (idx * 2, idx * 2 + 1):\n            self.data[child] += self.lazy[idx]\n            self.lazy[child] += self.lazy[idx]\n        self.lazy[idx] = 0\n\n    def _range_add(self, left: int, right: int, value: int, idx: int, seg_l: int, seg_r: int) -> None:\n        if right < seg_l or seg_r < left:\n            return\n        if left <= seg_l and seg_r <= right:\n            self.data[idx] += value\n            self.lazy[idx] += value\n            return\n        self._push(idx)\n        mid = (seg_l + seg_r) // 2\n        self._range_add(left, right, value, idx * 2, seg_l, mid)\n        self._range_add(left, right, value, idx * 2 + 1, mid + 1, seg_r)\n        self.data[idx] = min(self.data[idx * 2], self.data[idx * 2 + 1])\n\n    def range_add(self, left: int, right: int, value: int) -> None:\n        self._range_add(left, right, value, 1, 0, self.n - 1)\n\n    def _range_min(self, left: int, right: int, idx: int, seg_l: int, seg_r: int) -> int:\n        if right < seg_l or seg_r < left:\n            return 10 ** 18\n        if left <= seg_l and seg_r <= right:\n            return self.data[idx]\n        self._push(idx)\n        mid = (seg_l + seg_r) // 2\n        return min(\n            self._range_min(left, right, idx * 2, seg_l, mid),\n            self._range_min(left, right, idx * 2 + 1, mid + 1, seg_r),\n        )\n\n    def range_min(self, left: int, right: int) -> int:\n        return self._range_min(left, right, 1, 0, self.n - 1)\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    seg = LazySegTree(a)\n    out = []\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        if parts[0] == 1:\n            _, l, r, x = parts\n            seg.range_add(l - 1, r - 1, x)\n        else:\n            _, l, r = parts\n            out.append(str(seg.range_min(l - 1, r - 1)))\n    sys.stdout.write('\\n'.join(out))\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-097-basic-p3',
            title='遅延評価セグメント木 の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A と Q 個の操作が与えられる。 `1 l r x` は区間 [l, r] の全要素に x を加算し、`2 l r` は区間 [l, r] の最小値を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に操作。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n|Ai|, |x| <= 10^9\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n5 5\n5 2 8 1 4\n2 1 5\n1 2 4 3\n2 1 3\n1 5 5 -2\n2 4 5\n5 5\n5 2 8 1 4\n2 1 5\n1 2 4 3\n2 1 3\n1 5 5 -2\n2 4 5\n5 5\n5 2 8 1 4\n2 1 5\n1 2 4 3\n2 1 3\n1 5 5 -2\n2 4 5',
                    'output': '1\n5\n2\n1\n5\n2\n1\n5\n2',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nclass LazySegTree:\n    def __init__(self, arr: list[int]) -> None:\n        self.n = 1\n        while self.n < len(arr):\n            self.n <<= 1\n        self.data = [10 ** 18] * (2 * self.n)\n        self.lazy = [0] * (2 * self.n)\n        for i, value in enumerate(arr):\n            self.data[self.n + i] = value\n        for i in range(self.n - 1, 0, -1):\n            self.data[i] = min(self.data[i * 2], self.data[i * 2 + 1])\n\n    def _push(self, idx: int) -> None:\n        if self.lazy[idx] == 0:\n            return\n        for child in (idx * 2, idx * 2 + 1):\n            self.data[child] += self.lazy[idx]\n            self.lazy[child] += self.lazy[idx]\n        self.lazy[idx] = 0\n\n    def _range_add(self, left: int, right: int, value: int, idx: int, seg_l: int, seg_r: int) -> None:\n        if right < seg_l or seg_r < left:\n            return\n        if left <= seg_l and seg_r <= right:\n            self.data[idx] += value\n            self.lazy[idx] += value\n            return\n        self._push(idx)\n        mid = (seg_l + seg_r) // 2\n        self._range_add(left, right, value, idx * 2, seg_l, mid)\n        self._range_add(left, right, value, idx * 2 + 1, mid + 1, seg_r)\n        self.data[idx] = min(self.data[idx * 2], self.data[idx * 2 + 1])\n\n    def range_add(self, left: int, right: int, value: int) -> None:\n        self._range_add(left, right, value, 1, 0, self.n - 1)\n\n    def _range_min(self, left: int, right: int, idx: int, seg_l: int, seg_r: int) -> int:\n        if right < seg_l or seg_r < left:\n            return 10 ** 18\n        if left <= seg_l and seg_r <= right:\n            return self.data[idx]\n        self._push(idx)\n        mid = (seg_l + seg_r) // 2\n        return min(\n            self._range_min(left, right, idx * 2, seg_l, mid),\n            self._range_min(left, right, idx * 2 + 1, mid + 1, seg_r),\n        )\n\n    def range_min(self, left: int, right: int) -> int:\n        return self._range_min(left, right, 1, 0, self.n - 1)\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    seg = LazySegTree(a)\n    out = []\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        if parts[0] == 1:\n            _, l, r, x = parts\n            seg.range_add(l - 1, r - 1, x)\n        else:\n            _, l, r = parts\n            out.append(str(seg.range_min(l - 1, r - 1)))\n    sys.stdout.write('\\n'.join(out))\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
