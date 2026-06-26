from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-059-basic',
    title='締切付きジョブスケジューリング の基本',
    unit_kind='foundation',
    target_skill='締切付きジョブスケジューリング の基本',
    concept_overview='締切付きジョブスケジューリングは、日付順に候補仕事を集め、その時点で報酬の高い仕事を優先して選ぶ知識です。締切までにできる仕事数を守りながら報酬合計を最大化する基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-059-basic-p1',
            title='締切付きジョブスケジューリング の基本 / 締切日までに終えた仕事の報酬合計の最大値を求める',
            problem_statement='N 個の仕事があり、i 番目の締切は Di、報酬は Pi である。各仕事は 1 日かかり、1 日に 1 つだけ行える。締切日までに終えた仕事の報酬合計の最大値を求めよ。',
            input_format='1 行目に N。\n続く N 行に Di Pi。',
            output_format='得られる報酬合計の最大値を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= Di <= 2 * 10^5\n1 <= Pi <= 10^9',
            examples=[{'input': '4\n1 20\n2 10\n2 100\n1 30', 'output': '130'}],
            canonical_reference_solution="import heapq\n\ndef solve() -> None:\n    n = int(input())\n    jobs = [tuple(map(int, input().split())) for _ in range(n)]\n    jobs.sort()\n    chosen = []\n    for deadline, reward in jobs:\n        heapq.heappush(chosen, reward)\n        if len(chosen) > deadline:\n            heapq.heappop(chosen)\n    print(sum(chosen))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
