from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-052-integration',
    title='活動選択問題 の総合演習',
    unit_kind='integration',
    target_skill='活動選択問題 の総合演習',
    concept_overview='ある活動を必ず選ぶなら、その前に入れられる活動群と後に入れられる活動群を分けて考えられます。必須活動を軸に左右をそれぞれ貪欲に詰める形で、活動選択の考え方をまとめます。',
    problem_bank=[
        problem(
            problem_id='algo-052-integration-p1',
            title='活動選択問題 の総合演習 / 指定された活動 K を必ず含めるときの最大参加数を求める',
            problem_statement='N 個の活動の開始時刻 Si と終了時刻 Ti、および必ず参加する活動番号 K が与えられる。終了時刻ちょうどに次の活動を始めてもよいとして、活動 K を含みつつ参加できる活動数の最大値を求めよ。',
            input_format='1 行目に N K。\n続く N 行に Si Ti。',
            output_format='参加できる活動数の最大値を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= K <= N\n-10^9 <= S_i < T_i <= 10^9',
            examples=[{'input': '5 4\n1 4\n3 5\n0 6\n5 7\n8 9', 'output': '3'}],
            canonical_reference_solution="def greedy(intervals: list[tuple[int, int]]) -> int:\n    intervals.sort(key=lambda item: item[1])\n    ans = 0\n    current_end = None\n    for start, end in intervals:\n        if current_end is not None and start < current_end:\n            continue\n        ans += 1\n        current_end = end\n    return ans\n\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, k = map(int, input().split())\n    activities = [tuple(map(int, input().split())) for _ in range(n)]\n    ks, kt = activities[k - 1]\n    left = []\n    right = []\n    for i, (s, t) in enumerate(activities, start=1):\n        if i == k:\n            continue\n        if t <= ks:\n            left.append((s, t))\n        elif s >= kt:\n            right.append((s, t))\n    print(1 + greedy(left) + greedy(right))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
