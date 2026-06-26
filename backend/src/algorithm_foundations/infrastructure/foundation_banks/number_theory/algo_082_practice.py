from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-082-practice',
    title='素因数分解 を素直に実装する',
    unit_kind='foundation',
    target_skill='素因数分解 を素直に実装する',
    concept_overview='素因数分解は、入力の構造や候補を整理し、決まった手順で答えを作る知識です。まずは典型の使い方を自分の手で追える状態を目指します。',
    problem_bank=[
        problem(
            problem_id='algo-082-practice-p1',
            title='素因数分解 を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='整数 N が与えられる。素因数分解し、`素因数 指数` を素因数の昇順で出力せよ。',
            input_format='1 行目に N。',
            output_format='各行に `p e` を出力する。',
            constraints='2 <= N <= 10^12',
            examples=[
                {
                    'input': '72',
                    'output': '2 3\n3 2',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    out = []\n    d = 2\n    while d * d <= n:\n        if n % d == 0:\n            cnt = 0\n            while n % d == 0:\n                n //= d\n                cnt += 1\n            out.append(f'{d} {cnt}')\n        d += 1\n    if n > 1:\n        out.append(f'{n} 1')\n    print('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-082-practice-p2',
            title='素因数分解 を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、整数 N が与えられる。素因数分解し、`素因数 指数` を素因数の昇順で出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。',
            output_format='各ケースの答えを順に出力する。',
            constraints='2 <= N <= 10^12\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n72\n72',
                    'output': '2 3\n3 2\n2 3\n3 2',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n = int(input())\n    out = []\n    d = 2\n    while d * d <= n:\n        if n % d == 0:\n            cnt = 0\n            while n % d == 0:\n                n //= d\n                cnt += 1\n            out.append(f'{d} {cnt}')\n        d += 1\n    if n > 1:\n        out.append(f'{n} 1')\n    print('\\n'.join(out))\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-082-practice-p3',
            title='素因数分解 を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、整数 N が与えられる。素因数分解し、`素因数 指数` を素因数の昇順で出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。',
            output_format='各ケースの答えを順に出力する。',
            constraints='2 <= N <= 10^12\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n72\n72\n72',
                    'output': '2 3\n3 2\n2 3\n3 2\n2 3\n3 2',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n = int(input())\n    out = []\n    d = 2\n    while d * d <= n:\n        if n % d == 0:\n            cnt = 0\n            while n % d == 0:\n                n //= d\n                cnt += 1\n            out.append(f'{d} {cnt}')\n        d += 1\n    if n > 1:\n        out.append(f'{n} 1')\n    print('\\n'.join(out))\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
