from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-041-basic',
    title='桁DP の基本',
    unit_kind='foundation',
    target_skill='桁DP の基本',
    concept_overview='桁DPでは、上位桁から順に見ながら、ここまで N と一致しているかと条件を破っていないかを状態に持ちます。数を直接列挙せず、桁ごとの制約で個数を数える考え方を身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-041-basic-p1',
            title='桁DP の基本 / 0 以上 N 以下で 10 進表記に数字 4 を含まない整数の個数を求める',
            problem_statement='整数 N が与えられる。0 以上 N 以下で 10 進表記に数字 4 を含まない整数の個数を求めよ。',
            input_format='1 行目に N。',
            output_format='個数を出力する。',
            constraints='0 <= N <= 10^18',
            examples=[{'input': '20', 'output': '19'}],
            canonical_reference_solution="def solve() -> None:\n    n = input().strip()\n    equal = 1\n    less = 0\n    for ch in n:\n        digit = ord(ch) - ord('0')\n        next_equal = 0\n        next_less = less * 9\n        for value in range(digit):\n            if value != 4:\n                next_less += equal\n        if digit != 4:\n            next_equal = equal\n        equal = next_equal\n        less = next_less\n    print(equal + less)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
