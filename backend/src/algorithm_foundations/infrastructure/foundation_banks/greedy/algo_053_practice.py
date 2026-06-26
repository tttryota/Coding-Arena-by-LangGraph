from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-053-practice',
    title='ハフマン符号 を素直に実装する',
    unit_kind='foundation',
    target_skill='ハフマン符号 を素直に実装する',
    concept_overview='最小 2 要素の併合は、1 個になるまで続けるだけでなく「ちょうど K 個まで減らす」ときにも同じ貪欲が使えます。止める個数を変えたときの最小併合コストを確認します。',
    problem_bank=[
        problem(
            problem_id='algo-053-practice-p1',
            title='ハフマン符号 を素直に実装する / ちょうど K 個の束が残るまで併合するときの最小コストを求める',
            problem_statement='N 個の正整数が与えられる。毎回 2 つを選んでまとめ、その和のコストを支払う。この操作を、値がちょうど K 個残るまで続けるとき、支払うコスト合計の最小値を求めよ。',
            input_format='1 行目に N K。\n2 行目に A1..AN。',
            output_format='最小コストを出力する。',
            constraints='1 <= K <= N <= 2 * 10^5\n1 <= Ai <= 10^9',
            examples=[{'input': '4 2\n8 4 6 12', 'output': '28'}],
            canonical_reference_solution="import heapq\n\n\ndef solve() -> None:\n    n, k = map(int, input().split())\n    heap = list(map(int, input().split()))\n    heapq.heapify(heap)\n    total = 0\n    while len(heap) > k:\n        x = heapq.heappop(heap)\n        y = heapq.heappop(heap)\n        merged = x + y\n        total += merged\n        heapq.heappush(heap, merged)\n    print(total)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
