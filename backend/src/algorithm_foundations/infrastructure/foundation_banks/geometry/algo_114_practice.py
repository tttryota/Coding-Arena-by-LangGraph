from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-114-practice',
    title='円と直線の交点 を素直に実装する',
    unit_kind='foundation',
    target_skill='円と直線の交点 を素直に実装する',
    concept_overview='図形・座標の問題は、点や線の位置関係を式に直し、距離・面積・向きなどを使って判定する知識です。図を数式として扱う基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-114-practice-p1',
            title='円と直線の交点 を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='円の中心 C と半径 r、直線 AB が与えられる。交点の個数を 0, 1, 2 のいずれかで出力せよ。',
            input_format='1 行目に cx cy r ax ay bx by。',
            output_format='交点の個数を出力する。',
            constraints='座標と半径は整数',
            examples=[
                {
                    'input': '0 0 5 -10 0 10 0',
                    'output': '2',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import math\n    cx, cy, r, ax, ay, bx, by = map(int, input().split())\n    cross = abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax))\n    length = math.hypot(bx - ax, by - ay)\n    dist = cross / length\n    if dist > r:\n        print(0)\n    elif abs(dist - r) < 1e-9:\n        print(1)\n    else:\n        print(2)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-114-practice-p2',
            title='円と直線の交点 を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、円の中心 C と半径 r、直線 AB が与えられる。交点の個数を 0, 1, 2 のいずれかで出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に cx cy r ax ay bx by。',
            output_format='各ケースの答えを順に出力する。',
            constraints='座標と半径は整数\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n0 0 5 -10 0 10 0\n0 0 5 -10 0 10 0',
                    'output': '2\n2',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import math\n    cx, cy, r, ax, ay, bx, by = map(int, input().split())\n    cross = abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax))\n    length = math.hypot(bx - ax, by - ay)\n    dist = cross / length\n    if dist > r:\n        print(0)\n    elif abs(dist - r) < 1e-9:\n        print(1)\n    else:\n        print(2)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-114-practice-p3',
            title='円と直線の交点 を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、円の中心 C と半径 r、直線 AB が与えられる。交点の個数を 0, 1, 2 のいずれかで出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に cx cy r ax ay bx by。',
            output_format='各ケースの答えを順に出力する。',
            constraints='座標と半径は整数\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n0 0 5 -10 0 10 0\n0 0 5 -10 0 10 0\n0 0 5 -10 0 10 0',
                    'output': '2\n2\n2',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import math\n    cx, cy, r, ax, ay, bx, by = map(int, input().split())\n    cross = abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax))\n    length = math.hypot(bx - ax, by - ay)\n    dist = cross / length\n    if dist > r:\n        print(0)\n    elif abs(dist - r) < 1e-9:\n        print(1)\n    else:\n        print(2)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
