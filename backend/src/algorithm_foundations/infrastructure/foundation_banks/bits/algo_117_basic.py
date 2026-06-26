from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-117-basic',
    title='ポップカウント（立っているビット数） の基本',
    unit_kind='foundation',
    target_skill='ポップカウント（立っているビット数） の基本',
    concept_overview='ビット演算は、整数を 2 進数として見て、立っている桁の有無で状態や条件を扱う知識です。集合や状態をコンパクトに表す基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-117-basic-p1',
            title='ポップカウント（立っているビット数） の基本 / 1 ケースをそのまま解く',
            problem_statement='1 つの非負整数 X が与えられる。2 進表現で立っているビット数を求めよ。',
            input_format='1 行目に X。',
            output_format='ビット数を出力する。',
            constraints='0 <= X < 2^60',
            examples=[
                {
                    'input': '13',
                    'output': '3',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    x = int(input())\n    print(x.bit_count())\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-117-basic-p2',
            title='ポップカウント（立っているビット数） の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、1 つの非負整数 X が与えられる。2 進表現で立っているビット数を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に X。',
            output_format='各ケースの答えを順に出力する。',
            constraints='0 <= X < 2^60\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n13\n13',
                    'output': '3\n3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    x = int(input())\n    print(x.bit_count())\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-117-basic-p3',
            title='ポップカウント（立っているビット数） の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、1 つの非負整数 X が与えられる。2 進表現で立っているビット数を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に X。',
            output_format='各ケースの答えを順に出力する。',
            constraints='0 <= X < 2^60\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n13\n13\n13',
                    'output': '3\n3\n3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    x = int(input())\n    print(x.bit_count())\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
