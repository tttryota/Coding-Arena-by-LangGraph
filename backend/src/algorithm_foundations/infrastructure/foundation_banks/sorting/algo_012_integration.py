from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-012-integration',
    title='選択ソート の総合演習',
    unit_kind='integration',
    target_skill='選択ソート の総合演習',
    concept_overview='選択ソートは、1 回の「最小値を探して前へ置く」操作を繰り返して左側を確定していきます。ここでは 1 回と最後までの中間として、K 回進めた途中状態を扱います。',
    problem_bank=[
        problem(
            problem_id='algo-012-integration-p1',
            title='選択ソート の総合演習 / K 回の選択操作を行ったあとの列を求める',
            problem_statement='長さ N の整数列 A と整数 K が与えられる。選択ソートの「位置 i に対して i 以降の最小値を探し、その位置と交換する」操作を先頭から K 回行ったあとの列を出力せよ。K が N より大きいときは、配列が確定するまででよい。',
            input_format='1 行目に N K。\n2 行目に A1..AN。',
            output_format='K 回の操作後の列を空白区切りで出力する。',
            constraints='1 <= N <= 2000',
            examples=[{'input': '5 2\n4 1 5 2 3', 'output': '1 2 5 4 3'}],
            canonical_reference_solution="def solve() -> None:\n    n, k = map(int, input().split())\n    a = list(map(int, input().split()))\n    steps = min(k, n)\n    for i in range(steps):\n        best = i\n        for j in range(i + 1, n):\n            if a[j] < a[best]:\n                best = j\n        a[i], a[best] = a[best], a[i]\n    print(*a)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
