from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-062-basic',
    title='最近点対（closest pair） の基本',
    unit_kind='foundation',
    target_skill='最近点対（closest pair） の基本',
    concept_overview='分割統治は、問題を小さく分けて解き、その結果を合体して元の問題の答えを作る考え方です。分け方と戻し方を整理する基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-062-basic-p1',
            title='最近点対（closest pair） の基本 / 1 ケースをそのまま解く',
            problem_statement='長さ N の整数列 A が与えられる。分割統治を用いて列全体の最小値を求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='最小値を出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[
                {
                    'input': '5\n8 3 6 1 4',
                    'output': '1',
                },
            ],
            canonical_reference_solution="def solve_range(a: list[int], left: int, right: int) -> int:\n    if left == right:\n        return a[left]\n    mid = (left + right) // 2\n    return min(solve_range(a, left, mid), solve_range(a, mid + 1, right))\n\ndef solve() -> None:\n    input()\n    a = list(map(int, input().split()))\n    print(solve_range(a, 0, len(a) - 1))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-062-basic-p2',
            title='最近点対（closest pair） の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A が与えられる。分割統治を用いて列全体の最小値を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n5\n8 3 6 1 4\n5\n8 3 6 1 4',
                    'output': '1\n1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_range(a: list[int], left: int, right: int) -> int:\n    if left == right:\n        return a[left]\n    mid = (left + right) // 2\n    return min(solve_range(a, left, mid), solve_range(a, mid + 1, right))\n\ndef solve_one() -> None:\n    input()\n    a = list(map(int, input().split()))\n    print(solve_range(a, 0, len(a) - 1))\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-062-basic-p3',
            title='最近点対（closest pair） の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A が与えられる。分割統治を用いて列全体の最小値を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n5\n8 3 6 1 4\n5\n8 3 6 1 4\n5\n8 3 6 1 4',
                    'output': '1\n1\n1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_range(a: list[int], left: int, right: int) -> int:\n    if left == right:\n        return a[left]\n    mid = (left + right) // 2\n    return min(solve_range(a, left, mid), solve_range(a, mid + 1, right))\n\ndef solve_one() -> None:\n    input()\n    a = list(map(int, input().split()))\n    print(solve_range(a, 0, len(a) - 1))\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
