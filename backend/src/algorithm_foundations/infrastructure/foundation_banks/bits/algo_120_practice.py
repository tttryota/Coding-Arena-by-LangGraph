from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-120-practice',
    title='ビットシフトによる高速化 を素直に実装する',
    unit_kind='foundation',
    target_skill='ビットシフトによる高速化 を素直に実装する',
    concept_overview='ビットシフトでは、k bit 左にずらすと 2^k 倍、右にずらすと 2^k での整数除算になります。同じシフトでも、数値そのものではなく完全二分木上の位置を状態として持つ別視点の実装を確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-120-practice-p1',
            title='ビットシフトによる高速化 を素直に実装する / 二分木上の移動後の頂点番号を求める',
            problem_statement='完全二分木で、根の番号を 1 とする。現在位置 X と長さ Q の操作列が与えられる。`L` は左の子へ移動、`R` は右の子へ移動、`U` は親へ移動を表す。すべての操作を行ったあとの頂点番号を出力せよ。操作は常に有効である。',
            input_format='1 行目に X Q。\n2 行目に長さ Q の文字列 S。',
            output_format='最終的な頂点番号を出力する。',
            constraints='1 <= X < 2^60\n1 <= Q <= 2 * 10^5\nS は `L`, `R`, `U` からなる\n操作は常に有効で、途中結果は 2^63 未満',
            examples=[{'input': '5 5\nLRUUL', 'output': '10'}],
            canonical_reference_solution="def solve() -> None:\n    x, q = map(int, input().split())\n    s = input().strip()\n    for ch in s:\n        if ch == 'L':\n            x <<= 1\n        elif ch == 'R':\n            x = (x << 1) | 1\n        else:\n            x >>= 1\n    print(x)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
