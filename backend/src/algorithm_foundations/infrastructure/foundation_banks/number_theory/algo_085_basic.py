from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-085-basic',
    title='繰り返し二乗法（高速べき乗） の基本',
    unit_kind='foundation',
    target_skill='繰り返し二乗法（高速べき乗） の基本',
    concept_overview='繰り返し二乗法（高速べき乗）は、入力の構造や候補を整理し、決まった手順で答えを作る知識です。まずは典型の使い方を自分の手で追える状態を目指します。',
    problem_bank=[
        problem(
            problem_id='algo-085-basic-p1',
            title='繰り返し二乗法（高速べき乗） の基本 / 1 ケースをそのまま解く',
            problem_statement='整数 a, b, m が与えられる。a^b mod m を求めよ。',
            input_format='1 行目に a b m。',
            output_format='a^b mod m を出力する。',
            constraints='0 <= a, b <= 10^18\n1 <= m <= 10^9 + 7',
            examples=[
                {
                    'input': '2 10 1000',
                    'output': '24',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    a, b, m = map(int, input().split())\n    ans = 1\n    a %= m\n    while b > 0:\n        if b & 1:\n            ans = ans * a % m\n        a = a * a % m\n        b >>= 1\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-085-basic-p2',
            title='繰り返し二乗法（高速べき乗） の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、整数 a, b, m が与えられる。a^b mod m を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に a b m。',
            output_format='各ケースの答えを順に出力する。',
            constraints='0 <= a, b <= 10^18\n1 <= m <= 10^9 + 7\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n2 10 1000\n2 10 1000',
                    'output': '24\n24',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    a, b, m = map(int, input().split())\n    ans = 1\n    a %= m\n    while b > 0:\n        if b & 1:\n            ans = ans * a % m\n        a = a * a % m\n        b >>= 1\n    print(ans)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-085-basic-p3',
            title='繰り返し二乗法（高速べき乗） の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、整数 a, b, m が与えられる。a^b mod m を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に a b m。',
            output_format='各ケースの答えを順に出力する。',
            constraints='0 <= a, b <= 10^18\n1 <= m <= 10^9 + 7\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n2 10 1000\n2 10 1000\n2 10 1000',
                    'output': '24\n24\n24',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    a, b, m = map(int, input().split())\n    ans = 1\n    a %= m\n    while b > 0:\n        if b & 1:\n            ans = ans * a % m\n        a = a * a % m\n        b >>= 1\n    print(ans)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
