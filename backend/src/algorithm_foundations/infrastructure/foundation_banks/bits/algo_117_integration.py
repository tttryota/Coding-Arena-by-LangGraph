from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-117-integration',
    title='ポップカウント（立っているビット数） の総合演習',
    unit_kind='integration',
    target_skill='ポップカウント（立っているビット数） の総合演習',
    concept_overview='ポップカウントは毎回 0 から数え直すだけでなく、bit の反転に合わせて増減を追跡することもできます。現在の mask を保ちながら、立っている本数を更新する状態管理を確認します。',
    problem_bank=[
        problem(
            problem_id='algo-117-integration-p1',
            title='ポップカウント（立っているビット数） の総合演習 / bit を反転しながら現在の bit 数を保つ',
            problem_statement='非負整数 X と Q 個の操作が与えられる。各操作では 1 つの整数 k が与えられ、X の k bit を反転する。各操作の直後の X に対するポップカウントを出力せよ。',
            input_format='1 行目に X Q。\n続く Q 行に k。',
            output_format='各操作の答えを 1 行ずつ出力する。',
            constraints='0 <= X < 2^60\n1 <= Q <= 2 * 10^5\n0 <= k < 60',
            examples=[{'input': '0 5\n1\n3\n1\n2\n3', 'output': '1\n2\n1\n2\n1'}],
            canonical_reference_solution="def solve() -> None:\n    x, q = map(int, input().split())\n    count = x.bit_count()\n    out = []\n    for _ in range(q):\n        k = int(input())\n        if (x >> k) & 1:\n            count -= 1\n        else:\n            count += 1\n        x ^= 1 << k\n        out.append(str(count))\n    print('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
