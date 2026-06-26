from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-115-basic',
    title='ビットマスクの基本操作 の基本',
    unit_kind='foundation',
    target_skill='ビットマスクの基本操作 の基本',
    concept_overview='ビットマスクの基本操作は、整数の各 bit を 0/1 のスイッチとして見て扱う知識です。まずは 1 回だけ set、clear、test のどれかを適用し、各操作が整数をどう変えるかを直接確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-115-basic-p1',
            title='ビットマスクの基本操作 の基本 / 1 回の bit 操作結果を求める',
            problem_statement='非負整数 X と 1 回の操作 `t k` が与えられる。`t=1` なら X の k bit を立てた後の値、`t=2` なら X の k bit を下ろした後の値、`t=3` なら X の k bit が立っていれば 1、そうでなければ 0 を出力せよ。',
            input_format='1 行目に X。\n2 行目に t k。',
            output_format='答えを出力する。',
            constraints='0 <= X < 2^60\n1 <= t <= 3\n0 <= k < 60',
            examples=[{'input': '10\n1 0', 'output': '11'}],
            canonical_reference_solution="def solve() -> None:\n    x = int(input())\n    t, k = map(int, input().split())\n    mask = 1 << k\n    if t == 1:\n        print(x | mask)\n    elif t == 2:\n        print(x & ~mask)\n    else:\n        print((x >> k) & 1)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
