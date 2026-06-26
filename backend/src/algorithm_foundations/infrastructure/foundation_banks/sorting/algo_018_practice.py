from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-018-practice',
    title='基数ソート を素直に実装する',
    unit_kind='foundation',
    target_skill='基数ソート を素直に実装する',
    concept_overview='基数ソートでは、各桁で安定に bucket 分配し、その結果を次の桁へ渡します。1 の位から上位桁へ進み、列全体を昇順にします。',
    problem_bank=[
        problem(
            problem_id='algo-018-practice-p1',
            title='基数ソート を素直に実装する / 非負整数列を昇順に並べる',
            problem_statement='長さ N の非負整数列 A が与えられる。基数ソートで昇順に並べ替えて出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='昇順の列を空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai <= 10^9',
            examples=[{'input': '5\n4 1 5 2 3', 'output': '1 2 3 4 5'}],
            canonical_reference_solution="def solve() -> None:\n    input()\n    a = list(map(int, input().split()))\n    exp = 1\n    while True:\n        buckets = [[] for _ in range(10)]\n        done = True\n        for value in a:\n            digit = (value // exp) % 10\n            buckets[digit].append(value)\n            if value // exp >= 10:\n                done = False\n        a = [value for bucket in buckets for value in bucket]\n        if done:\n            break\n        exp *= 10\n    print(*a)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
