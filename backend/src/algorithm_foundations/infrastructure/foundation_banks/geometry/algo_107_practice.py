from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-107-practice',
    title='凸包（Convex Hull） を素直に実装する',
    unit_kind='foundation',
    target_skill='凸包（Convex Hull） を素直に実装する',
    concept_overview='図形・座標の問題は、点や線の位置関係を式に直し、距離・面積・向きなどを使って判定する知識です。図を数式として扱う基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-107-practice-p1',
            title='凸包（Convex Hull） を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='平面上の N 点が与えられる。凸包に含まれる点数を求めよ。',
            input_format='1 行目に N。\n続く N 行に xi yi。',
            output_format='凸包上の点数を出力する。',
            constraints='3 <= N <= 2 * 10^5\n座標は整数',
            examples=[
                {
                    'input': '5\n0 0\n2 0\n2 2\n0 2\n1 1',
                    'output': '4',
                },
            ],
            canonical_reference_solution="def cross(o: tuple[int, int], a: tuple[int, int], b: tuple[int, int]) -> int:\n    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])\n\ndef solve() -> None:\n    n = int(input())\n    pts = sorted({tuple(map(int, input().split())) for _ in range(n)})\n    if len(pts) <= 1:\n        print(len(pts))\n        return\n    lower = []\n    for p in pts:\n        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:\n            lower.pop()\n        lower.append(p)\n    upper = []\n    for p in reversed(pts):\n        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:\n            upper.pop()\n        upper.append(p)\n    hull = lower[:-1] + upper[:-1]\n    print(len(hull))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-107-practice-p2',
            title='凸包（Convex Hull） を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、平面上の N 点が与えられる。凸包に含まれる点数を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n続く N 行に xi yi。',
            output_format='各ケースの答えを順に出力する。',
            constraints='3 <= N <= 2 * 10^5\n座標は整数\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n5\n0 0\n2 0\n2 2\n0 2\n1 1\n5\n0 0\n2 0\n2 2\n0 2\n1 1',
                    'output': '4\n4',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef cross(o: tuple[int, int], a: tuple[int, int], b: tuple[int, int]) -> int:\n    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])\n\ndef solve_one() -> None:\n    n = int(input())\n    pts = sorted({tuple(map(int, input().split())) for _ in range(n)})\n    if len(pts) <= 1:\n        print(len(pts))\n        return\n    lower = []\n    for p in pts:\n        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:\n            lower.pop()\n        lower.append(p)\n    upper = []\n    for p in reversed(pts):\n        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:\n            upper.pop()\n        upper.append(p)\n    hull = lower[:-1] + upper[:-1]\n    print(len(hull))\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-107-practice-p3',
            title='凸包（Convex Hull） を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、平面上の N 点が与えられる。凸包に含まれる点数を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n続く N 行に xi yi。',
            output_format='各ケースの答えを順に出力する。',
            constraints='3 <= N <= 2 * 10^5\n座標は整数\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n5\n0 0\n2 0\n2 2\n0 2\n1 1\n5\n0 0\n2 0\n2 2\n0 2\n1 1\n5\n0 0\n2 0\n2 2\n0 2\n1 1',
                    'output': '4\n4\n4',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef cross(o: tuple[int, int], a: tuple[int, int], b: tuple[int, int]) -> int:\n    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])\n\ndef solve_one() -> None:\n    n = int(input())\n    pts = sorted({tuple(map(int, input().split())) for _ in range(n)})\n    if len(pts) <= 1:\n        print(len(pts))\n        return\n    lower = []\n    for p in pts:\n        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:\n            lower.pop()\n        lower.append(p)\n    upper = []\n    for p in reversed(pts):\n        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:\n            upper.pop()\n        upper.append(p)\n    hull = lower[:-1] + upper[:-1]\n    print(len(hull))\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
