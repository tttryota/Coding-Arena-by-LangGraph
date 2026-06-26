from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-003-basic',
    title='三分探索 の基本',
    unit_kind='foundation',
    target_skill='三分探索 の基本',
    concept_overview='三分探索は、値が山型や谷型に変化するとき、比較する位置を 3 分するように動かして最適値に近づく解き方です。関数の形に注目して範囲を狭める感覚を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-003-basic-p1',
            title='三分探索 の基本 / 1 ケースをそのまま解く',
            problem_statement='下に凸な数列 A が与えられる。最小値を求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='最小値を出力する。',
            constraints='3 <= N <= 2 * 10^5\nA は下に凸',
            examples=[
                {
                    'input': '7\n9 6 4 2 3 5 8',
                    'output': '2',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    left, right = 0, n - 1\n    while right - left > 3:\n        m1 = left + (right - left) // 3\n        m2 = right - (right - left) // 3\n        if a[m1] <= a[m2]:\n            right = m2 - 1\n        else:\n            left = m1 + 1\n    print(min(a[left:right + 1]))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-003-basic-p2',
            title='三分探索 の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、下に凸な数列 A が与えられる。最小値を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='3 <= N <= 2 * 10^5\nA は下に凸\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n7\n9 6 4 2 3 5 8\n7\n9 6 4 2 3 5 8',
                    'output': '2\n2',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    left, right = 0, n - 1\n    while right - left > 3:\n        m1 = left + (right - left) // 3\n        m2 = right - (right - left) // 3\n        if a[m1] <= a[m2]:\n            right = m2 - 1\n        else:\n            left = m1 + 1\n    print(min(a[left:right + 1]))\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-003-basic-p3',
            title='三分探索 の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、下に凸な数列 A が与えられる。最小値を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='3 <= N <= 2 * 10^5\nA は下に凸\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n7\n9 6 4 2 3 5 8\n7\n9 6 4 2 3 5 8\n7\n9 6 4 2 3 5 8',
                    'output': '2\n2\n2',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    left, right = 0, n - 1\n    while right - left > 3:\n        m1 = left + (right - left) // 3\n        m2 = right - (right - left) // 3\n        if a[m1] <= a[m2]:\n            right = m2 - 1\n        else:\n            left = m1 + 1\n    print(min(a[left:right + 1]))\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
