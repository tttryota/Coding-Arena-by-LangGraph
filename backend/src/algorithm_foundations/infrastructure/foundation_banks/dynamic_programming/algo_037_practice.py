from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-037-practice',
    title='最長増加部分列（LIS） を素直に実装する',
    unit_kind='foundation',
    target_skill='最長増加部分列（LIS） を素直に実装する',
    concept_overview='LIS は長さだけでなく、直前の位置を覚えておくと実際の増加部分列も復元できます。ここでは 1 本の LIS を出力します。',
    problem_bank=[
        problem(
            problem_id='algo-037-practice-p1',
            title='最長増加部分列（LIS） を素直に実装する / 1 本の LIS を復元する',
            problem_statement='長さ N の整数列 A が与えられる。最長増加部分列の長さと、そのような部分列を 1 つ出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='1 行目に LIS の長さ L、2 行目にその部分列を空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[{'input': '6\n3 1 4 1 5 9', 'output': '4\n1 4 5 9'}],
            canonical_reference_solution="from bisect import bisect_left\n\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    a = list(map(int, input().split()))\n    tails = []\n    tails_index = []\n    prev = [-1] * n\n    for i, value in enumerate(a):\n        pos = bisect_left(tails, value)\n        if pos == len(tails):\n            tails.append(value)\n            tails_index.append(i)\n        else:\n            tails[pos] = value\n            tails_index[pos] = i\n        if pos > 0:\n            prev[i] = tails_index[pos - 1]\n    seq = []\n    cur = tails_index[-1]\n    while cur != -1:\n        seq.append(a[cur])\n        cur = prev[cur]\n    seq.reverse()\n    print(len(seq))\n    print(*seq)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
