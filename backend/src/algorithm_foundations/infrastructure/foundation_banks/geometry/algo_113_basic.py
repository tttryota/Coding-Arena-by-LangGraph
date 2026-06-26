from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-113-basic',
    title='回転・平行移動（アフィン変換） の基本',
    unit_kind='foundation',
    target_skill='回転・平行移動（アフィン変換） の基本',
    concept_overview='図形・座標の問題は、点や線の位置関係を式に直し、距離・面積・向きなどを使って判定する知識です。図を数式として扱う基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-113-basic-p1',
            title='回転・平行移動（アフィン変換） の基本 / 1 ケースをそのまま解く',
            problem_statement='点 (x, y) と Q 個の操作が与えられる。 `T dx dy` は平行移動、`R` は原点まわりに 90 度反時計回り回転とする。 すべて適用した後の座標を出力せよ。',
            input_format='1 行目に x y。\n2 行目に Q。\n続く Q 行に操作。',
            output_format='最終座標を `x y` で出力する。',
            constraints='1 <= Q <= 2 * 10^5\n座標は整数',
            examples=[
                {
                    'input': '1 2\n3\nT 1 0\nR\nT 0 -1',
                    'output': '-2 1',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    x, y = map(int, input().split())\n    q = int(input())\n    for _ in range(q):\n        parts = input().split()\n        if parts[0] == 'T':\n            x += int(parts[1])\n            y += int(parts[2])\n        else:\n            x, y = -y, x\n    print(x, y)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-113-basic-p2',
            title='回転・平行移動（アフィン変換） の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、点 (x, y) と Q 個の操作が与えられる。 `T dx dy` は平行移動、`R` は原点まわりに 90 度反時計回り回転とする。 すべて適用した後の座標を出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に x y。\n2 行目に Q。\n続く Q 行に操作。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= Q <= 2 * 10^5\n座標は整数\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n1 2\n3\nT 1 0\nR\nT 0 -1\n1 2\n3\nT 1 0\nR\nT 0 -1',
                    'output': '-2 1\n-2 1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    x, y = map(int, input().split())\n    q = int(input())\n    for _ in range(q):\n        parts = input().split()\n        if parts[0] == 'T':\n            x += int(parts[1])\n            y += int(parts[2])\n        else:\n            x, y = -y, x\n    print(x, y)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-113-basic-p3',
            title='回転・平行移動（アフィン変換） の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、点 (x, y) と Q 個の操作が与えられる。 `T dx dy` は平行移動、`R` は原点まわりに 90 度反時計回り回転とする。 すべて適用した後の座標を出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に x y。\n2 行目に Q。\n続く Q 行に操作。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= Q <= 2 * 10^5\n座標は整数\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n1 2\n3\nT 1 0\nR\nT 0 -1\n1 2\n3\nT 1 0\nR\nT 0 -1\n1 2\n3\nT 1 0\nR\nT 0 -1',
                    'output': '-2 1\n-2 1\n-2 1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    x, y = map(int, input().split())\n    q = int(input())\n    for _ in range(q):\n        parts = input().split()\n        if parts[0] == 'T':\n            x += int(parts[1])\n            y += int(parts[2])\n        else:\n            x, y = -y, x\n    print(x, y)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
