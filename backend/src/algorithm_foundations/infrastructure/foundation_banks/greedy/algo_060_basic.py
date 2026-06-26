from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-060-basic',
    title='イベントソートによる走査 の基本',
    unit_kind='foundation',
    target_skill='イベントソートによる走査 の基本',
    concept_overview='イベントソートによる走査は、開始・終了のような出来事を時刻順に並べ、左から順に見ながら状態を更新する知識です。時刻ごとの変化量を先に作っておくことで、重なり数や同時発生の最大値を素直に求めます。',
    problem_bank=[
        problem(
            problem_id='algo-060-basic-p1',
            title='イベントソートによる走査 の基本 / ある時刻に同時に存在するイベント数の最大値を求める',
            problem_statement='N 個のイベントの開始時刻 L_i と終了時刻 R_i が与えられる。各イベントは区間 [L_i, R_i) の間だけ存在する。ある時刻に同時に存在するイベント数の最大値を求めよ。',
            input_format='1 行目に N。\n続く N 行に L_i R_i。',
            output_format='同時に存在するイベント数の最大値を出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= L_i < R_i <= 10^9',
            examples=[{'input': '4\n1 4\n2 5\n5 7\n6 8', 'output': '2'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    diff = {}\n    for _ in range(n):\n        l, r = map(int, input().split())\n        diff[l] = diff.get(l, 0) + 1\n        diff[r] = diff.get(r, 0) - 1\n    current = 0\n    best = 0\n    for time in sorted(diff):\n        current += diff[time]\n        best = max(best, current)\n    print(best)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
