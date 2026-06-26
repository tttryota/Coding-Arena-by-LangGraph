from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-059-practice',
    title='締切付きジョブスケジューリング を素直に実装する',
    unit_kind='foundation',
    target_skill='締切付きジョブスケジューリング を素直に実装する',
    concept_overview='貪欲法は、その時点で最もよさそうな選択を順に確定していく考え方です。後戻りせずに決めてよい条件を見抜く基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-059-practice-p1',
            title='締切付きジョブスケジューリング を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='N 個の仕事があり、i 番目の締切は Di、報酬は Pi である。各仕事は 1 日かかり、1 日に 1 つだけ行える。締切日までに終えた仕事の報酬合計の最大値を求めよ。',
            input_format='1 行目に N。\n続く N 行に Di Pi。',
            output_format='得られる報酬合計の最大値を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= Di <= 2 * 10^5\n1 <= Pi <= 10^9',
            examples=[
                {
                    'input': '4\n1 20\n2 10\n2 100\n1 30',
                    'output': '130',
                },
            ],
            canonical_reference_solution="import heapq\n\ndef solve() -> None:\n    n = int(input())\n    jobs = [tuple(map(int, input().split())) for _ in range(n)]\n    jobs.sort()\n    chosen = []\n    for deadline, reward in jobs:\n        heapq.heappush(chosen, reward)\n        if len(chosen) > deadline:\n            heapq.heappop(chosen)\n    print(sum(chosen))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-059-practice-p2',
            title='締切付きジョブスケジューリング を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、N 個の仕事があり、i 番目の締切は Di、報酬は Pi である。各仕事は 1 日かかり、1 日に 1 つだけ行える。締切日までに終えた仕事の報酬合計の最大値を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n続く N 行に Di Pi。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= Di <= 2 * 10^5\n1 <= Pi <= 10^9\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n4\n1 20\n2 10\n2 100\n1 30\n4\n1 20\n2 10\n2 100\n1 30',
                    'output': '130\n130',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nimport heapq\n\ndef solve_one() -> None:\n    n = int(input())\n    jobs = [tuple(map(int, input().split())) for _ in range(n)]\n    jobs.sort()\n    chosen = []\n    for deadline, reward in jobs:\n        heapq.heappush(chosen, reward)\n        if len(chosen) > deadline:\n            heapq.heappop(chosen)\n    print(sum(chosen))\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-059-practice-p3',
            title='締切付きジョブスケジューリング を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、N 個の仕事があり、i 番目の締切は Di、報酬は Pi である。各仕事は 1 日かかり、1 日に 1 つだけ行える。締切日までに終えた仕事の報酬合計の最大値を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n続く N 行に Di Pi。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= Di <= 2 * 10^5\n1 <= Pi <= 10^9\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n4\n1 20\n2 10\n2 100\n1 30\n4\n1 20\n2 10\n2 100\n1 30\n4\n1 20\n2 10\n2 100\n1 30',
                    'output': '130\n130\n130',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nimport heapq\n\ndef solve_one() -> None:\n    n = int(input())\n    jobs = [tuple(map(int, input().split())) for _ in range(n)]\n    jobs.sort()\n    chosen = []\n    for deadline, reward in jobs:\n        heapq.heappush(chosen, reward)\n        if len(chosen) > deadline:\n            heapq.heappop(chosen)\n    print(sum(chosen))\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
