from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-017-basic',
    title='計数ソート（カウンティングソート） の基本',
    unit_kind='foundation',
    target_skill='計数ソート（カウンティングソート） の基本',
    concept_overview='計数ソートは、まず各値の出現回数を数えるところから始まります。ここでは整列結果を作る前段として、頻度配列そのものを作る感覚を固めます。',
    problem_bank=[
        problem(
            problem_id='algo-017-basic-p1',
            title='計数ソート（カウンティングソート） の基本 / 0 から K までの出現回数を数える',
            problem_statement='0 以上 K 以下の整数からなる長さ N の列 A が与えられる。各 x = 0, 1, ..., K について、A の中に x が何回現れるかを数えて出力せよ。',
            input_format='1 行目に N K。\n2 行目に A1..AN。',
            output_format='cnt[0], cnt[1], ..., cnt[K] を空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= K <= 10^6\n0 <= Ai <= K',
            examples=[{'input': '7 5\n4 1 4 0 2 1 5', 'output': '1 2 1 0 2 1'}],
            canonical_reference_solution="def solve() -> None:\n    n, k = map(int, input().split())\n    a = list(map(int, input().split()))\n    cnt = [0] * (k + 1)\n    for value in a:\n        cnt[value] += 1\n    print(*cnt)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
