from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-101-practice',
    title='平衡二分探索木 を素直に実装する',
    unit_kind='foundation',
    target_skill='平衡二分探索木 を素直に実装する',
    concept_overview='二分探索は、条件を満たす境目や値を、探索範囲を半分ずつ絞りながら見つける解き方です。単調性を見つけて mid で判定する流れを身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-101-practice-p1',
            title='平衡二分探索木 を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='Q 個の操作が与えられる。`1 x` は x を集合に追加し、`2 x` は x を削除し、 `3 x` は x が存在するなら Yes、そうでなければ No を出力せよ。',
            input_format='1 行目に Q。\n続く Q 行に操作。',
            output_format='type=3 のたびに Yes / No を出力する。',
            constraints='1 <= Q <= 2 * 10^5\n0 <= x <= 10^9',
            examples=[
                {
                    'input': '6\n1 5\n1 2\n3 2\n2 2\n3 2\n3 5',
                    'output': 'Yes\nNo\nYes',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    q = int(input())\n    values = set()\n    out = []\n    for _ in range(q):\n        t, x = map(int, input().split())\n        if t == 1:\n            values.add(x)\n        elif t == 2:\n            values.discard(x)\n        else:\n            out.append('Yes' if x in values else 'No')\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-101-practice-p2',
            title='平衡二分探索木 を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、Q 個の操作が与えられる。`1 x` は x を集合に追加し、`2 x` は x を削除し、 `3 x` は x が存在するなら Yes、そうでなければ No を出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に Q。\n続く Q 行に操作。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= Q <= 2 * 10^5\n0 <= x <= 10^9\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n6\n1 5\n1 2\n3 2\n2 2\n3 2\n3 5\n6\n1 5\n1 2\n3 2\n2 2\n3 2\n3 5',
                    'output': 'Yes\nNo\nYes\nYes\nNo\nYes',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    q = int(input())\n    values = set()\n    out = []\n    for _ in range(q):\n        t, x = map(int, input().split())\n        if t == 1:\n            values.add(x)\n        elif t == 2:\n            values.discard(x)\n        else:\n            out.append('Yes' if x in values else 'No')\n    sys.stdout.write('\\n'.join(out))\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-101-practice-p3',
            title='平衡二分探索木 を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、Q 個の操作が与えられる。`1 x` は x を集合に追加し、`2 x` は x を削除し、 `3 x` は x が存在するなら Yes、そうでなければ No を出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に Q。\n続く Q 行に操作。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= Q <= 2 * 10^5\n0 <= x <= 10^9\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n6\n1 5\n1 2\n3 2\n2 2\n3 2\n3 5\n6\n1 5\n1 2\n3 2\n2 2\n3 2\n3 5\n6\n1 5\n1 2\n3 2\n2 2\n3 2\n3 5',
                    'output': 'Yes\nNo\nYes\nYes\nNo\nYes\nYes\nNo\nYes',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    q = int(input())\n    values = set()\n    out = []\n    for _ in range(q):\n        t, x = map(int, input().split())\n        if t == 1:\n            values.add(x)\n        elif t == 2:\n            values.discard(x)\n        else:\n            out.append('Yes' if x in values else 'No')\n    sys.stdout.write('\\n'.join(out))\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
