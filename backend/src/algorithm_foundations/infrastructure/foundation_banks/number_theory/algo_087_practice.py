from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-087-practice',
    title='包除原理 を素直に実装する',
    unit_kind='foundation',
    target_skill='包除原理 を素直に実装する',
    concept_overview='包除原理は、入力の構造や候補を整理し、決まった手順で答えを作る知識です。まずは典型の使い方を自分の手で追える状態を目指します。',
    problem_bank=[
        problem(
            problem_id='algo-087-practice-p1',
            title='包除原理 を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='整数 N, A, B が与えられる。1 以上 N 以下で A または B の倍数である整数の個数を求めよ。',
            input_format='1 行目に N A B。',
            output_format='条件を満たす個数を出力する。',
            constraints='1 <= N, A, B <= 10^18',
            examples=[
                {
                    'input': '20 4 6',
                    'output': '6',
                },
            ],
            canonical_reference_solution="from math import gcd\n\ndef solve() -> None:\n    n, a, b = map(int, input().split())\n    lcm = a // gcd(a, b) * b\n    ans = n // a + n // b - n // lcm\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-087-practice-p2',
            title='包除原理 を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、整数 N, A, B が与えられる。1 以上 N 以下で A または B の倍数である整数の個数を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N A B。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, A, B <= 10^18\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n20 4 6\n20 4 6',
                    'output': '6\n6',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom math import gcd\n\ndef solve_one() -> None:\n    n, a, b = map(int, input().split())\n    lcm = a // gcd(a, b) * b\n    ans = n // a + n // b - n // lcm\n    print(ans)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-087-practice-p3',
            title='包除原理 を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、整数 N, A, B が与えられる。1 以上 N 以下で A または B の倍数である整数の個数を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N A B。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, A, B <= 10^18\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n20 4 6\n20 4 6\n20 4 6',
                    'output': '6\n6\n6',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom math import gcd\n\ndef solve_one() -> None:\n    n, a, b = map(int, input().split())\n    lcm = a // gcd(a, b) * b\n    ans = n // a + n // b - n // lcm\n    print(ans)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
