from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-108-basic',
    title='線分の交差判定 の基本',
    unit_kind='foundation',
    target_skill='線分の交差判定 の基本',
    concept_overview='図形・座標の問題は、点や線の位置関係を式に直し、距離・面積・向きなどを使って判定する知識です。図を数式として扱う基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-108-basic-p1',
            title='線分の交差判定 の基本 / 1 ケースをそのまま解く',
            problem_statement='線分 AB と線分 CD が交差するなら Yes、そうでなければ No を出力せよ。',
            input_format='1 行目に ax ay bx by cx cy dx dy。',
            output_format='Yes / No を出力する。',
            constraints='座標は整数',
            examples=[
                {
                    'input': '0 0 4 4 0 4 4 0',
                    'output': 'Yes',
                },
            ],
            canonical_reference_solution="def ccw(ax: int, ay: int, bx: int, by: int, cx: int, cy: int) -> int:\n    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)\n\ndef solve() -> None:\n    ax, ay, bx, by, cx, cy, dx, dy = map(int, input().split())\n    c1 = ccw(ax, ay, bx, by, cx, cy)\n    c2 = ccw(ax, ay, bx, by, dx, dy)\n    c3 = ccw(cx, cy, dx, dy, ax, ay)\n    c4 = ccw(cx, cy, dx, dy, bx, by)\n    print('Yes' if c1 * c2 <= 0 and c3 * c4 <= 0 else 'No')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-108-basic-p2',
            title='線分の交差判定 の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、線分 AB と線分 CD が交差するなら Yes、そうでなければ No を出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に ax ay bx by cx cy dx dy。',
            output_format='各ケースの答えを順に出力する。',
            constraints='座標は整数\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n0 0 4 4 0 4 4 0\n0 0 4 4 0 4 4 0',
                    'output': 'Yes\nYes',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef ccw(ax: int, ay: int, bx: int, by: int, cx: int, cy: int) -> int:\n    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)\n\ndef solve_one() -> None:\n    ax, ay, bx, by, cx, cy, dx, dy = map(int, input().split())\n    c1 = ccw(ax, ay, bx, by, cx, cy)\n    c2 = ccw(ax, ay, bx, by, dx, dy)\n    c3 = ccw(cx, cy, dx, dy, ax, ay)\n    c4 = ccw(cx, cy, dx, dy, bx, by)\n    print('Yes' if c1 * c2 <= 0 and c3 * c4 <= 0 else 'No')\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-108-basic-p3',
            title='線分の交差判定 の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、線分 AB と線分 CD が交差するなら Yes、そうでなければ No を出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に ax ay bx by cx cy dx dy。',
            output_format='各ケースの答えを順に出力する。',
            constraints='座標は整数\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n0 0 4 4 0 4 4 0\n0 0 4 4 0 4 4 0\n0 0 4 4 0 4 4 0',
                    'output': 'Yes\nYes\nYes',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef ccw(ax: int, ay: int, bx: int, by: int, cx: int, cy: int) -> int:\n    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)\n\ndef solve_one() -> None:\n    ax, ay, bx, by, cx, cy, dx, dy = map(int, input().split())\n    c1 = ccw(ax, ay, bx, by, cx, cy)\n    c2 = ccw(ax, ay, bx, by, dx, dy)\n    c3 = ccw(cx, cy, dx, dy, ax, ay)\n    c4 = ccw(cx, cy, dx, dy, bx, by)\n    print('Yes' if c1 * c2 <= 0 and c3 * c4 <= 0 else 'No')\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
