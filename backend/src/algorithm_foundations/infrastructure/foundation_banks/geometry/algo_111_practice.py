from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-111-practice',
    title='点の多角形内包判定 を素直に実装する',
    unit_kind='foundation',
    target_skill='点の多角形内包判定 を素直に実装する',
    concept_overview='図形・座標の問題は、点や線の位置関係を式に直し、距離・面積・向きなどを使って判定する知識です。図を数式として扱う基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-111-practice-p1',
            title='点の多角形内包判定 を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='多角形と点 P が与えられる。P が多角形の内部または辺上なら Yes、外部なら No を出力せよ。',
            input_format='1 行目に N。\n続く N 行に xi yi。\n最後に px py。',
            output_format='Yes / No を出力する。',
            constraints='3 <= N <= 2 * 10^5\n座標は整数',
            examples=[
                {
                    'input': '4\n0 0\n4 0\n4 4\n0 4\n2 2',
                    'output': 'Yes',
                },
            ],
            canonical_reference_solution="def on_segment(ax: int, ay: int, bx: int, by: int, px: int, py: int) -> bool:\n    cross = (bx - ax) * (py - ay) - (by - ay) * (px - ax)\n    if cross != 0:\n        return False\n    return min(ax, bx) <= px <= max(ax, bx) and min(ay, by) <= py <= max(ay, by)\n\ndef solve() -> None:\n    n = int(input())\n    pts = [tuple(map(int, input().split())) for _ in range(n)]\n    px, py = map(int, input().split())\n    inside = False\n    for i in range(n):\n        ax, ay = pts[i]\n        bx, by = pts[(i + 1) % n]\n        if on_segment(ax, ay, bx, by, px, py):\n            print('Yes')\n            return\n        if ((ay > py) != (by > py)):\n            x = (bx - ax) * (py - ay) / (by - ay) + ax\n            if x >= px:\n                inside = not inside\n    print('Yes' if inside else 'No')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-111-practice-p2',
            title='点の多角形内包判定 を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、多角形と点 P が与えられる。P が多角形の内部または辺上なら Yes、外部なら No を出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n続く N 行に xi yi。\n最後に px py。',
            output_format='各ケースの答えを順に出力する。',
            constraints='3 <= N <= 2 * 10^5\n座標は整数\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n4\n0 0\n4 0\n4 4\n0 4\n2 2\n4\n0 0\n4 0\n4 4\n0 4\n2 2',
                    'output': 'Yes\nYes',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef on_segment(ax: int, ay: int, bx: int, by: int, px: int, py: int) -> bool:\n    cross = (bx - ax) * (py - ay) - (by - ay) * (px - ax)\n    if cross != 0:\n        return False\n    return min(ax, bx) <= px <= max(ax, bx) and min(ay, by) <= py <= max(ay, by)\n\ndef solve_one() -> None:\n    n = int(input())\n    pts = [tuple(map(int, input().split())) for _ in range(n)]\n    px, py = map(int, input().split())\n    inside = False\n    for i in range(n):\n        ax, ay = pts[i]\n        bx, by = pts[(i + 1) % n]\n        if on_segment(ax, ay, bx, by, px, py):\n            print('Yes')\n            return\n        if ((ay > py) != (by > py)):\n            x = (bx - ax) * (py - ay) / (by - ay) + ax\n            if x >= px:\n                inside = not inside\n    print('Yes' if inside else 'No')\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-111-practice-p3',
            title='点の多角形内包判定 を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、多角形と点 P が与えられる。P が多角形の内部または辺上なら Yes、外部なら No を出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n続く N 行に xi yi。\n最後に px py。',
            output_format='各ケースの答えを順に出力する。',
            constraints='3 <= N <= 2 * 10^5\n座標は整数\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n4\n0 0\n4 0\n4 4\n0 4\n2 2\n4\n0 0\n4 0\n4 4\n0 4\n2 2\n4\n0 0\n4 0\n4 4\n0 4\n2 2',
                    'output': 'Yes\nYes\nYes',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef on_segment(ax: int, ay: int, bx: int, by: int, px: int, py: int) -> bool:\n    cross = (bx - ax) * (py - ay) - (by - ay) * (px - ax)\n    if cross != 0:\n        return False\n    return min(ax, bx) <= px <= max(ax, bx) and min(ay, by) <= py <= max(ay, by)\n\ndef solve_one() -> None:\n    n = int(input())\n    pts = [tuple(map(int, input().split())) for _ in range(n)]\n    px, py = map(int, input().split())\n    inside = False\n    for i in range(n):\n        ax, ay = pts[i]\n        bx, by = pts[(i + 1) % n]\n        if on_segment(ax, ay, bx, by, px, py):\n            print('Yes')\n            return\n        if ((ay > py) != (by > py)):\n            x = (bx - ax) * (py - ay) / (by - ay) + ax\n            if x >= px:\n                inside = not inside\n    print('Yes' if inside else 'No')\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
