from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-053-basic',
    title='ハフマン符号 の基本',
    unit_kind='foundation',
    target_skill='ハフマン符号 の基本',
    concept_overview='貪欲法は、その時点で最もよさそうな選択を順に確定していく考え方です。後戻りせずに決めてよい条件を見抜く基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-053-basic-p1',
            title='ハフマン符号 の基本 / 1 ケースをそのまま解く',
            problem_statement='N 個の正整数が与えられる。毎回 2 つを選んでまとめ、その和のコストを支払う。これを 1 個になるまで続けるとき、支払うコスト合計の最小値を求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='最小コストを出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= Ai <= 10^9',
            examples=[
                {
                    'input': '4\n8 4 6 12',
                    'output': '58',
                },
            ],
            canonical_reference_solution="import heapq\n\ndef solve() -> None:\n    input()\n    heap = list(map(int, input().split()))\n    heapq.heapify(heap)\n    total = 0\n    while len(heap) > 1:\n        x = heapq.heappop(heap)\n        y = heapq.heappop(heap)\n        merged = x + y\n        total += merged\n        heapq.heappush(heap, merged)\n    print(total)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-053-basic-p2',
            title='ハフマン符号 の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、N 個の正整数が与えられる。毎回 2 つを選んでまとめ、その和のコストを支払う。これを 1 個になるまで続けるとき、支払うコスト合計の最小値を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= Ai <= 10^9\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n4\n8 4 6 12\n4\n8 4 6 12',
                    'output': '58\n58',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nimport heapq\n\ndef solve_one() -> None:\n    input()\n    heap = list(map(int, input().split()))\n    heapq.heapify(heap)\n    total = 0\n    while len(heap) > 1:\n        x = heapq.heappop(heap)\n        y = heapq.heappop(heap)\n        merged = x + y\n        total += merged\n        heapq.heappush(heap, merged)\n    print(total)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-053-basic-p3',
            title='ハフマン符号 の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、N 個の正整数が与えられる。毎回 2 つを選んでまとめ、その和のコストを支払う。これを 1 個になるまで続けるとき、支払うコスト合計の最小値を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= Ai <= 10^9\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n4\n8 4 6 12\n4\n8 4 6 12\n4\n8 4 6 12',
                    'output': '58\n58\n58',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nimport heapq\n\ndef solve_one() -> None:\n    input()\n    heap = list(map(int, input().split()))\n    heapq.heapify(heap)\n    total = 0\n    while len(heap) > 1:\n        x = heapq.heappop(heap)\n        y = heapq.heappop(heap)\n        merged = x + y\n        total += merged\n        heapq.heappush(heap, merged)\n    print(total)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
