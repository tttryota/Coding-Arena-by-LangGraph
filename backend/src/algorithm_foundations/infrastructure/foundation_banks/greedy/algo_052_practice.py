from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-052-practice',
    title='活動選択問題 を素直に実装する',
    unit_kind='foundation',
    target_skill='活動選択問題 を素直に実装する',
    concept_overview='貪欲法は、その時点で最もよさそうな選択を順に確定していく考え方です。後戻りせずに決めてよい条件を見抜く基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-052-practice-p1',
            title='活動選択問題 を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='N 個の活動の開始時刻 Si と終了時刻 Ti が与えられる。終了時刻ちょうどに次の活動を始めてもよいとして、重ならないように参加できる活動数の最大値を求めよ。',
            input_format='1 行目に N。\n続く N 行に Si Ti。',
            output_format='参加できる活動数の最大値を出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[
                {
                    'input': '5\n1 4\n3 5\n0 6\n5 7\n8 9',
                    'output': '3',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    activities = [tuple(map(int, input().split())) for _ in range(n)]\n    activities.sort(key=lambda item: item[1])\n    ans = 0\n    current_end = -10 ** 18\n    for start, end in activities:\n        if start < current_end:\n            continue\n        ans += 1\n        current_end = end\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-052-practice-p2',
            title='活動選択問題 を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、N 個の活動の開始時刻 Si と終了時刻 Ti が与えられる。終了時刻ちょうどに次の活動を始めてもよいとして、重ならないように参加できる活動数の最大値を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n続く N 行に Si Ti。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n5\n1 4\n3 5\n0 6\n5 7\n8 9\n5\n1 4\n3 5\n0 6\n5 7\n8 9',
                    'output': '3\n3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    activities = [tuple(map(int, input().split())) for _ in range(n)]\n    activities.sort(key=lambda item: item[1])\n    ans = 0\n    current_end = -10 ** 18\n    for start, end in activities:\n        if start < current_end:\n            continue\n        ans += 1\n        current_end = end\n    print(ans)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-052-practice-p3',
            title='活動選択問題 を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、N 個の活動の開始時刻 Si と終了時刻 Ti が与えられる。終了時刻ちょうどに次の活動を始めてもよいとして、重ならないように参加できる活動数の最大値を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n続く N 行に Si Ti。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n5\n1 4\n3 5\n0 6\n5 7\n8 9\n5\n1 4\n3 5\n0 6\n5 7\n8 9\n5\n1 4\n3 5\n0 6\n5 7\n8 9',
                    'output': '3\n3\n3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    activities = [tuple(map(int, input().split())) for _ in range(n)]\n    activities.sort(key=lambda item: item[1])\n    ans = 0\n    current_end = -10 ** 18\n    for start, end in activities:\n        if start < current_end:\n            continue\n        ans += 1\n        current_end = end\n    print(ans)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
