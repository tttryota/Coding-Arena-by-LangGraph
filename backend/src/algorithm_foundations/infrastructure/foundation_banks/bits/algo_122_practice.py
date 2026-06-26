from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-122-practice',
    title='ビット畳み込み（AND/OR畳み込み） を素直に実装する',
    unit_kind='foundation',
    target_skill='ビット畳み込み（AND/OR畳み込み） を素直に実装する',
    concept_overview='ビット畳み込みで各 `C[s]` を作れたら、その結果に対して「この集合 T の部分集合だけを見る」といった問い合わせも処理できます。ここでは OR 畳み込みの結果を使って、複数の集合条件問い合わせに答えます。',
    problem_bank=[
        problem(
            problem_id='algo-122-practice-p1',
            title='ビット畳み込み（AND/OR畳み込み） を素直に実装する / OR 畳み込み結果に対する集合条件問い合わせを処理する',
            problem_statement='長さ 2^N の配列 A, B と Q 個の集合マスク T_j が与えられる。OR 畳み込み C を `C[s] = Σ A[x]B[y] (x OR y = s)` で定義する。各 T_j について、`s` が `T_j` の部分集合であるような C[s] の総和を求めよ。',
            input_format='1 行目に N Q。\n2 行目に A。\n3 行目に B。\n続く Q 行に T_j。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='1 <= N <= 8\n1 <= Q <= 2 * 10^5\n0 <= Ai, Bi <= 10^9\n0 <= T_j < 2^N',
            examples=[{'input': '2 3\n1 2 3 4\n5 6 7 8\n1\n2\n3', 'output': '33\n48\n260'}],
            canonical_reference_solution="def solve() -> None:\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    b = list(map(int, input().split()))\n    size = 1 << n\n    c = [0] * size\n    for x in range(size):\n        for y in range(size):\n            c[x | y] += a[x] * b[y]\n    out = []\n    for _ in range(q):\n        t = int(input())\n        total = 0\n        sub = t\n        while True:\n            total += c[sub]\n            if sub == 0:\n                break\n            sub = (sub - 1) & t\n        out.append(str(total))\n    print('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
