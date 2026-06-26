from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-014-basic',
    title='マージソート の基本',
    unit_kind='foundation',
    target_skill='マージソート の基本',
    concept_overview='マージソートは、列を半分ずつに分けて整列し、2 つの昇順列をマージして全体を作る知識です。まずは分割と併合で整列する基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-014-basic-p1',
            title='マージソート の基本 / 2 本の昇順列をマージする',
            problem_statement='昇順に並んだ 2 本の整数列 A, B が与えられる。2 本をマージして 1 本の昇順列を出力せよ。',
            input_format='1 行目に N M。\n2 行目に A1..AN。\n3 行目に B1..BM。',
            output_format='マージ後の昇順列を空白区切りで出力する。',
            constraints='1 <= N, M <= 2 * 10^5',
            examples=[{'input': '3 4\n1 4 7\n2 3 5 8', 'output': '1 2 3 4 5 7 8'}],
            canonical_reference_solution="def solve() -> None:\n    n, m = map(int, input().split())\n    a = list(map(int, input().split()))\n    b = list(map(int, input().split()))\n    i = j = 0\n    out = []\n    while i < n and j < m:\n        if a[i] <= b[j]:\n            out.append(a[i])\n            i += 1\n        else:\n            out.append(b[j])\n            j += 1\n    out.extend(a[i:])\n    out.extend(b[j:])\n    print(*out)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
