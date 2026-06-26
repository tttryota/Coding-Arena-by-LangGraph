from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-073-practice',
    title='Suffix Array を素直に実装する',
    unit_kind='foundation',
    target_skill='Suffix Array を素直に実装する',
    concept_overview='Suffix Array で接尾辞を辞書順に並べると、似ている接尾辞どうしは隣り合います。ここでは並べたあとに隣接 suffix の共通接頭辞を調べ、最長の繰り返し部分文字列へ結びつける見方を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-073-practice-p1',
            title='Suffix Array を素直に実装する / 最長の繰り返し部分文字列の長さを求める',
            problem_statement='文字列 S が与えられる。S に 2 回以上現れる部分文字列のうち、最長のものの長さを求めよ。出現位置は重なっていてもよい。',
            input_format='1 行目に S。',
            output_format='答えを出力する。',
            constraints='1 <= |S| <= 2000',
            examples=[{'input': 'banana', 'output': '3'}],
            canonical_reference_solution="def lcp_length(a: str, b: str) -> int:\n    length = 0\n    limit = min(len(a), len(b))\n    while length < limit and a[length] == b[length]:\n        length += 1\n    return length\n\n\ndef solve() -> None:\n    s = input().strip()\n    suffixes = sorted(s[i:] for i in range(len(s)))\n    ans = 0\n    for i in range(len(suffixes) - 1):\n        ans = max(ans, lcp_length(suffixes[i], suffixes[i + 1]))\n    print(ans)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
