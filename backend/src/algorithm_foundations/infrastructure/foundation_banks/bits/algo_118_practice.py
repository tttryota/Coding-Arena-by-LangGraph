from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-118-practice',
    title='ビットで集合を表現 を素直に実装する',
    unit_kind='foundation',
    target_skill='ビットで集合を表現 を素直に実装する',
    concept_overview='ビットで集合を表現すると、和集合は OR、共通部分は AND で計算できます。2 つの集合を別々の mask にして、集合演算の結果を bit_count で集計する視点を確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-118-practice-p1',
            title='ビットで集合を表現 を素直に実装する / bit で表現し、和集合と共通部分の要素数を求める',
            problem_statement='集合 A, B が与えられる。bit で表現し、和集合と共通部分の要素数を求めよ。',
            input_format='1 行目に NA NB。\n2 行目に A の要素。\n3 行目に B の要素。',
            output_format='1 行に `union_size intersection_size` を出力する。',
            constraints='0 <= NA, NB <= 60\n0 <= 要素 < 60\n各集合の要素は相異なる',
            examples=[{'input': '3 3\n1 3 5\n3 4 5', 'output': '4 2'}],
            canonical_reference_solution="def build_mask(values: list[int]) -> int:\n    mask = 0\n    for value in values:\n        mask |= 1 << value\n    return mask\n\ndef solve() -> None:\n    na, nb = map(int, input().split())\n    a = list(map(int, input().split())) if na else []\n    b = list(map(int, input().split())) if nb else []\n    ma = build_mask(a)\n    mb = build_mask(b)\n    print((ma | mb).bit_count(), (ma & mb).bit_count())\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
