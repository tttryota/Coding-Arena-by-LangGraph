from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-106-basic',
    title='ベクトルの内積・外積 の基本',
    unit_kind='foundation',
    target_skill='ベクトルの内積・外積 の基本',
    concept_overview='内積はベクトルどうしの角の開き方、外積は向きと平行四辺形の符号付き面積を表します。まずは 2 ベクトルから内積・外積そのものを式で計算できるようになります。',
    problem_bank=[
        problem(
            problem_id='algo-106-basic-p1',
            title='ベクトルの内積・外積 の基本 / 2 ベクトルの内積と外積を計算する',
            problem_statement='平面上の 2 ベクトル (ax, ay), (bx, by) が与えられる。内積と外積をこの順に出力せよ。',
            input_format='1 行目に ax ay bx by。',
            output_format='1 行に `dot cross` を出力する。',
            constraints='-10^9 <= ax, ay, bx, by <= 10^9',
            examples=[{'input': '1 2 3 4', 'output': '11 -2'}],
            canonical_reference_solution="def solve() -> None:\n    ax, ay, bx, by = map(int, input().split())\n    dot = ax * bx + ay * by\n    cross = ax * by - ay * bx\n    print(dot, cross)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
