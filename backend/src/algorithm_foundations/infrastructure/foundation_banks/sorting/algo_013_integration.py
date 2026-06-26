from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-013-integration',
    title='挿入ソート の総合演習',
    unit_kind='integration',
    target_skill='挿入ソート の総合演習',
    concept_overview='挿入ソートは、1 要素を差し込む操作を左から順に繰り返して整列済み prefix を広げます。ここでは 1 回の差し込みと最後までの中間として、K 回進めた途中状態を扱います。',
    problem_bank=[
        problem(
            problem_id='algo-013-integration-p1',
            title='挿入ソート の総合演習 / K 回の差し込みを行ったあとの列を求める',
            problem_statement='長さ N の整数列 A と整数 K が与えられる。挿入ソートの「位置 i の値を左側の整列済み部分へ差し込む」操作を、i=2 から順に K 回行ったあとの列を出力せよ。K が N-1 より大きいときは、配列が整列するまででよい。',
            input_format='1 行目に N K。\n2 行目に A1..AN。',
            output_format='K 回の差し込み後の列を空白区切りで出力する。',
            constraints='1 <= N <= 2000',
            examples=[{'input': '5 3\n4 1 5 2 3', 'output': '1 2 4 5 3'}],
            canonical_reference_solution="def solve() -> None:\n    n, k = map(int, input().split())\n    a = list(map(int, input().split()))\n    steps = min(k, n - 1)\n    for i in range(1, steps + 1):\n        value = a[i]\n        j = i - 1\n        while j >= 0 and a[j] > value:\n            a[j + 1] = a[j]\n            j -= 1\n        a[j + 1] = value\n    print(*a)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
