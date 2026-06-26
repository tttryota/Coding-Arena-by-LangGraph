from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-091-practice',
    title='オイラーのトーシェント関数 を素直に実装する',
    unit_kind='foundation',
    target_skill='オイラーのトーシェント関数 を素直に実装する',
    concept_overview='オイラー路・オイラー閉路は、辺をちょうど 1 回ずつ通る道が作れるかを考える知識です。次数や通り方の条件を整理する基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-091-practice-p1',
            title='オイラーのトーシェント関数 を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='整数 N が与えられる。オイラーの φ 関数 φ(N) を求めよ。',
            input_format='1 行目に N。',
            output_format='φ(N) を出力する。',
            constraints='1 <= N <= 10^12',
            examples=[
                {
                    'input': '12',
                    'output': '4',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    x = n\n    ans = n\n    p = 2\n    while p * p <= x:\n        if x % p == 0:\n            while x % p == 0:\n                x //= p\n            ans -= ans // p\n        p += 1\n    if x > 1:\n        ans -= ans // x\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-091-practice-p2',
            title='オイラーのトーシェント関数 を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、整数 N が与えられる。オイラーの φ 関数 φ(N) を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 10^12\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n12\n12',
                    'output': '4\n4',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n = int(input())\n    x = n\n    ans = n\n    p = 2\n    while p * p <= x:\n        if x % p == 0:\n            while x % p == 0:\n                x //= p\n            ans -= ans // p\n        p += 1\n    if x > 1:\n        ans -= ans // x\n    print(ans)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-091-practice-p3',
            title='オイラーのトーシェント関数 を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、整数 N が与えられる。オイラーの φ 関数 φ(N) を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 10^12\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n12\n12\n12',
                    'output': '4\n4\n4',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n = int(input())\n    x = n\n    ans = n\n    p = 2\n    while p * p <= x:\n        if x % p == 0:\n            while x % p == 0:\n                x //= p\n            ans -= ans // p\n        p += 1\n    if x > 1:\n        ans -= ans // x\n    print(ans)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
