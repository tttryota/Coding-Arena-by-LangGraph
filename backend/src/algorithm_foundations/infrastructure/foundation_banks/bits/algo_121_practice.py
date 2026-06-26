from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-121-practice',
    title='最下位ビット（LSB）の取得 を素直に実装する',
    unit_kind='foundation',
    target_skill='最下位ビット（LSB）の取得 を素直に実装する',
    concept_overview='ビット演算は、整数を 2 進数として見て、立っている桁の有無で状態や条件を扱う知識です。集合や状態をコンパクトに表す基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-121-practice-p1',
            title='最下位ビット（LSB）の取得 を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='非負整数 X が与えられる。最下位の立っているビットの値を出力せよ。X=0 のときは 0 を出力する。',
            input_format='1 行目に X。',
            output_format='答えを出力する。',
            constraints='0 <= X < 2^60',
            examples=[
                {
                    'input': '12',
                    'output': '4',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    x = int(input())\n    print(x & -x if x else 0)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-121-practice-p2',
            title='最下位ビット（LSB）の取得 を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、非負整数 X が与えられる。最下位の立っているビットの値を出力せよ。X=0 のときは 0 を出力する。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に X。',
            output_format='各ケースの答えを順に出力する。',
            constraints='0 <= X < 2^60\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n12\n12',
                    'output': '4\n4',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    x = int(input())\n    print(x & -x if x else 0)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-121-practice-p3',
            title='最下位ビット（LSB）の取得 を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、非負整数 X が与えられる。最下位の立っているビットの値を出力せよ。X=0 のときは 0 を出力する。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に X。',
            output_format='各ケースの答えを順に出力する。',
            constraints='0 <= X < 2^60\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n12\n12\n12',
                    'output': '4\n4\n4',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    x = int(input())\n    print(x & -x if x else 0)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
