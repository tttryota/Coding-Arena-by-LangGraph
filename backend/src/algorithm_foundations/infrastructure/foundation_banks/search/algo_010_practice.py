from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-010-practice',
    title='ランダム探索（モンテカルロ法） を素直に実装する',
    unit_kind='foundation',
    target_skill='ランダム探索（モンテカルロ法） を素直に実装する',
    concept_overview='ランダム探索（モンテカルロ法）では、1 回の試行で得られる候補が 1 つの値とは限らず、複数の値をまとめて 1 候補として評価することもあります。ここでは試した 2 変数候補の列に対して、評価値と辞書順の tie-break をそろえて最良候補を保持する実装へ広げます。',
    problem_bank=[
        problem(
            problem_id='algo-010-practice-p1',
            title='ランダム探索（モンテカルロ法） を素直に実装する / 試した 2 変数候補の中から x+y が T に最も近い組を選ぶ',
            problem_statement='あるランダム探索器が M 回の試行で得た候補 (x_i, y_i) と目標値 T が与えられる。試した候補のうち x_i + y_i が T に最も近い組を出力せよ。差が同じなら x が小さい方、さらに同じなら y が小さい方を採用する。',
            input_format='1 行目に M T。\n続く M 行に x_i y_i。',
            output_format='選ばれた x, y を空白区切りで出力する。',
            constraints='1 <= M <= 2 * 10^5\n-10^9 <= x_i, y_i, T <= 10^9',
            examples=[{'input': '4 10\n1 7\n3 4\n5 5\n2 8', 'output': '2 8'}],
            canonical_reference_solution="def solve() -> None:\n    m, target = map(int, input().split())\n    best_x = None\n    best_y = None\n    best_diff = None\n    for _ in range(m):\n        x, y = map(int, input().split())\n        diff = abs(x + y - target)\n        if (\n            best_diff is None\n            or diff < best_diff\n            or (diff == best_diff and (x < best_x or (x == best_x and y < best_y)))\n        ):\n            best_x = x\n            best_y = y\n            best_diff = diff\n    print(best_x, best_y)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
