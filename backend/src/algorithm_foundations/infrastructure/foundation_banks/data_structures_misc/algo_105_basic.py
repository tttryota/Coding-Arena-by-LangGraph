from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-105-basic',
    title='単調デック（スライド最小値） の基本',
    unit_kind='foundation',
    target_skill='単調デック（スライド最小値） の基本',
    concept_overview='単調デック（スライド最小値）は、区間最小値の候補だけを単調に保ちながら並べる知識です。まずは固定長の窓に対して、後ろから不要候補を捨て、前から期限切れを落とす基本形を確認します。',
    problem_bank=[
        problem(
            problem_id='algo-105-basic-p1',
            title='単調デック（スライド最小値） の基本 / 各長さ K の連続部分列について最小値を求める',
            problem_statement='長さ N の整数列 A と幅 K が与えられる。 各長さ K の連続部分列について最小値を求めよ。',
            input_format='1 行目に N K。\n2 行目に A1..AN。',
            output_format='各区間の最小値を空白区切りで出力する。',
            constraints='1 <= K <= N <= 2 * 10^5',
            examples=[{'input': '7 3\n4 2 5 1 6 3 7', 'output': '2 1 1 1 3'}],
            canonical_reference_solution="from collections import deque\n\ndef solve() -> None:\n    n, k = map(int, input().split())\n    a = list(map(int, input().split()))\n    dq = deque()\n    ans = []\n    for i, value in enumerate(a):\n        while dq and a[dq[-1]] >= value:\n            dq.pop()\n        dq.append(i)\n        if dq[0] <= i - k:\n            dq.popleft()\n        if i >= k - 1:\n            ans.append(a[dq[0]])\n    print(*ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
