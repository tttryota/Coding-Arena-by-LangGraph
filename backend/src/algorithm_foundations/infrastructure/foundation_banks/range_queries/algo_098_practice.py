from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-098-practice',
    title='Binary Indexed Tree（BIT/Fenwick木） を素直に実装する',
    unit_kind='foundation',
    target_skill='Binary Indexed Tree（BIT/Fenwick木） を素直に実装する',
    concept_overview='BIT を頻度表として使うと、値 x 以下がいくつあるかを更新しながら素早く数えられます。添字を値だと思って prefix sum を取る使い方を確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-098-practice-p1',
            title='Binary Indexed Tree（BIT/Fenwick木） を素直に実装する / 値 x 以下の個数を追加削除つきで答える',
            problem_statement='1 以上 N 以下の番号がついた箱と Q 個の操作が与えられる。`1 x` は箱 x にボールを 1 個追加し、`2 x` は箱 x からボールを 1 個削除し、`3 x` は 1 番から x 番までの箱に入っているボール総数を答えよ。',
            input_format='1 行目に N Q。\n続く Q 行に操作。',
            output_format='type=3 のたびに答えを 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\ntype=2 の時点で箱 x には 1 個以上のボールが入っている',
            examples=[{'input': '5 7\n1 2\n1 4\n3 3\n1 2\n3 4\n2 2\n3 2', 'output': '1\n3\n1'}],
            canonical_reference_solution="class Fenwick:\n    def __init__(self, n: int) -> None:\n        self.n = n\n        self.data = [0] * (n + 1)\n\n    def add(self, idx: int, value: int) -> None:\n        while idx <= self.n:\n            self.data[idx] += value\n            idx += idx & -idx\n\n    def sum(self, idx: int) -> int:\n        total = 0\n        while idx > 0:\n            total += self.data[idx]\n            idx -= idx & -idx\n        return total\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    bit = Fenwick(n)\n    out = []\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        t, x = parts\n        if t == 1:\n            bit.add(x, 1)\n        elif t == 2:\n            bit.add(x, -1)\n        else:\n            out.append(str(bit.sum(x)))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
