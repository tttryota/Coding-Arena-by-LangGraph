from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-118-basic',
    title='ビットで集合を表現 の基本',
    unit_kind='foundation',
    target_skill='ビットで集合を表現 の基本',
    concept_overview='ビットで集合を表現する方法は、各要素の有無を対応する bit の 0/1 で持つ知識です。まずは 1 つの集合を mask に変換し、各要素が含まれるかを bit の参照で判定する最も基本の使い方を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-118-basic-p1',
            title='ビットで集合を表現 の基本 / 集合に含まれるかを判定せよ',
            problem_statement='0 以上 59 以下の整数からなる集合 A と Q 個の問い合わせが与えられる。A を bit で表現し、各問い合わせ x について x が A に含まれるなら 1、含まれないなら 0 を出力せよ。',
            input_format='1 行目に N Q。\n2 行目に A の要素。\n続く Q 行に x。',
            output_format='各問い合わせに対する答えを 1 行ずつ出力する。',
            constraints='0 <= N, Q <= 2 * 10^5\n0 <= 要素, x < 60\nA の要素は相異なる',
            examples=[{'input': '4 5\n1 3 5 8\n3\n4\n8\n0\n5', 'output': '1\n0\n1\n0\n1'}],
            canonical_reference_solution="def build_mask(values: list[int]) -> int:\n    mask = 0\n    for value in values:\n        mask |= 1 << value\n    return mask\n\ndef solve() -> None:\n    n, q = map(int, input().split())\n    a = list(map(int, input().split())) if n else []\n    mask = build_mask(a)\n    answers = []\n    for _ in range(q):\n        x = int(input())\n        answers.append(str((mask >> x) & 1))\n    print('\\n'.join(answers))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
