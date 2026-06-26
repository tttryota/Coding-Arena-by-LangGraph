from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-115-practice',
    title='ビットマスクの基本操作 を素直に実装する',
    unit_kind='foundation',
    target_skill='ビットマスクの基本操作 を素直に実装する',
    concept_overview='ビットマスクの基本操作では、対象 bit だけを書き換えながら 1 つの状態を保ちます。更新と判定を交互に処理し、現在の mask を逐次更新する流れを確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-115-practice-p1',
            title='ビットマスクの基本操作 を素直に実装する / set, clear, test を順に処理する',
            problem_statement='非負整数 X と Q 個の操作が与えられる。`1 k` は k bit を立てる、`2 k` は k bit を下ろす、`3 k` は k bit が立っていれば 1、そうでなければ 0 を出力せよ。',
            input_format='1 行目に X Q。\n続く Q 行に操作。',
            output_format='type=3 のたびに答えを 1 行ずつ出力する。',
            constraints='0 <= X < 2^60\n1 <= Q <= 2 * 10^5\n0 <= k < 60',
            examples=[{'input': '0 5\n1 2\n3 2\n2 2\n3 2\n3 1', 'output': '1\n0\n0'}],
            canonical_reference_solution="def solve() -> None:\n    x, q = map(int, input().split())\n    out = []\n    for _ in range(q):\n        t, k = map(int, input().split())\n        mask = 1 << k\n        if t == 1:\n            x |= mask\n        elif t == 2:\n            x &= ~mask\n        else:\n            out.append(str((x >> k) & 1))\n    print('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
