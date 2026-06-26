from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-077-integration',
    title='部分文字列の列挙 の総合演習',
    unit_kind='integration',
    target_skill='部分文字列の列挙 の総合演習',
    concept_overview='部分文字列の列挙で全区間を生成できると、集合による重複除去だけでなく、辞書で出現回数も集計できます。ここでは「何を数えるか」と「同じ部分文字列をどうまとめるか」を合わせて扱います。',
    problem_bank=[
        problem(
            problem_id='algo-077-integration-p1',
            title='部分文字列の列挙 の総合演習 / 2 回以上現れる部分文字列のうち最長のものを求める',
            problem_statement='文字列 S が与えられる。S の部分文字列のうち、出現位置が 2 か所以上あるものの中で最長のものを求めよ。最長のものが複数あるときは、辞書順で最も小さいものを出力せよ。そのような部分文字列が存在しないときは `-` を出力せよ。',
            input_format='1 行目に S。',
            output_format='条件を満たす部分文字列を 1 行で出力する。',
            constraints='1 <= |S| <= 200',
            examples=[{'input': 'banana', 'output': 'ana'}],
            canonical_reference_solution="def solve() -> None:\n    s = input().strip()\n    freq = {}\n    n = len(s)\n    for left in range(n):\n        for right in range(left + 1, n + 1):\n            sub = s[left:right]\n            freq[sub] = freq.get(sub, 0) + 1\n\n    answer = ''\n    for sub, count in freq.items():\n        if count < 2:\n            continue\n        if len(sub) > len(answer) or (len(sub) == len(answer) and sub < answer):\n            answer = sub\n\n    print(answer if answer else '-')\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
