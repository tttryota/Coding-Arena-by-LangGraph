from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-110-basic',
    title='多角形の面積（シューレースの公式） の基本',
    unit_kind='foundation',
    target_skill='多角形の面積（シューレースの公式） の基本',
    concept_overview='図形・座標の問題は、点や線の位置関係を式に直し、距離・面積・向きなどを使って判定する知識です。図を数式として扱う基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-110-basic-p1',
            title='多角形の面積（シューレースの公式） の基本 / 1 ケースをそのまま解く',
            problem_statement='頂点が順に与えられる多角形の面積を求めよ。',
            input_format='1 行目に N。\n続く N 行に xi yi。',
            output_format='面積を出力する。',
            constraints='3 <= N <= 2 * 10^5\n座標は整数',
            examples=[
                {
                    'input': '4\n0 0\n2 0\n2 1\n0 1',
                    'output': '2.0',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    points = [tuple(map(int, input().split())) for _ in range(n)]\n    total = 0\n    for i in range(n):\n        x1, y1 = points[i]\n        x2, y2 = points[(i + 1) % n]\n        total += x1 * y2 - y1 * x2\n    print(abs(total) / 2)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-110-basic-p2',
            title='多角形の面積（シューレースの公式） の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、頂点が順に与えられる多角形の面積を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n続く N 行に xi yi。',
            output_format='各ケースの答えを順に出力する。',
            constraints='3 <= N <= 2 * 10^5\n座標は整数\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n4\n0 0\n2 0\n2 1\n0 1\n4\n0 0\n2 0\n2 1\n0 1',
                    'output': '2.0\n2.0',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n = int(input())\n    points = [tuple(map(int, input().split())) for _ in range(n)]\n    total = 0\n    for i in range(n):\n        x1, y1 = points[i]\n        x2, y2 = points[(i + 1) % n]\n        total += x1 * y2 - y1 * x2\n    print(abs(total) / 2)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-110-basic-p3',
            title='多角形の面積（シューレースの公式） の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、頂点が順に与えられる多角形の面積を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n続く N 行に xi yi。',
            output_format='各ケースの答えを順に出力する。',
            constraints='3 <= N <= 2 * 10^5\n座標は整数\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n4\n0 0\n2 0\n2 1\n0 1\n4\n0 0\n2 0\n2 1\n0 1\n4\n0 0\n2 0\n2 1\n0 1',
                    'output': '2.0\n2.0\n2.0',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n = int(input())\n    points = [tuple(map(int, input().split())) for _ in range(n)]\n    total = 0\n    for i in range(n):\n        x1, y1 = points[i]\n        x2, y2 = points[(i + 1) % n]\n        total += x1 * y2 - y1 * x2\n    print(abs(total) / 2)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
