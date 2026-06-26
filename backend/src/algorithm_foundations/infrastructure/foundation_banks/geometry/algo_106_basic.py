from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-106-basic',
    title='ベクトルの内積・外積 の基本',
    unit_kind='foundation',
    target_skill='ベクトルの内積・外積 の基本',
    concept_overview='図形・座標の問題は、点や線の位置関係を式に直し、距離・面積・向きなどを使って判定する知識です。図を数式として扱う基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-106-basic-p1',
            title='ベクトルの内積・外積 の基本 / 1 ケースをそのまま解く',
            problem_statement='平面上の 2 ベクトル (ax, ay), (bx, by) が与えられる。内積と外積をこの順に出力せよ。',
            input_format='1 行目に ax ay bx by。',
            output_format='1 行に `dot cross` を出力する。',
            constraints='各値は整数',
            examples=[
                {
                    'input': '1 2 3 4',
                    'output': '11 -2',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    ax, ay, bx, by = map(int, input().split())\n    dot = ax * bx + ay * by\n    cross = ax * by - ay * bx\n    print(dot, cross)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-106-basic-p2',
            title='ベクトルの内積・外積 の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、平面上の 2 ベクトル (ax, ay), (bx, by) が与えられる。内積と外積をこの順に出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に ax ay bx by。',
            output_format='各ケースの答えを順に出力する。',
            constraints='各値は整数\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n1 2 3 4\n1 2 3 4',
                    'output': '11 -2\n11 -2',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    ax, ay, bx, by = map(int, input().split())\n    dot = ax * bx + ay * by\n    cross = ax * by - ay * bx\n    print(dot, cross)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-106-basic-p3',
            title='ベクトルの内積・外積 の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、平面上の 2 ベクトル (ax, ay), (bx, by) が与えられる。内積と外積をこの順に出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に ax ay bx by。',
            output_format='各ケースの答えを順に出力する。',
            constraints='各値は整数\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n1 2 3 4\n1 2 3 4\n1 2 3 4',
                    'output': '11 -2\n11 -2\n11 -2',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    ax, ay, bx, by = map(int, input().split())\n    dot = ax * bx + ay * by\n    cross = ax * by - ay * bx\n    print(dot, cross)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
