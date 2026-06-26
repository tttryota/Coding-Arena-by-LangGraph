from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-105-integration',
    title='単調デック（スライド最小値） の総合演習',
    unit_kind='integration',
    target_skill='単調デック（スライド最小値） の総合演習',
    concept_overview='固定長窓の最小値が取れるようになると、同じ窓に対して最大値も並行して管理できます。ここでは最小値デックと最大値デックを併用し、各窓のばらつき `max-min` を求めます。',
    problem_bank=[
        problem(
            problem_id='algo-105-integration-p1',
            title='単調デック（スライド最小値） の総合演習 / 各長さ K の区間について max-min を求める',
            problem_statement='長さ N の整数列 A と幅 K が与えられる。各長さ K の連続部分列について、`最大値 - 最小値` を求めよ。',
            input_format='1 行目に N K。\n2 行目に A1..AN。',
            output_format='各区間の答えを空白区切りで出力する。',
            constraints='1 <= K <= N <= 2 * 10^5\n0 <= A_i <= 10^9',
            examples=[{'input': '7 3\n4 2 5 1 6 3 7', 'output': '3 4 5 5 4'}],
            canonical_reference_solution="from collections import deque\n\n\ndef solve() -> None:\n    n, k = map(int, input().split())\n    a = list(map(int, input().split()))\n    min_dq = deque()\n    max_dq = deque()\n    ans = []\n\n    for i, value in enumerate(a):\n        while min_dq and a[min_dq[-1]] >= value:\n            min_dq.pop()\n        min_dq.append(i)\n        while max_dq and a[max_dq[-1]] <= value:\n            max_dq.pop()\n        max_dq.append(i)\n\n        if min_dq[0] <= i - k:\n            min_dq.popleft()\n        if max_dq[0] <= i - k:\n            max_dq.popleft()\n\n        if i >= k - 1:\n            ans.append(a[max_dq[0]] - a[min_dq[0]])\n\n    print(*ans)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
