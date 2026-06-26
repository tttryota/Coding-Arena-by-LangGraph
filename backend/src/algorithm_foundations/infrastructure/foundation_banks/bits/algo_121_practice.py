from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-121-practice',
    title='最下位ビット（LSB）の取得 を素直に実装する',
    unit_kind='foundation',
    target_skill='最下位ビット（LSB）の取得 を素直に実装する',
    concept_overview='LSB の取得では、2 の補数を使うと最下位の立っている bit だけを残せます。1 回だけ値を取るのではなく、LSB を順に抜き出して状態を更新しながら全ての立っている bit を低い順に列挙する流れを確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-121-practice-p1',
            title='最下位ビット（LSB）の取得 を素直に実装する / 立っているビットを低い順に列挙せよ',
            problem_statement='非負整数 X が与えられる。LSB を繰り返し取り出して X から削除し、立っている bit の値を低い順にすべて出力せよ。X=0 のときは 0 を出力する。',
            input_format='1 行目に X。',
            output_format='立っている bit の値を空白区切りで出力する。X=0 のときは 0 を出力する。',
            constraints='0 <= X < 2^60',
            examples=[{'input': '44', 'output': '4 8 32'}],
            canonical_reference_solution="def solve() -> None:\n    x = int(input())\n    if x == 0:\n        print(0)\n        return\n    parts = []\n    while x:\n        lsb = x & -x\n        parts.append(str(lsb))\n        x -= lsb\n    print(*parts)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
