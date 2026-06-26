from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-083-practice',
    title='拡張ユークリッドの互除法 を素直に実装する',
    unit_kind='foundation',
    target_skill='拡張ユークリッドの互除法 を素直に実装する',
    concept_overview='拡張ユークリッドの互除法で `ax + by = gcd(a, b)` の係数が分かると、`ax + by = c` の形も解けるようになります。gcd が c を割るかどうかで解の有無が決まる使い方を確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-083-practice-p1',
            title='拡張ユークリッドの互除法 を素直に実装する / ax + by = c を満たす整数解があるか判定し、あれば 1 組を出力する',
            problem_statement='整数 a, b, c が与えられる。`ax + by = c` を満たす整数 x, y が存在するなら Yes とその 1 組を、存在しなければ No を出力せよ。',
            input_format='1 行目に a b c。',
            output_format='存在するなら 1 行目に Yes、2 行目に `x y`。存在しないなら 1 行目に No を出力する。',
            constraints='1 <= a, b, |c| <= 10^18',
            examples=[{'input': '30 18 6', 'output': 'Yes\n-1 2'}],
            canonical_reference_solution="def extgcd(a: int, b: int) -> tuple[int, int, int]:\n    if b == 0:\n        return a, 1, 0\n    g, x1, y1 = extgcd(b, a % b)\n    x = y1\n    y = x1 - (a // b) * y1\n    return g, x, y\n\ndef solve() -> None:\n    a, b, c = map(int, input().split())\n    g, x, y = extgcd(a, b)\n    if c % g != 0:\n        print('No')\n        return\n    scale = c // g\n    print('Yes')\n    print(x * scale, y * scale)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
