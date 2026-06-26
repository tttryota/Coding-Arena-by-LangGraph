from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-109-basic',
    title='点と直線の距離 の基本',
    unit_kind='foundation',
    target_skill='点と直線の距離 の基本',
    concept_overview='図形・座標の問題は、点や線の位置関係を式に直し、距離・面積・向きなどを使って判定する知識です。図を数式として扱う基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-109-basic-p1',
            title='点と直線の距離 の基本 / 1 ケースをそのまま解く',
            problem_statement='点 P と直線 AB が与えられる。P から直線 AB への距離を求めよ。',
            input_format='1 行目に px py ax ay bx by。',
            output_format='距離を出力する。',
            constraints='座標は整数',
            examples=[
                {
                    'input': '0 2 -1 0 1 0',
                    'output': '2.0',
                },
            ],
            canonical_reference_solution="import math\n\ndef solve() -> None:\n    px, py, ax, ay, bx, by = map(int, input().split())\n    cross = abs((bx - ax) * (py - ay) - (by - ay) * (px - ax))\n    length = math.hypot(bx - ax, by - ay)\n    print(cross / length)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-109-basic-p2',
            title='点と直線の距離 の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、点 P と直線 AB が与えられる。P から直線 AB への距離を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に px py ax ay bx by。',
            output_format='各ケースの答えを順に出力する。',
            constraints='座標は整数\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n0 2 -1 0 1 0\n0 2 -1 0 1 0',
                    'output': '2.0\n2.0',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nimport math\n\ndef solve_one() -> None:\n    px, py, ax, ay, bx, by = map(int, input().split())\n    cross = abs((bx - ax) * (py - ay) - (by - ay) * (px - ax))\n    length = math.hypot(bx - ax, by - ay)\n    print(cross / length)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-109-basic-p3',
            title='点と直線の距離 の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、点 P と直線 AB が与えられる。P から直線 AB への距離を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に px py ax ay bx by。',
            output_format='各ケースの答えを順に出力する。',
            constraints='座標は整数\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n0 2 -1 0 1 0\n0 2 -1 0 1 0\n0 2 -1 0 1 0',
                    'output': '2.0\n2.0\n2.0',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nimport math\n\ndef solve_one() -> None:\n    px, py, ax, ay, bx, by = map(int, input().split())\n    cross = abs((bx - ax) * (py - ay) - (by - ay) * (px - ax))\n    length = math.hypot(bx - ax, by - ay)\n    print(cross / length)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
