from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-002-basic',
    title='二分探索 の基本',
    unit_kind='foundation',
    target_skill='二分探索 の基本',
    concept_overview='二分探索は、条件を満たす境目や値を、探索範囲を半分ずつ絞りながら見つける解き方です。単調性を見つけて mid で判定する流れを身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-002-basic-p1',
            title='二分探索 の基本 / A の中で x 以上となる最初の位置を 1-indexed で求め',
            problem_statement='昇順に並んだ長さ N の整数列 A と Q 個の値 x が与えられる。 各 x について、A の中で x 以上となる最初の位置を 1-indexed で求め、 存在しない場合は -1 を出力せよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に x。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\nA は昇順',
            examples=[{'input': '5 3\n1 3 5 8 13\n4\n13\n20', 'output': '3\n5\n-1'}],
            canonical_reference_solution="from bisect import bisect_left\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    out = []\n    for _ in range(q):\n        x = int(input())\n        idx = bisect_left(a, x)\n        out.append(str(idx + 1) if idx < n else '-1')\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
