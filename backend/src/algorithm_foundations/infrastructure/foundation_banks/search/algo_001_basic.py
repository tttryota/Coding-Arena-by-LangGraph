from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-001-basic',
    title='全探索（ブルートフォース） の基本',
    unit_kind='foundation',
    target_skill='全探索（ブルートフォース） の基本',
    concept_overview='全探索（ブルートフォース）は、ありえる候補を順番に全部試し、条件を満たすものを見つける解き方です。まずは漏れなく列挙し、1 つずつ判定する形を身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-001-basic-p1',
            title='全探索（ブルートフォース） の基本 / 1 ケースをそのまま解く',
            problem_statement='長さ N の整数列 A と目標値 S が与えられる。 連続部分列または要素の選び方を工夫して、条件を満たすものが存在するか判定せよ。',
            input_format='1 行目に N S。\n2 行目に A1..AN。',
            output_format='条件を満たすなら Yes、そうでなければ No を出力する。',
            constraints='1 <= N <= 40',
            examples=[
                {
                    'input': '4 11\n2 5 9 4',
                    'output': 'Yes',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    n, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    for mask in range(1 << n):\n        total = 0\n        for i in range(n):\n            if mask >> i & 1:\n                total += a[i]\n        if total == s:\n            print('Yes')\n            return\n    print('No')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-001-basic-p2',
            title='全探索（ブルートフォース） の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A と目標値 S が与えられる。 連続部分列または要素の選び方を工夫して、条件を満たすものが存在するか判定せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N S。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 40\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n4 11\n2 5 9 4\n4 11\n2 5 9 4',
                    'output': 'Yes\nYes',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    for mask in range(1 << n):\n        total = 0\n        for i in range(n):\n            if mask >> i & 1:\n                total += a[i]\n        if total == s:\n            print('Yes')\n            return\n    print('No')\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-001-basic-p3',
            title='全探索（ブルートフォース） の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A と目標値 S が与えられる。 連続部分列または要素の選び方を工夫して、条件を満たすものが存在するか判定せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N S。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 40\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n4 11\n2 5 9 4\n4 11\n2 5 9 4\n4 11\n2 5 9 4',
                    'output': 'Yes\nYes\nYes',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    for mask in range(1 << n):\n        total = 0\n        for i in range(n):\n            if mask >> i & 1:\n                total += a[i]\n        if total == s:\n            print('Yes')\n            return\n    print('No')\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
