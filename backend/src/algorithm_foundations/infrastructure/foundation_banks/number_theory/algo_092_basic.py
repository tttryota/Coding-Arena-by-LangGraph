from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-092-basic',
    title='メビウス関数・メビウスの反転公式 の基本',
    unit_kind='foundation',
    target_skill='メビウス関数・メビウスの反転公式 の基本',
    concept_overview='メビウス関数・メビウスの反転公式は、入力の構造や候補を整理し、決まった手順で答えを作る知識です。まずは典型の使い方を自分の手で追える状態を目指します。',
    problem_bank=[
        problem(
            problem_id='algo-092-basic-p1',
            title='メビウス関数・メビウスの反転公式 の基本 / 1 ケースをそのまま解く',
            problem_statement='整数 N が与えられる。メビウス関数 μ(N) を求めよ。',
            input_format='1 行目に N。',
            output_format='μ(N) を出力する。',
            constraints='1 <= N <= 10^12',
            examples=[
                {
                    'input': '30',
                    'output': '-1',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    x = n\n    cnt = 0\n    p = 2\n    while p * p <= x:\n        if x % p == 0:\n            exp = 0\n            while x % p == 0:\n                x //= p\n                exp += 1\n            if exp >= 2:\n                print(0)\n                return\n            cnt += 1\n        p += 1\n    if x > 1:\n        cnt += 1\n    print(-1 if cnt % 2 else 1)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-092-basic-p2',
            title='メビウス関数・メビウスの反転公式 の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、整数 N が与えられる。メビウス関数 μ(N) を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 10^12\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n30\n30',
                    'output': '-1\n-1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n = int(input())\n    x = n\n    cnt = 0\n    p = 2\n    while p * p <= x:\n        if x % p == 0:\n            exp = 0\n            while x % p == 0:\n                x //= p\n                exp += 1\n            if exp >= 2:\n                print(0)\n                return\n            cnt += 1\n        p += 1\n    if x > 1:\n        cnt += 1\n    print(-1 if cnt % 2 else 1)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-092-basic-p3',
            title='メビウス関数・メビウスの反転公式 の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、整数 N が与えられる。メビウス関数 μ(N) を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 10^12\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n30\n30\n30',
                    'output': '-1\n-1\n-1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n = int(input())\n    x = n\n    cnt = 0\n    p = 2\n    while p * p <= x:\n        if x % p == 0:\n            exp = 0\n            while x % p == 0:\n                x //= p\n                exp += 1\n            if exp >= 2:\n                print(0)\n                return\n            cnt += 1\n        p += 1\n    if x > 1:\n        cnt += 1\n    print(-1 if cnt % 2 else 1)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
