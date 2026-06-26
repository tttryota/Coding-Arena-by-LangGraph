from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-080-basic',
    title='素数判定・試し割り の基本',
    unit_kind='foundation',
    target_skill='素数判定・試し割り の基本',
    concept_overview='素数判定や試し割りは、数の割り切れ方を使って性質を見抜く知識です。まずは 1 個の整数に対して 2 から sqrt(N) までの約数候補だけを調べる基本を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-080-basic-p1',
            title='素数判定・試し割り の基本 / 1 個の整数が素数かどうかを判定する',
            problem_statement='整数 X が与えられる。X が素数なら Yes、素数でなければ No を出力せよ。',
            input_format='1 行目に X。',
            output_format='Yes または No を出力する。',
            constraints='1 <= X <= 10^12',
            examples=[{'input': '17', 'output': 'Yes'}],
            canonical_reference_solution="def is_prime(x: int) -> bool:\n    if x < 2:\n        return False\n    if x == 2:\n        return True\n    if x % 2 == 0:\n        return False\n    d = 3\n    while d * d <= x:\n        if x % d == 0:\n            return False\n        d += 2\n    return True\n\n\ndef solve() -> None:\n    x = int(input())\n    print('Yes' if is_prime(x) else 'No')\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
