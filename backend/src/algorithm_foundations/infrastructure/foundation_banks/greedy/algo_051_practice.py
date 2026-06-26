from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-051-practice',
    title='参加計画が実行できるかを順に確かめる',
    unit_kind='foundation',
    target_skill='参加計画が実行できるかを順に確かめる',
    concept_overview='2 つの活動の両立判定が分かったら、次は複数個の計画を前から順に検査します。いま最後に終わった活動時刻を持ちながら、提案された順番どおりに実行可能かを確認します。',
    problem_bank=[
        problem(
            problem_id='algo-051-practice-p1',
            title='参加計画が実行できるかを順に確かめる / 指定された順番の活動列が実行可能かを判定する',
            problem_statement='N 個の活動の開始時刻 Si と終了時刻 Ti が与えられる。M 個の活動番号 a1, a2, ..., aM が提案されるので、この順番どおりにすべて参加できるかを判定せよ。活動は半開区間 [Si, Ti) で表され、ある活動の終了時刻と次の活動の開始時刻が等しいときは続けて参加できる。',
            input_format='1 行目に N M。\n続く N 行に Si Ti。\n最後の 1 行に a1 a2 ... aM。',
            output_format='提案された順番どおりにすべて参加できるなら Yes、できないなら No を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= M <= 2 * 10^5\n-10^9 <= S_i < T_i <= 10^9\n1 <= a_i <= N',
            examples=[{'input': '5 3\n1 3\n3 5\n5 8\n4 6\n8 10\n1 2 5', 'output': 'Yes'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    activities = [tuple(map(int, input().split())) for _ in range(n)]\n    order = list(map(int, input().split()))\n    current_end = None\n    for idx in order:\n        start, end = activities[idx - 1]\n        if current_end is not None and start < current_end:\n            print('No')\n            return\n        current_end = end\n    print('Yes')\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
