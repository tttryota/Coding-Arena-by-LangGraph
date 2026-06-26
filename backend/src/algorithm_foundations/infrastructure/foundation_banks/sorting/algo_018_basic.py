from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-018-basic',
    title='基数ソート の基本',
    unit_kind='foundation',
    target_skill='基数ソート の基本',
    concept_overview='基数ソートは、下位の桁から順に安定に並べ替えていく解き方です。まずは 1 の位だけで 1 回並べ替えると配列がどう変わるかを見ます。',
    problem_bank=[
        problem(
            problem_id='algo-018-basic-p1',
            title='基数ソート の基本 / 1 の位で 1 回だけ安定に並べ替える',
            problem_statement='長さ N の非負整数列 A が与えられる。各要素を 1 の位で見て、0 から 9 の bucket に安定に分け直し、bucket 0, 1, ..., 9 の順につなげた列を出力せよ。10 の位以上はまだ使わない。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='1 の位で 1 回並べ替えた結果を空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai <= 10^9',
            examples=[{'input': '8\n170 45 75 90 802 24 2 66', 'output': '170 90 802 2 24 45 75 66'}],
            canonical_reference_solution="def solve() -> None:\n    input()\n    a = list(map(int, input().split()))\n    buckets = [[] for _ in range(10)]\n    for value in a:\n        buckets[value % 10].append(value)\n    out = [value for bucket in buckets for value in bucket]\n    print(*out)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
