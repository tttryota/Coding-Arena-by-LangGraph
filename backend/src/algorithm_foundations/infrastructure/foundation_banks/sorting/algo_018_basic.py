from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-018-basic',
    title='基数ソート の基本',
    unit_kind='foundation',
    target_skill='基数ソート の基本',
    concept_overview='ソートは、要素を決まった順番に並べ替える知識です。比較や交換をどう進めると目的の順序になるかを手順として理解します。',
    problem_bank=[
        problem(
            problem_id='algo-018-basic-p1',
            title='基数ソート の基本 / 1 ケースをそのまま解く',
            problem_statement='長さ N の非負整数列 A が与えられる。基数ソートで昇順に並べ替えて出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='昇順の列を空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai <= 10^9',
            examples=[
                {
                    'input': '5\n4 1 5 2 3',
                    'output': '1 2 3 4 5',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    input()\n    a = list(map(int, input().split()))\n    exp = 1\n    while True:\n        buckets = [[] for _ in range(10)]\n        done = True\n        for value in a:\n            digit = (value // exp) % 10\n            buckets[digit].append(value)\n            if value // exp >= 10:\n                done = False\n        a = [value for bucket in buckets for value in bucket]\n        if done:\n            break\n        exp *= 10\n    print(*a)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-018-basic-p2',
            title='基数ソート の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、長さ N の非負整数列 A が与えられる。基数ソートで昇順に並べ替えて出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai <= 10^9\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n5\n4 1 5 2 3\n5\n4 1 5 2 3',
                    'output': '1 2 3 4 5\n1 2 3 4 5',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    input()\n    a = list(map(int, input().split()))\n    exp = 1\n    while True:\n        buckets = [[] for _ in range(10)]\n        done = True\n        for value in a:\n            digit = (value // exp) % 10\n            buckets[digit].append(value)\n            if value // exp >= 10:\n                done = False\n        a = [value for bucket in buckets for value in bucket]\n        if done:\n            break\n        exp *= 10\n    print(*a)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-018-basic-p3',
            title='基数ソート の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、長さ N の非負整数列 A が与えられる。基数ソートで昇順に並べ替えて出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai <= 10^9\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n5\n4 1 5 2 3\n5\n4 1 5 2 3\n5\n4 1 5 2 3',
                    'output': '1 2 3 4 5\n1 2 3 4 5\n1 2 3 4 5',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    input()\n    a = list(map(int, input().split()))\n    exp = 1\n    while True:\n        buckets = [[] for _ in range(10)]\n        done = True\n        for value in a:\n            digit = (value // exp) % 10\n            buckets[digit].append(value)\n            if value // exp >= 10:\n                done = False\n        a = [value for bucket in buckets for value in bucket]\n        if done:\n            break\n        exp *= 10\n    print(*a)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
