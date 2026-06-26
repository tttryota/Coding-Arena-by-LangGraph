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
    concept_overview='締切順に候補を見て、超過したら最小報酬を落とす貪欲は、「何日までに何本まで選べるか」という上限が追加されても使えます。ここでは選べる仕事数に上限 K を加えた形へ広げます。',
    problem_bank=[
        problem(
            problem_id='algo-059-practice-p1',
            title='締切付きジョブスケジューリング を素直に実装する / 高々 K 個まで選べるときの最大報酬を求める',
            problem_statement='N 個の仕事があり、i 番目の締切は Di、報酬は Pi である。各仕事は 1 日かかり、1 日に 1 つだけ行える。さらに、選べる仕事は高々 K 個までとする。締切日までに終えた仕事の報酬合計の最大値を求めよ。',
            input_format='1 行目に N K。\n続く N 行に Di Pi。',
            output_format='得られる報酬合計の最大値を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= K <= N\n1 <= Di <= 2 * 10^5\n1 <= Pi <= 10^9',
            examples=[{'input': '5 2\n1 20\n2 10\n2 100\n1 30\n3 40', 'output': '140'}],
            canonical_reference_solution="import heapq\n\n\ndef solve() -> None:\n    n, k = map(int, input().split())\n    jobs = [tuple(map(int, input().split())) for _ in range(n)]\n    jobs.sort()\n    chosen = []\n    for deadline, reward in jobs:\n        heapq.heappush(chosen, reward)\n        limit = min(deadline, k)\n        if len(chosen) > limit:\n            heapq.heappop(chosen)\n    print(sum(chosen))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
