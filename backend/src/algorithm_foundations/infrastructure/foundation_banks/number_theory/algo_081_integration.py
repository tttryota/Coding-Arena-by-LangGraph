from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-081-integration',
    title='エラトステネスの篩 の総合演習',
    unit_kind='integration',
    target_skill='エラトステネスの篩 の総合演習',
    concept_overview='素数判定やふるいは、数の割り切れ方を使って素数を見分けたり列挙したりする知識です。約数の性質を利用する基本を押さえます。 この unit では、既習の エラトステネスの篩 の基本 と エラトステネスの篩 を素直に実装する を順に使いながら、1 問を分けて解く流れまで確認します。',
    problem_bank=[
        problem(
            problem_id='algo-081-integration-p1',
            title='エラトステネスの篩 の総合演習 / 1 ケースをそのまま解く',
            problem_statement='整数 N が与えられる。1 以上 N 以下の素数の個数を求めよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に N。',
            output_format='素数の個数を出力する。',
            constraints='2 <= N <= 10^7\n使う知識は前提 unit までに限定すること。',
            examples=[
                {
                    'input': '10',
                    'output': '4',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    is_prime = [True] * (n + 1)\n    if n >= 0:\n        is_prime[0] = False\n    if n >= 1:\n        is_prime[1] = False\n    p = 2\n    while p * p <= n:\n        if is_prime[p]:\n            step = p * p\n            for multiple in range(step, n + 1, p):\n                is_prime[multiple] = False\n        p += 1\n    print(sum(is_prime))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-081-integration-p2',
            title='エラトステネスの篩 の総合演習 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、整数 N が与えられる。1 以上 N 以下の素数の個数を求めよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。',
            output_format='各ケースの答えを順に出力する。',
            constraints='2 <= N <= 10^7\n使う知識は前提 unit までに限定すること。\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n10\n10',
                    'output': '4\n4',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n = int(input())\n    is_prime = [True] * (n + 1)\n    if n >= 0:\n        is_prime[0] = False\n    if n >= 1:\n        is_prime[1] = False\n    p = 2\n    while p * p <= n:\n        if is_prime[p]:\n            step = p * p\n            for multiple in range(step, n + 1, p):\n                is_prime[multiple] = False\n        p += 1\n    print(sum(is_prime))\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-081-integration-p3',
            title='エラトステネスの篩 の総合演習 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、整数 N が与えられる。1 以上 N 以下の素数の個数を求めよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。',
            output_format='各ケースの答えを順に出力する。',
            constraints='2 <= N <= 10^7\n使う知識は前提 unit までに限定すること。\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n10\n10\n10',
                    'output': '4\n4\n4',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n = int(input())\n    is_prime = [True] * (n + 1)\n    if n >= 0:\n        is_prime[0] = False\n    if n >= 1:\n        is_prime[1] = False\n    p = 2\n    while p * p <= n:\n        if is_prime[p]:\n            step = p * p\n            for multiple in range(step, n + 1, p):\n                is_prime[multiple] = False\n        p += 1\n    print(sum(is_prime))\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
