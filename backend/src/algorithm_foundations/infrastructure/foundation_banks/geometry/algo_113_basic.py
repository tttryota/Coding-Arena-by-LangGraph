from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-113-basic',
    title='回転・平行移動（アフィン変換） の基本',
    unit_kind='foundation',
    target_skill='回転・平行移動（アフィン変換） の基本',
    concept_overview='回転と平行移動は、点の座標を順番に更新する操作として扱えます。まずは 1 点に対して操作列をそのまま適用し、90 度反時計回り回転が `(x, y) -> (-y, x)` になることを確実に使えるようにします。',
    problem_bank=[
        problem(
            problem_id='algo-113-basic-p1',
            title='回転・平行移動（アフィン変換） の基本 / 1 点に操作列を順に適用する',
            problem_statement='点 (x, y) と Q 個の操作が与えられる。 `T dx dy` は平行移動、`R` は原点まわりに 90 度反時計回り回転とする。 すべて適用した後の座標を出力せよ。',
            input_format='1 行目に x y。\n2 行目に Q。\n続く Q 行に操作。',
            output_format='最終座標を `x y` で出力する。',
            constraints='1 <= Q <= 2 * 10^5\n座標は整数',
            examples=[{'input': '1 2\n3\nT 1 0\nR\nT 0 -1', 'output': '-2 1'}],
            canonical_reference_solution="def solve() -> None:\n    x, y = map(int, input().split())\n    q = int(input())\n    for _ in range(q):\n        parts = input().split()\n        if parts[0] == 'T':\n            x += int(parts[1])\n            y += int(parts[2])\n        else:\n            x, y = -y, x\n    print(x, y)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
