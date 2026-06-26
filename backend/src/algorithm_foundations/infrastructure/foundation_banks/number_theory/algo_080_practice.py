from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-080-practice',
    title='素数判定・試し割り を複数回の判定に使う',
    unit_kind='foundation',
    target_skill='素数判定・試し割り を複数回の判定に使う',
    concept_overview='素数判定・試し割りは 1 個の整数だけでなく、複数の整数に対して繰り返し使えます。ここでは各整数ごとに 2 から sqrt(X) までを調べ、素数かどうかを順に判定する練習をします。',
    problem_bank=[
        problem(
            problem_id='algo-080-practice-p1',
            title='素数判定・試し割り を複数回の判定に使う / Q 個の整数が素数かどうかを順に判定する',
            problem_statement='Q 個の整数 X_1, X_2, ..., X_Q が与えられる。各 X_i について、素数なら Yes、素数でなければ No を出力せよ。',
            input_format='1 行目に Q。\n続く Q 行に X_i。',
            output_format='各整数について Yes / No を 1 行ずつ出力する。',
            constraints='1 <= Q <= 2 * 10^4\n1 <= X_i <= 10^12',
            examples=[{'input': '4\n2\n17\n18\n91', 'output': 'Yes\nYes\nNo\nNo'}],
            canonical_reference_solution="def is_prime(x: int) -> bool:\n    if x < 2:\n        return False\n    if x == 2:\n        return True\n    if x % 2 == 0:\n        return False\n    d = 3\n    while d * d <= x:\n        if x % d == 0:\n            return False\n        d += 2\n    return True\n\n\ndef solve() -> None:\n    q = int(input())\n    out = []\n    for _ in range(q):\n        x = int(input())\n        out.append('Yes' if is_prime(x) else 'No')\n    print('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
