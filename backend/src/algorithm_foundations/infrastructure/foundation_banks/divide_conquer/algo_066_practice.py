from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-066-practice',
    title='セグメント木上の分割統治 を素直に実装する',
    unit_kind='foundation',
    target_skill='セグメント木上の分割統治 を素直に実装する',
    concept_overview='セグメント木は、区間を二分しながら情報を木に持たせ、更新と区間問い合わせを素早く行う知識です。部分区間の答えを合体して全体の答えを作る基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-066-practice-p1',
            title='セグメント木上の分割統治 を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='長さ N の整数列 A と Q 個の操作が与えられる。 `1 i x` は A_i を x に更新し、`2 l r` は区間 [l, r] の最小値を求めよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に操作。',
            output_format='type=2 のたびに区間最小値を 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5',
            examples=[
                {
                    'input': '5 4\n5 2 8 1 4\n2 1 5\n1 3 0\n2 2 4\n2 3 3',
                    'output': '1\n0\n0',
                },
            ],
            canonical_reference_solution="class SegTree:\n    def __init__(self, arr: list[int]) -> None:\n        self.n = 1\n        while self.n < len(arr):\n            self.n <<= 1\n        self.data = [10 ** 18] * (2 * self.n)\n        for i, value in enumerate(arr):\n            self.data[self.n + i] = value\n        for i in range(self.n - 1, 0, -1):\n            self.data[i] = min(self.data[i * 2], self.data[i * 2 + 1])\n    def update(self, idx: int, value: int) -> None:\n        idx += self.n\n        self.data[idx] = value\n        idx >>= 1\n        while idx:\n            self.data[idx] = min(self.data[idx * 2], self.data[idx * 2 + 1])\n            idx >>= 1\n\n    def query(self, left: int, right: int) -> int:\n        left += self.n\n        right += self.n\n        ans = 10 ** 18\n        while left <= right:\n            if left & 1:\n                ans = min(ans, self.data[left]); left += 1\n            if not (right & 1):\n                ans = min(ans, self.data[right]); right -= 1\n            left >>= 1\n            right >>= 1\n        return ans\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    seg = SegTree(a)\n    out = []\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        if parts[0] == 1:\n            _, i, x = parts\n            seg.update(i - 1, x)\n        else:\n            _, l, r = parts\n            out.append(str(seg.query(l - 1, r - 1)))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-066-practice-p2',
            title='セグメント木上の分割統治 を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A と Q 個の操作が与えられる。 `1 i x` は A_i を x に更新し、`2 l r` は区間 [l, r] の最小値を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に操作。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n5 4\n5 2 8 1 4\n2 1 5\n1 3 0\n2 2 4\n2 3 3\n5 4\n5 2 8 1 4\n2 1 5\n1 3 0\n2 2 4\n2 3 3',
                    'output': '1\n0\n0\n1\n0\n0',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nclass SegTree:\n    def __init__(self, arr: list[int]) -> None:\n        self.n = 1\n        while self.n < len(arr):\n            self.n <<= 1\n        self.data = [10 ** 18] * (2 * self.n)\n        for i, value in enumerate(arr):\n            self.data[self.n + i] = value\n        for i in range(self.n - 1, 0, -1):\n            self.data[i] = min(self.data[i * 2], self.data[i * 2 + 1])\n    def update(self, idx: int, value: int) -> None:\n        idx += self.n\n        self.data[idx] = value\n        idx >>= 1\n        while idx:\n            self.data[idx] = min(self.data[idx * 2], self.data[idx * 2 + 1])\n            idx >>= 1\n\n    def query(self, left: int, right: int) -> int:\n        left += self.n\n        right += self.n\n        ans = 10 ** 18\n        while left <= right:\n            if left & 1:\n                ans = min(ans, self.data[left]); left += 1\n            if not (right & 1):\n                ans = min(ans, self.data[right]); right -= 1\n            left >>= 1\n            right >>= 1\n        return ans\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    seg = SegTree(a)\n    out = []\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        if parts[0] == 1:\n            _, i, x = parts\n            seg.update(i - 1, x)\n        else:\n            _, l, r = parts\n            out.append(str(seg.query(l - 1, r - 1)))\n    sys.stdout.write('\\n'.join(out))\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-066-practice-p3',
            title='セグメント木上の分割統治 を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A と Q 個の操作が与えられる。 `1 i x` は A_i を x に更新し、`2 l r` は区間 [l, r] の最小値を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に操作。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n5 4\n5 2 8 1 4\n2 1 5\n1 3 0\n2 2 4\n2 3 3\n5 4\n5 2 8 1 4\n2 1 5\n1 3 0\n2 2 4\n2 3 3\n5 4\n5 2 8 1 4\n2 1 5\n1 3 0\n2 2 4\n2 3 3',
                    'output': '1\n0\n0\n1\n0\n0\n1\n0\n0',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nclass SegTree:\n    def __init__(self, arr: list[int]) -> None:\n        self.n = 1\n        while self.n < len(arr):\n            self.n <<= 1\n        self.data = [10 ** 18] * (2 * self.n)\n        for i, value in enumerate(arr):\n            self.data[self.n + i] = value\n        for i in range(self.n - 1, 0, -1):\n            self.data[i] = min(self.data[i * 2], self.data[i * 2 + 1])\n    def update(self, idx: int, value: int) -> None:\n        idx += self.n\n        self.data[idx] = value\n        idx >>= 1\n        while idx:\n            self.data[idx] = min(self.data[idx * 2], self.data[idx * 2 + 1])\n            idx >>= 1\n\n    def query(self, left: int, right: int) -> int:\n        left += self.n\n        right += self.n\n        ans = 10 ** 18\n        while left <= right:\n            if left & 1:\n                ans = min(ans, self.data[left]); left += 1\n            if not (right & 1):\n                ans = min(ans, self.data[right]); right -= 1\n            left >>= 1\n            right >>= 1\n        return ans\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    seg = SegTree(a)\n    out = []\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        if parts[0] == 1:\n            _, i, x = parts\n            seg.update(i - 1, x)\n        else:\n            _, l, r = parts\n            out.append(str(seg.query(l - 1, r - 1)))\n    sys.stdout.write('\\n'.join(out))\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
