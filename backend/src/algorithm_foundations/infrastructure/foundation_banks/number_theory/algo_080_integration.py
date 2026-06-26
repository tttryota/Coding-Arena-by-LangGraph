from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-080-integration',
    title='素数判定・試し割り の活用',
    unit_kind='integration',
    target_skill='素数判定・試し割り の活用',
    concept_overview='試し割りで最初の約数が見つかれば、合成数を 2 つの整数の積としてその場で分けられます。ここでは「素数ならそのまま、合成数なら 1 組の因数を返す」形で試し割りの使い道を確認します。',
    problem_bank=[
        problem(
            problem_id='algo-080-integration-p1',
            title='素数判定・試し割り の活用 / 合成数なら 1 組の因数に分ける',
            problem_statement='整数 X が与えられる。X が素数なら `Prime` を出力せよ。素数でなければ、`a b` を出力せよ。ただし `a * b = X` かつ `1 < a <= b` を満たし、a はできるだけ小さいものとする。',
            input_format='1 行目に X。',
            output_format='素数なら Prime、そうでなければ条件を満たす a と b を空白区切りで出力する。',
            constraints='2 <= X <= 10^12',
            examples=[{'input': '91', 'output': '7 13'}],
            canonical_reference_solution="def solve() -> None:\n    x = int(input())\n    if x == 2:\n        print('Prime')\n        return\n    if x % 2 == 0:\n        print(2, x // 2)\n        return\n    d = 3\n    while d * d <= x:\n        if x % d == 0:\n            print(d, x // d)\n            return\n        d += 2\n    print('Prime')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
