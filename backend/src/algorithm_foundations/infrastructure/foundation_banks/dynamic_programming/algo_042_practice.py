from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-042-practice',
    title='bitDP（集合に対するDP） を素直に実装する',
    unit_kind='foundation',
    target_skill='bitDP（集合に対するDP） を素直に実装する',
    concept_overview='動的計画法は、小さい状態の答えを先に求め、その結果を使って大きい状態の答えを作る考え方です。状態・遷移・初期値を整理する基本を身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-042-practice-p1',
            title='bitDP（集合に対するDP） を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='N 個の正整数 A と目標値 S が与えられる。 いくつかを選んで合計をちょうど S にできるなら Yes、できなければ No を出力せよ。',
            input_format='1 行目に N S。\n2 行目に A1..AN。',
            output_format='Yes / No を出力する。',
            constraints='1 <= N <= 200\n1 <= S <= 2 * 10^5',
            examples=[
                {
                    'input': '4 11\n2 5 9 4',
                    'output': 'Yes',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    possible = [False] * (s + 1)\n    possible[0] = True\n    for value in a:\n        for cur in range(s, value - 1, -1):\n            if possible[cur - value]:\n                possible[cur] = True\n    print('Yes' if possible[s] else 'No')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-042-practice-p2',
            title='bitDP（集合に対するDP） を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、N 個の正整数 A と目標値 S が与えられる。 いくつかを選んで合計をちょうど S にできるなら Yes、できなければ No を出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N S。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 200\n1 <= S <= 2 * 10^5\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n4 11\n2 5 9 4\n4 11\n2 5 9 4',
                    'output': 'Yes\nYes',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    possible = [False] * (s + 1)\n    possible[0] = True\n    for value in a:\n        for cur in range(s, value - 1, -1):\n            if possible[cur - value]:\n                possible[cur] = True\n    print('Yes' if possible[s] else 'No')\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-042-practice-p3',
            title='bitDP（集合に対するDP） を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、N 個の正整数 A と目標値 S が与えられる。 いくつかを選んで合計をちょうど S にできるなら Yes、できなければ No を出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N S。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 200\n1 <= S <= 2 * 10^5\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n4 11\n2 5 9 4\n4 11\n2 5 9 4\n4 11\n2 5 9 4',
                    'output': 'Yes\nYes\nYes',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    possible = [False] * (s + 1)\n    possible[0] = True\n    for value in a:\n        for cur in range(s, value - 1, -1):\n            if possible[cur - value]:\n                possible[cur] = True\n    print('Yes' if possible[s] else 'No')\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
