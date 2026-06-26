from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-105-practice',
    title='単調デック（スライド最小値） を素直に実装する',
    unit_kind='foundation',
    target_skill='単調デック（スライド最小値） を素直に実装する',
    concept_overview='単調デックでは値だけでなく位置も管理しているので、最小値そのものだけでなく「その最小値がどこで現れるか」も取り出せます。ここでは同値が並ぶときの残し方を含めて確認します。',
    problem_bank=[
        problem(
            problem_id='algo-105-practice-p1',
            title='単調デック（スライド最小値） を素直に実装する / 各長さ K の連続部分列で最小値をとる最左位置を求める',
            problem_statement='長さ N の整数列 A と幅 K が与えられる。各長さ K の連続部分列について、その区間で最小値をとる位置を 1-indexed で求めよ。最小値をとる位置が複数あるときは最も左を答えよ。',
            input_format='1 行目に N K。\n2 行目に A1..AN。',
            output_format='各区間の答えを空白区切りで出力する。',
            constraints='1 <= K <= N <= 2 * 10^5',
            examples=[{'input': '7 3\n4 2 2 1 1 3 1', 'output': '2 4 4 4 5'}],
            canonical_reference_solution="from collections import deque\n\ndef solve() -> None:\n    n, k = map(int, input().split())\n    a = list(map(int, input().split()))\n    dq = deque()\n    ans = []\n    for i, value in enumerate(a):\n        while dq and a[dq[-1]] > value:\n            dq.pop()\n        dq.append(i)\n        if dq[0] <= i - k:\n            dq.popleft()\n        if i >= k - 1:\n            ans.append(dq[0] + 1)\n    print(*ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
