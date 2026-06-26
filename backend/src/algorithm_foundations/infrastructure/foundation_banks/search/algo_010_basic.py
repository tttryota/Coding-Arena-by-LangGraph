from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-010-basic',
    title='ランダム探索（モンテカルロ法） の基本',
    unit_kind='foundation',
    target_skill='ランダム探索（モンテカルロ法） の基本',
    concept_overview='ランダム探索（モンテカルロ法）は、候補を全列挙せずにランダムに試した候補の中から、その場で最良候補を更新していく知識です。まずは、すでに試した候補列が与えられたときに「最もよい 1 個」を保つ基本形を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-010-basic-p1',
            title='ランダム探索（モンテカルロ法） の基本 / 試した候補列から T に最も近い値を選ぶ',
            problem_statement='あるランダム探索器が M 回の試行で得た候補列 x_1, x_2, ..., x_M と目標値 T が与えられる。試した候補のうち T に最も近い値を出力せよ。差が同じなら値が小さい方を採用する。',
            input_format='1 行目に M T。\n2 行目に x1..xM。',
            output_format='選ばれた値を出力する。',
            constraints='1 <= M <= 2 * 10^5\n-10^9 <= xi, T <= 10^9',
            examples=[{'input': '5 7\n0 10 6 8 5', 'output': '6'}],
            canonical_reference_solution="def solve() -> None:\n    m, target = map(int, input().split())\n    candidates = list(map(int, input().split()))\n    best = candidates[0]\n    best_diff = abs(best - target)\n    for cand in candidates[1:]:\n        diff = abs(cand - target)\n        if diff < best_diff or (diff == best_diff and cand < best):\n            best = cand\n            best_diff = diff\n    print(best)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
