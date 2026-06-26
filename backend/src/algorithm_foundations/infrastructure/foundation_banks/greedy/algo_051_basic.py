from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-051-basic',
    title='活動どうしが両立する条件 の基本',
    unit_kind='foundation',
    target_skill='活動どうしが両立する条件 の基本',
    concept_overview='活動選択に入る前に、まずは 2 つの活動が同じ日に両立できる条件を押さえます。半開区間 [開始, 終了) では、片方の終了時刻がもう片方の開始時刻以下なら両立できます。',
    problem_bank=[
        problem(
            problem_id='algo-051-basic-p1',
            title='活動どうしが両立する条件 の基本 / 2 つの活動を両方行えるかを判定する',
            problem_statement='N 個の活動の開始時刻 Si と終了時刻 Ti が与えられる。活動は半開区間 [Si, Ti) で表され、ある活動の終了時刻と別の活動の開始時刻が等しいときは両方に参加できる。Q 個の問い合わせについて、指定された 2 つの活動に両方参加できるなら Yes、できないなら No を出力せよ。',
            input_format='1 行目に N Q。\n続く N 行に Si Ti。\n続く Q 行に ai bi。',
            output_format='各問い合わせについて Yes または No を 1 行ずつ出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= Q <= 2 * 10^5\n-10^9 <= S_i < T_i <= 10^9\n1 <= a_i, b_i <= N\na_i != b_i',
            examples=[{'input': '4 3\n1 3\n3 5\n2 4\n6 8\n1 2\n1 3\n2 4', 'output': 'Yes\nNo\nYes'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    activities = [tuple(map(int, input().split())) for _ in range(n)]\n    out = []\n    for _ in range(q):\n        a, b = map(int, input().split())\n        sa, ta = activities[a - 1]\n        sb, tb = activities[b - 1]\n        if ta <= sb or tb <= sa:\n            out.append('Yes')\n        else:\n            out.append('No')\n    print('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
