from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-052-basic',
    title='活動選択問題 の基本',
    unit_kind='foundation',
    target_skill='活動選択問題 の基本',
    concept_overview='活動選択問題は、次に始められる活動のうち終了が最も早いものを選ぶと、参加できる数を最大化しやすい知識です。終了時刻ちょうど開始可という条件での基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-052-basic-p1',
            title='活動選択問題 の基本 / 終了時刻ちょうどに次の活動を始めてもよいとして、重ならないように参加できる活動数の最大値を求める',
            problem_statement='N 個の活動の開始時刻 Si と終了時刻 Ti が与えられる。終了時刻ちょうどに次の活動を始めてもよいとして、重ならないように参加できる活動数の最大値を求めよ。',
            input_format='1 行目に N。\n続く N 行に Si Ti。',
            output_format='参加できる活動数の最大値を出力する。',
            constraints='1 <= N <= 2 * 10^5\n-10^9 <= S_i < T_i <= 10^9',
            examples=[{'input': '5\n1 4\n3 5\n0 6\n5 7\n8 9', 'output': '3'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    activities = [tuple(map(int, input().split())) for _ in range(n)]\n    activities.sort(key=lambda item: item[1])\n    ans = 0\n    current_end = None\n    for start, end in activities:\n        if current_end is not None and start < current_end:\n            continue\n        ans += 1\n        current_end = end\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
