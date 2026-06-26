from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-119-basic',
    title='部分集合の列挙（ビット演算） の基本',
    unit_kind='foundation',
    target_skill='部分集合の列挙（ビット演算） の基本',
    concept_overview='ビット演算は、整数を 2 進数として見て、立っている桁の有無で状態や条件を扱う知識です。集合や状態をコンパクトに表す基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-119-basic-p1',
            title='部分集合の列挙（ビット演算） の基本 / 1 ケースをそのまま解く',
            problem_statement='長さ N の整数列 A が与えられる。全部分集合の和を小さい順に出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='部分集合和を空白区切りで出力する。',
            constraints='1 <= N <= 20',
            examples=[
                {
                    'input': '2\n1 3',
                    'output': '0 1 3 4',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    sums = []\n    for mask in range(1 << n):\n        total = 0\n        for i in range(n):\n            if mask >> i & 1:\n                total += a[i]\n        sums.append(total)\n    sums.sort()\n    print(*sums)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-119-basic-p2',
            title='部分集合の列挙（ビット演算） の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A が与えられる。全部分集合の和を小さい順に出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 20\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n2\n1 3\n2\n1 3',
                    'output': '0 1 3 4\n0 1 3 4',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    sums = []\n    for mask in range(1 << n):\n        total = 0\n        for i in range(n):\n            if mask >> i & 1:\n                total += a[i]\n        sums.append(total)\n    sums.sort()\n    print(*sums)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-119-basic-p3',
            title='部分集合の列挙（ビット演算） の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A が与えられる。全部分集合の和を小さい順に出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 20\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n2\n1 3\n2\n1 3\n2\n1 3',
                    'output': '0 1 3 4\n0 1 3 4\n0 1 3 4',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    sums = []\n    for mask in range(1 << n):\n        total = 0\n        for i in range(n):\n            if mask >> i & 1:\n                total += a[i]\n        sums.append(total)\n    sums.sort()\n    print(*sums)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
