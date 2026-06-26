from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-041-basic',
    title='桁DP の基本',
    unit_kind='foundation',
    target_skill='桁DP の基本',
    concept_overview='動的計画法は、小さい状態の答えを先に求め、その結果を使って大きい状態の答えを作る考え方です。状態・遷移・初期値を整理する基本を身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-041-basic-p1',
            title='桁DP の基本 / 1 ケースをそのまま解く',
            problem_statement='整数 N が与えられる。0 以上 N 以下で 10 進表記に数字 4 を含まない整数の個数を求めよ。',
            input_format='1 行目に N。',
            output_format='個数を出力する。',
            constraints='0 <= N <= 10^18',
            examples=[
                {
                    'input': '20',
                    'output': '19',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    n = input().strip()\n    equal = 1\n    less = 0\n    for ch in n:\n        digit = ord(ch) - ord('0')\n        next_equal = 0\n        next_less = less * 9\n        for value in range(digit):\n            if value != 4:\n                next_less += equal\n        if digit != 4:\n            next_equal = equal\n        equal = next_equal\n        less = next_less\n    print(equal + less)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-041-basic-p2',
            title='桁DP の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、整数 N が与えられる。0 以上 N 以下で 10 進表記に数字 4 を含まない整数の個数を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。',
            output_format='各ケースの答えを順に出力する。',
            constraints='0 <= N <= 10^18\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n20\n20',
                    'output': '19\n19',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n = input().strip()\n    equal = 1\n    less = 0\n    for ch in n:\n        digit = ord(ch) - ord('0')\n        next_equal = 0\n        next_less = less * 9\n        for value in range(digit):\n            if value != 4:\n                next_less += equal\n        if digit != 4:\n            next_equal = equal\n        equal = next_equal\n        less = next_less\n    print(equal + less)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-041-basic-p3',
            title='桁DP の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、整数 N が与えられる。0 以上 N 以下で 10 進表記に数字 4 を含まない整数の個数を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。',
            output_format='各ケースの答えを順に出力する。',
            constraints='0 <= N <= 10^18\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n20\n20\n20',
                    'output': '19\n19\n19',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n = input().strip()\n    equal = 1\n    less = 0\n    for ch in n:\n        digit = ord(ch) - ord('0')\n        next_equal = 0\n        next_less = less * 9\n        for value in range(digit):\n            if value != 4:\n                next_less += equal\n        if digit != 4:\n            next_equal = equal\n        equal = next_equal\n        less = next_less\n    print(equal + less)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
