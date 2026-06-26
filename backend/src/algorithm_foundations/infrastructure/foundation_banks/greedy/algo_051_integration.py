from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-051-integration',
    title='休憩時間つきの参加計画を検査する',
    unit_kind='integration',
    target_skill='休憩時間つきの参加計画を検査する',
    concept_overview='活動どうしの両立判定に、終了後の休憩時間 D を足すと条件が少し広がります。活動列を順に追いながら、どこで詰まるかを見て「前から何個まで実行できるか」を数える形で橋渡しします。',
    problem_bank=[
        problem(
            problem_id='algo-051-integration-p1',
            title='休憩時間つきの参加計画を検査する / 休憩 D をはさんで前から何個実行できるか数える',
            problem_statement='N 個の活動の開始時刻 Si と終了時刻 Ti、および固定の休憩時間 D が与えられる。M 個の活動番号 a1, a2, ..., aM が提案されるので、この順番で前から順に実行するとき、連続して何個の活動まで参加できるかを求めよ。1 つの活動を終えたら、次の活動の開始までに少なくとも D 時間の休憩が必要である。',
            input_format='1 行目に N M D。\n続く N 行に Si Ti。\n最後の 1 行に a1 a2 ... aM。',
            output_format='連続して実行できる活動数を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= M <= 2 * 10^5\n0 <= D <= 10^9\n-10^9 <= S_i < T_i <= 10^9\n1 <= a_i <= N',
            examples=[{'input': '5 4 1\n1 3\n4 6\n7 9\n3 5\n10 12\n1 2 4 5', 'output': '2'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m, d = map(int, input().split())\n    activities = [tuple(map(int, input().split())) for _ in range(n)]\n    order = list(map(int, input().split()))\n    next_start = None\n    completed = 0\n    for idx in order:\n        start, end = activities[idx - 1]\n        if next_start is not None and start < next_start:\n            break\n        completed += 1\n        next_start = end + d\n    print(completed)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
