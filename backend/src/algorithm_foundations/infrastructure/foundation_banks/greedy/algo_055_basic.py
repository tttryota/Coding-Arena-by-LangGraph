from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-055-basic',
    title='交換による証明（exchange argument） の基本',
    unit_kind='foundation',
    target_skill='交換による証明（exchange argument） の基本',
    concept_overview='交換による証明（exchange argument）は、ある並べ方が最適でないなら、隣り合う 2 要素を入れ替えても悪化しないことを示して最適形へ近づける知識です。順序を短い局所交換で正当化する基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-055-basic-p1',
            title='交換による証明（exchange argument） の基本 / 1 台の機械で 1 つずつ順番に処理するとき、完了時刻の総和を最小にせよ',
            problem_statement='N 個の仕事があり、i 番目の処理時間は Ti である。1 台の機械で 1 つずつ順番に処理するとき、完了時刻の総和を最小にせよ。',
            input_format='1 行目に N。\n2 行目に T1..TN。',
            output_format='完了時刻の総和の最小値を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= Ti <= 10^9',
            examples=[{'input': '3\n5 1 2', 'output': '12'}],
            canonical_reference_solution="def solve() -> None:\n    input()\n    times = sorted(map(int, input().split()))\n    current = 0\n    total = 0\n    for time in times:\n        current += time\n        total += current\n    print(total)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
