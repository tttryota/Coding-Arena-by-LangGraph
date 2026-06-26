from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-051-basic',
    title='区間スケジューリング問題 の基本',
    unit_kind='foundation',
    target_skill='区間スケジューリング問題 の基本',
    concept_overview='貪欲法は、その時点で最もよさそうな選択を順に確定していく考え方です。後戻りせずに決めてよい条件を見抜く基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-051-basic-p1',
            title='区間スケジューリング問題 の基本 / 1 ケースをそのまま解く',
            problem_statement='N 個の区間 [Li, Ri) が与えられる。互いに重ならないように選べる区間数の最大値を求めよ。',
            input_format='1 行目に N。\n続く N 行に Li Ri。',
            output_format='選べる区間数の最大値を出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[
                {
                    'input': '4\n1 3\n2 5\n4 6\n6 7',
                    'output': '3',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    intervals = [tuple(map(int, input().split())) for _ in range(n)]\n    intervals.sort(key=lambda item: item[1])\n    ans = 0\n    current_end = -10 ** 18\n    for left, right in intervals:\n        if left < current_end:\n            continue\n        ans += 1\n        current_end = right\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-051-basic-p2',
            title='区間スケジューリング問題 の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、N 個の区間 [Li, Ri) が与えられる。互いに重ならないように選べる区間数の最大値を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n続く N 行に Li Ri。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n4\n1 3\n2 5\n4 6\n6 7\n4\n1 3\n2 5\n4 6\n6 7',
                    'output': '3\n3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    intervals = [tuple(map(int, input().split())) for _ in range(n)]\n    intervals.sort(key=lambda item: item[1])\n    ans = 0\n    current_end = -10 ** 18\n    for left, right in intervals:\n        if left < current_end:\n            continue\n        ans += 1\n        current_end = right\n    print(ans)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-051-basic-p3',
            title='区間スケジューリング問題 の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、N 個の区間 [Li, Ri) が与えられる。互いに重ならないように選べる区間数の最大値を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n続く N 行に Li Ri。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n4\n1 3\n2 5\n4 6\n6 7\n4\n1 3\n2 5\n4 6\n6 7\n4\n1 3\n2 5\n4 6\n6 7',
                    'output': '3\n3\n3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    intervals = [tuple(map(int, input().split())) for _ in range(n)]\n    intervals.sort(key=lambda item: item[1])\n    ans = 0\n    current_end = -10 ** 18\n    for left, right in intervals:\n        if left < current_end:\n            continue\n        ans += 1\n        current_end = right\n    print(ans)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
