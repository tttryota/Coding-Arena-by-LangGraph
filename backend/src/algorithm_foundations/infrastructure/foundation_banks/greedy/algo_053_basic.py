from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-053-basic',
    title='ハフマン符号 の基本',
    unit_kind='foundation',
    target_skill='ハフマン符号 の基本',
    concept_overview='ハフマン符号の核になる貪欲法は、毎回いちばん小さい 2 つを先にまとめると総コストを最小にできる知識です。最小 2 要素の併合を繰り返す基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-053-basic-p1',
            title='ハフマン符号 の基本 / これを 1 個になるまで続けるとき、支払うコスト合計の最小値を求める',
            problem_statement='N 個の正整数が与えられる。毎回 2 つを選んでまとめ、その和のコストを支払う。これを 1 個になるまで続けるとき、支払うコスト合計の最小値を求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='最小コストを出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= Ai <= 10^9',
            examples=[{'input': '4\n8 4 6 12', 'output': '58'}],
            canonical_reference_solution="import heapq\n\ndef solve() -> None:\n    input()\n    heap = list(map(int, input().split()))\n    heapq.heapify(heap)\n    total = 0\n    while len(heap) > 1:\n        x = heapq.heappop(heap)\n        y = heapq.heappop(heap)\n        merged = x + y\n        total += merged\n        heapq.heappush(heap, merged)\n    print(total)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
