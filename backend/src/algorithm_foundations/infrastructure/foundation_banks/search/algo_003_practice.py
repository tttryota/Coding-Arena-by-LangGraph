from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-003-practice',
    title='三分探索 を素直に実装する',
    unit_kind='foundation',
    target_skill='三分探索 を素直に実装する',
    concept_overview='三分探索で候補範囲を十分に狭めたあと、最後だけ素直に走査して答えを確定する場面があります。ここでは谷底が複数マス続く数列を使い、絞り込みと最終確認を組み合わせる形を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-003-practice-p1',
            title='三分探索 を素直に実装する / 谷底が続く数列で最小値の左端位置を求める',
            problem_statement='長さ N の整数列 A が与えられる。A は、はじめ狭義単調減少し、そのあと最小値が連続して現れ、最後に狭義単調増加する数列である。三分探索で候補範囲を狭め、最小値を取る位置のうち最も左を 1-indexed で求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='最小値を取る位置のうち最も左を出力する。',
            constraints='3 <= N <= 2 * 10^5\nA は「狭義単調減少 -> 最小値の連続区間 -> 狭義単調増加」の形',
            examples=[{'input': '9\n9 7 4 2 2 2 3 5 8', 'output': '4'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    left, right = 0, n - 1\n    while right - left > 5:\n        m1 = left + (right - left) // 3\n        m2 = right - (right - left) // 3\n        if a[m1] < a[m2]:\n            right = m2 - 1\n        elif a[m1] > a[m2]:\n            left = m1 + 1\n        else:\n            right = m2\n    best_value = min(a[left:right + 1])\n    for i in range(left, right + 1):\n        if a[i] == best_value:\n            print(i + 1)\n            return\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
