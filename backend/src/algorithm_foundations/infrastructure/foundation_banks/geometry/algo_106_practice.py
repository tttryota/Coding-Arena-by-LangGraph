from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-106-practice',
    title='ベクトルの内積・外積 を素直に実装する',
    unit_kind='foundation',
    target_skill='ベクトルの内積・外積 を使って位置関係を判定する',
    concept_overview='内積の符号で鋭角・直角・鈍角、外積の符号で左回り・一直線・右回りが分かります。計算した値をそのまま答える段階から、その意味を読んで分類する段階へ進みます。',
    problem_bank=[
        problem(
            problem_id='algo-106-practice-p1',
            title='ベクトルの内積・外積 を使って位置関係を判定する / 角の種類と回転の向きを分類する',
            problem_statement='平面上の 2 ベクトル (ax, ay), (bx, by) が与えられる。ベクトルどうしのなす角が鋭角なら `Acute`、直角なら `Right`、鈍角なら `Obtuse` とし、(ax, ay) から (bx, by) への回転が反時計回りなら `Left`、同一直線上なら `Collinear`、時計回りなら `Right` とする。これらをこの順に出力せよ。',
            input_format='1 行目に ax ay bx by。',
            output_format='1 行に `angle turn` を出力する。',
            constraints='-10^9 <= ax, ay, bx, by <= 10^9\n(ax, ay) と (bx, by) はどちらも零ベクトルではない',
            examples=[{'input': '1 1 -1 2', 'output': 'Acute Left'}],
            canonical_reference_solution="def solve() -> None:\n    ax, ay, bx, by = map(int, input().split())\n    dot = ax * bx + ay * by\n    cross = ax * by - ay * bx\n\n    if dot > 0:\n        angle = 'Acute'\n    elif dot == 0:\n        angle = 'Right'\n    else:\n        angle = 'Obtuse'\n\n    if cross > 0:\n        turn = 'Left'\n    elif cross == 0:\n        turn = 'Collinear'\n    else:\n        turn = 'Right'\n\n    print(angle, turn)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
