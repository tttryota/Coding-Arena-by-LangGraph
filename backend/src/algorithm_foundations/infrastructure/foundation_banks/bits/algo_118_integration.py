from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-118-integration',
    title='ビットで集合を表現 の総合演習',
    unit_kind='integration',
    target_skill='ビットで集合を表現 の総合演習',
    concept_overview='ビットで集合を表現すると、集合の更新も OR・AND・XOR と補集合の組み合わせで扱えます。2 つの集合を mask で持ち、更新を挟んだあとに和集合と共通部分を集計する軽い総合問題として確認します。',
    problem_bank=[
        problem(
            problem_id='algo-118-integration-p1',
            title='ビットで集合を表現 の総合演習 / 2 つの集合を更新したあとの和集合と共通部分を求める',
            problem_statement='0 以上 59 以下の整数からなる 2 つの集合 A, B がある。Q 個の操作を順に処理したあと、和集合と共通部分の要素数を求めよ。\n`1 s x`: 集合 s に x を追加する。\n`2 s x`: 集合 s から x を削除する。\n`3 s x`: 集合 s に対する x の所属を反転する。\nここで s は 1 または 2 で、それぞれ A, B を表す。',
            input_format='1 行目に NA NB Q。\n2 行目に A の要素。\n3 行目に B の要素。\n続く Q 行に操作。',
            output_format='1 行に `union_size intersection_size` を出力する。',
            constraints='0 <= NA, NB <= 60\n1 <= Q <= 2 * 10^5\n0 <= x < 60\n各初期集合の要素は相異なる',
            examples=[{'input': '2 2 4\n1 5\n3 5\n1 1 3\n2 2 5\n3 1 1\n1 2 4', 'output': '3 1'}],
            canonical_reference_solution="def build_mask(values: list[int]) -> int:\n    mask = 0\n    for value in values:\n        mask |= 1 << value\n    return mask\n\ndef solve() -> None:\n    na, nb, q = map(int, input().split())\n    a = list(map(int, input().split())) if na else []\n    b = list(map(int, input().split())) if nb else []\n    masks = [build_mask(a), build_mask(b)]\n    for _ in range(q):\n        t, s, x = map(int, input().split())\n        bit = 1 << x\n        idx = s - 1\n        if t == 1:\n            masks[idx] |= bit\n        elif t == 2:\n            masks[idx] &= ~bit\n        else:\n            masks[idx] ^= bit\n    print((masks[0] | masks[1]).bit_count(), (masks[0] & masks[1]).bit_count())\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
