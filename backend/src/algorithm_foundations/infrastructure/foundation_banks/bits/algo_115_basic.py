from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-115-basic',
    title='ビットマスクの基本操作 の基本',
    unit_kind='foundation',
    target_skill='ビットマスクの基本操作 の基本',
    concept_overview='ビット演算は、整数を 2 進数として見て、立っている桁の有無で状態や条件を扱う知識です。集合や状態をコンパクトに表す基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-115-basic-p1',
            title='ビットマスクの基本操作 の基本 / 1 ケースをそのまま解く',
            problem_statement='非負整数 X と Q 個の操作が与えられる。 `1 k` は k bit を立てる、`2 k` は k bit を下ろす、`3 k` は k bit が立っていれば 1、そうでなければ 0 を出力せよ。',
            input_format='1 行目に X Q。\n続く Q 行に操作。',
            output_format='type=3 のたびに答えを 1 行ずつ出力する。',
            constraints='0 <= X < 2^60\n1 <= Q <= 2 * 10^5\n0 <= k < 60',
            examples=[
                {
                    'input': '0 5\n1 2\n3 2\n2 2\n3 2\n3 1',
                    'output': '1\n0\n0',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    x, q = map(int, input().split())\n    out = []\n    for _ in range(q):\n        t, k = map(int, input().split())\n        if t == 1:\n            x |= 1 << k\n        elif t == 2:\n            x &= ~(1 << k)\n        else:\n            out.append(str((x >> k) & 1))\n    print('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-115-basic-p2',
            title='ビットマスクの基本操作 の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、非負整数 X と Q 個の操作が与えられる。 `1 k` は k bit を立てる、`2 k` は k bit を下ろす、`3 k` は k bit が立っていれば 1、そうでなければ 0 を出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に X Q。\n続く Q 行に操作。',
            output_format='各ケースの答えを順に出力する。',
            constraints='0 <= X < 2^60\n1 <= Q <= 2 * 10^5\n0 <= k < 60\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n0 5\n1 2\n3 2\n2 2\n3 2\n3 1\n0 5\n1 2\n3 2\n2 2\n3 2\n3 1',
                    'output': '1\n0\n0\n1\n0\n0',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    x, q = map(int, input().split())\n    out = []\n    for _ in range(q):\n        t, k = map(int, input().split())\n        if t == 1:\n            x |= 1 << k\n        elif t == 2:\n            x &= ~(1 << k)\n        else:\n            out.append(str((x >> k) & 1))\n    print('\\n'.join(out))\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-115-basic-p3',
            title='ビットマスクの基本操作 の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、非負整数 X と Q 個の操作が与えられる。 `1 k` は k bit を立てる、`2 k` は k bit を下ろす、`3 k` は k bit が立っていれば 1、そうでなければ 0 を出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に X Q。\n続く Q 行に操作。',
            output_format='各ケースの答えを順に出力する。',
            constraints='0 <= X < 2^60\n1 <= Q <= 2 * 10^5\n0 <= k < 60\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n0 5\n1 2\n3 2\n2 2\n3 2\n3 1\n0 5\n1 2\n3 2\n2 2\n3 2\n3 1\n0 5\n1 2\n3 2\n2 2\n3 2\n3 1',
                    'output': '1\n0\n0\n1\n0\n0\n1\n0\n0',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    x, q = map(int, input().split())\n    out = []\n    for _ in range(q):\n        t, k = map(int, input().split())\n        if t == 1:\n            x |= 1 << k\n        elif t == 2:\n            x &= ~(1 << k)\n        else:\n            out.append(str((x >> k) & 1))\n    print('\\n'.join(out))\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
