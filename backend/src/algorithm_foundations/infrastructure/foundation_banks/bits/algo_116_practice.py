from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-116-practice',
    title='XORの性質と応用 を素直に実装する',
    unit_kind='foundation',
    target_skill='XORの性質と応用 を素直に実装する',
    concept_overview='ビット演算は、整数を 2 進数として見て、立っている桁の有無で状態や条件を扱う知識です。集合や状態をコンパクトに表す基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-116-practice-p1',
            title='XORの性質と応用 を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='長さ N の整数列 A が与えられる。すべての要素の XOR を求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='XOR を出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai < 2^60',
            examples=[
                {
                    'input': '4\n1 2 3 4',
                    'output': '4',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    input()\n    ans = 0\n    for value in map(int, input().split()):\n        ans ^= value\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-116-practice-p2',
            title='XORの性質と応用 を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A が与えられる。すべての要素の XOR を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai < 2^60\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n4\n1 2 3 4\n4\n1 2 3 4',
                    'output': '4\n4',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    input()\n    ans = 0\n    for value in map(int, input().split()):\n        ans ^= value\n    print(ans)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-116-practice-p3',
            title='XORの性質と応用 を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A が与えられる。すべての要素の XOR を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai < 2^60\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n4\n1 2 3 4\n4\n1 2 3 4\n4\n1 2 3 4',
                    'output': '4\n4\n4',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    input()\n    ans = 0\n    for value in map(int, input().split()):\n        ans ^= value\n    print(ans)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
