from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-122-basic',
    title='ビット畳み込み（AND/OR畳み込み） の基本',
    unit_kind='foundation',
    target_skill='ビット畳み込み（AND/OR畳み込み） の基本',
    concept_overview='ビット畳み込み（AND/OR畳み込み）は、添字をビット集合とみなして、OR や AND の結果ごとに寄与を集める知識です。まずは OR 畳み込みの定義どおりに全組を数え上げて、結果の添字にどの組が寄与するかを理解します。',
    problem_bank=[
        problem(
            problem_id='algo-122-basic-p1',
            title='ビット畳み込み（AND/OR畳み込み） の基本 / すべての C[s] を求める',
            problem_statement='長さ 2^N の配列 A, B が与えられる。 OR 畳み込み C を `C[s] = Σ A[x]B[y] (x OR y = s)` で定義する。 すべての C[s] を求めよ。',
            input_format='1 行目に N。\n2 行目に A。\n3 行目に B。',
            output_format='C を空白区切りで出力する。',
            constraints='1 <= N <= 5\n0 <= Ai, Bi <= 10^9',
            examples=[{'input': '2\n1 2 3 4\n5 6 7 8', 'output': '5 28 43 184'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    size = 1 << n\n    a = list(map(int, input().split()))\n    b = list(map(int, input().split()))\n    c = [0] * size\n    for x in range(size):\n        for y in range(size):\n            c[x | y] += a[x] * b[y]\n    print(*c)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
