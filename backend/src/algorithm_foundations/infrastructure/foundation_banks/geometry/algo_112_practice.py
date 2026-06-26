from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-112-practice',
    title='直線の交差判定 を素直に実装する',
    unit_kind='foundation',
    target_skill='直線の交差判定 を素直に実装する',
    concept_overview='図形・座標の問題は、点や線の位置関係を式に直し、距離・面積・向きなどを使って判定する知識です。図を数式として扱う基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-112-practice-p1',
            title='直線の交差判定 を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='直線 AB と直線 CD が平行なら Parallel、そうでなければ Intersect を出力せよ。',
            input_format='1 行目に ax ay bx by cx cy dx dy。',
            output_format='Parallel または Intersect を出力する。',
            constraints='座標は整数',
            examples=[
                {
                    'input': '0 0 1 1 0 1 1 2',
                    'output': 'Parallel',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    ax, ay, bx, by, cx, cy, dx, dy = map(int, input().split())\n    cross = (bx - ax) * (dy - cy) - (by - ay) * (dx - cx)\n    print('Parallel' if cross == 0 else 'Intersect')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-112-practice-p2',
            title='直線の交差判定 を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、直線 AB と直線 CD が平行なら Parallel、そうでなければ Intersect を出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に ax ay bx by cx cy dx dy。',
            output_format='各ケースの答えを順に出力する。',
            constraints='座標は整数\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n0 0 1 1 0 1 1 2\n0 0 1 1 0 1 1 2',
                    'output': 'Parallel\nParallel',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    ax, ay, bx, by, cx, cy, dx, dy = map(int, input().split())\n    cross = (bx - ax) * (dy - cy) - (by - ay) * (dx - cx)\n    print('Parallel' if cross == 0 else 'Intersect')\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-112-practice-p3',
            title='直線の交差判定 を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、直線 AB と直線 CD が平行なら Parallel、そうでなければ Intersect を出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に ax ay bx by cx cy dx dy。',
            output_format='各ケースの答えを順に出力する。',
            constraints='座標は整数\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n0 0 1 1 0 1 1 2\n0 0 1 1 0 1 1 2\n0 0 1 1 0 1 1 2',
                    'output': 'Parallel\nParallel\nParallel',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    ax, ay, bx, by, cx, cy, dx, dy = map(int, input().split())\n    cross = (bx - ax) * (dy - cy) - (by - ay) * (dx - cx)\n    print('Parallel' if cross == 0 else 'Intersect')\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
