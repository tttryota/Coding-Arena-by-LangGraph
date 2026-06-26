from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-090-practice',
    title='約数列挙 で条件に合うものを抜き出す',
    unit_kind='foundation',
    target_skill='約数列挙 で条件に合うものを抜き出す',
    concept_overview='約数列挙では、見つかった約数をそのまま並べるだけでなく、条件に合うものだけを集めることもできます。小さい側と大きい側に分けて集め、最後に昇順へ戻す流れを確認します。',
    problem_bank=[
        problem(
            problem_id='algo-090-practice-p1',
            title='約数列挙 で条件に合うものを抜き出す / K 以上の約数だけを小さい順に出力する',
            problem_statement='整数 N, K が与えられる。N の正の約数のうち K 以上のものだけを小さい順に出力せよ。1 つもなければ `None` を出力する。',
            input_format='1 行目に N K。',
            output_format='条件を満たす約数を空白区切りで出力し、存在しなければ None を出力する。',
            constraints='1 <= N <= 10^12',
            examples=[{'input': '36 6', 'output': '6 9 12 18 36'}],
            canonical_reference_solution="def solve() -> None:\n    n, k = map(int, input().split())\n    small = []\n    large = []\n    d = 1\n    while d * d <= n:\n        if n % d == 0:\n            if d >= k:\n                small.append(d)\n            other = n // d\n            if d * d != n and other >= k:\n                large.append(other)\n        d += 1\n    ans = small + large[::-1]\n    print(' '.join(map(str, ans)) if ans else 'None')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
