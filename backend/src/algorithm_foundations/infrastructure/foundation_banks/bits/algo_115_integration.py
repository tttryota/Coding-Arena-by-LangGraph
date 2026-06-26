from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-115-integration',
    title='ビットマスクの基本操作 の総合演習',
    unit_kind='integration',
    target_skill='ビットマスクの基本操作 の総合演習',
    concept_overview='ビットマスクの基本操作は、複数の bit をまとめて切り替える形にも拡張できます。区間から mask を作って set と clear を行い、最後に個別 bit を判定する流れで理解をまとめます。',
    problem_bank=[
        problem(
            problem_id='algo-115-integration-p1',
            title='ビットマスクの基本操作 の総合演習 / 区間 set, 区間 clear, 1 点 test を処理する',
            problem_statement='非負整数 X と Q 個の操作が与えられる。`1 l r` は l bit から r bit までをすべて立てる、`2 l r` は l bit から r bit までをすべて下ろす、`3 k` は k bit が立っていれば 1、そうでなければ 0 を出力せよ。',
            input_format='1 行目に X Q。\n続く Q 行に操作。',
            output_format='type=3 のたびに答えを 1 行ずつ出力する。',
            constraints='0 <= X < 2^60\n1 <= Q <= 2 * 10^5\n0 <= l <= r < 60\n0 <= k < 60',
            examples=[{'input': '0 5\n1 1 3\n3 2\n2 2 4\n3 3\n3 1', 'output': '1\n0\n1'}],
            canonical_reference_solution="def range_mask(l: int, r: int) -> int:\n    width = r - l + 1\n    return ((1 << width) - 1) << l\n\ndef solve() -> None:\n    x, q = map(int, input().split())\n    out = []\n    for _ in range(q):\n        query = list(map(int, input().split()))\n        t = query[0]\n        if t == 3:\n            k = query[1]\n            out.append(str((x >> k) & 1))\n            continue\n        l, r = query[1], query[2]\n        mask = range_mask(l, r)\n        if t == 1:\n            x |= mask\n        else:\n            x &= ~mask\n    print('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
