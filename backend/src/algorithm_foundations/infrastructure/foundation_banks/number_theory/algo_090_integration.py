from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-090-integration',
    title='約数列挙 の総合演習',
    unit_kind='integration',
    target_skill='約数列挙 の総合演習',
    concept_overview='約数列挙は、入力の構造や候補を整理し、決まった手順で答えを作る知識です。まずは典型の使い方を自分の手で追える状態を目指します。 この unit では、既習の 約数列挙 の基本 と 約数列挙 を素直に実装する を順に使いながら、1 問を分けて解く流れまで確認します。',
    problem_bank=[
        problem(
            problem_id='algo-090-integration-p1',
            title='約数列挙 の総合演習 / 1 ケースをそのまま解く',
            problem_statement='整数 N が与えられる。N の正の約数を小さい順にすべて出力せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に N。',
            output_format='正の約数を空白区切りで出力する。',
            constraints='1 <= N <= 10^12\n使う知識は前提 unit までに限定すること。',
            examples=[
                {
                    'input': '12',
                    'output': '1 2 3 4 6 12',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    small = []\n    large = []\n    d = 1\n    while d * d <= n:\n        if n % d == 0:\n            small.append(d)\n            if d * d != n:\n                large.append(n // d)\n        d += 1\n    print(*(small + large[::-1]))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-090-integration-p2',
            title='約数列挙 の総合演習 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、整数 N が与えられる。N の正の約数を小さい順にすべて出力せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 10^12\n使う知識は前提 unit までに限定すること。\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n12\n12',
                    'output': '1 2 3 4 6 12\n1 2 3 4 6 12',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n = int(input())\n    small = []\n    large = []\n    d = 1\n    while d * d <= n:\n        if n % d == 0:\n            small.append(d)\n            if d * d != n:\n                large.append(n // d)\n        d += 1\n    print(*(small + large[::-1]))\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-090-integration-p3',
            title='約数列挙 の総合演習 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、整数 N が与えられる。N の正の約数を小さい順にすべて出力せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 10^12\n使う知識は前提 unit までに限定すること。\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n12\n12\n12',
                    'output': '1 2 3 4 6 12\n1 2 3 4 6 12\n1 2 3 4 6 12',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n = int(input())\n    small = []\n    large = []\n    d = 1\n    while d * d <= n:\n        if n % d == 0:\n            small.append(d)\n            if d * d != n:\n                large.append(n // d)\n        d += 1\n    print(*(small + large[::-1]))\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
