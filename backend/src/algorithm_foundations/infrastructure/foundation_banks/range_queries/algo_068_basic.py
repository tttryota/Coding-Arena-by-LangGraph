from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-068-basic',
    title='マージソートで転倒数 の基本',
    unit_kind='foundation',
    target_skill='マージソートで転倒数 の基本',
    concept_overview='マージソートで転倒数を数えるときは、左右の昇順列をマージする途中で「右から先に取られた回数」を数えます。まずは 2 本の昇順列のあいだにある転倒数だけを数える基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-068-basic-p1',
            title='マージソートで転倒数 の基本 / 2 本の昇順列のあいだにある転倒数を数える',
            problem_statement='昇順に並んだ長さ N の整数列 A と、昇順に並んだ長さ M の整数列 B が与えられる。A_i > B_j となる組 (i, j) の個数を求めよ。',
            input_format='1 行目に N M。\n2 行目に A1..AN。\n3 行目に B1..BM。',
            output_format='求める個数を出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n-10^18 <= A_i, B_j <= 10^18\nA, B はそれぞれ昇順',
            examples=[{'input': '3 3\n1 4 7\n2 5 6', 'output': '4'}],
            canonical_reference_solution="def solve() -> None:\n    n, m = map(int, input().split())\n    a = list(map(int, input().split()))\n    b = list(map(int, input().split()))\n    i = j = 0\n    ans = 0\n    while i < n and j < m:\n        if a[i] <= b[j]:\n            i += 1\n        else:\n            ans += n - i\n            j += 1\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
