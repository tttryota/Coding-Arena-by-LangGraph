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
    concept_overview='活動数の最大値が分かったら、実際にどの活動へ参加するかも同じ貪欲で復元できます。終了時刻順に採用した活動の番号を記録する流れを確認します。',
    problem_bank=[
        problem(
            problem_id='algo-052-practice-p1',
            title='活動選択問題 を素直に実装する / 最大本数で参加する活動の番号を出力する',
            problem_statement='N 個の活動の開始時刻 Si と終了時刻 Ti が与えられる。終了時刻ちょうどに次の活動を始めてもよいとして、参加できる活動数が最大になる 1 つの参加計画を元の番号で出力せよ。',
            input_format='1 行目に N。\n続く N 行に Si Ti。',
            output_format='1 行目に参加する活動数 K、2 行目に参加する活動の番号を、実際に参加する順で空白区切りにして出力する。',
            constraints='1 <= N <= 2 * 10^5\n-10^9 <= S_i < T_i <= 10^9',
            examples=[{'input': '5\n1 4\n3 5\n0 6\n5 7\n8 9', 'output': '3\n1 4 5'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    activities = []\n    for i in range(1, n + 1):\n        s, t = map(int, input().split())\n        activities.append((t, s, i))\n    activities.sort()\n    current_end = None\n    chosen = []\n    for end, start, idx in activities:\n        if current_end is not None and start < current_end:\n            continue\n        chosen.append(idx)\n        current_end = end\n    print(len(chosen))\n    print(*chosen)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
