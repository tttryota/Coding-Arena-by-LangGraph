from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-058-practice',
    title='辞書順最小の構成 を素直に実装する',
    unit_kind='foundation',
    target_skill='辞書順最小の構成 を素直に実装する',
    concept_overview='2 文字列の比較規則が分かれば、それを比較関数として全体を並べ替えられます。ここでは N 個の文字列を実際に整列し、辞書順最小の連結結果を構成します。',
    problem_bank=[
        problem(
            problem_id='algo-058-practice-p1',
            title='辞書順最小の構成 を素直に実装する / N 個の文字列を並べて最小連結文字列を作る',
            problem_statement='N 個の文字列 S_i が与えられる。並べる順番を自由に選んで連結するとき、得られる文字列が辞書順で最小になるようにせよ。その最小の文字列を出力する。',
            input_format='1 行目に N。\n続く N 行に S_i。',
            output_format='辞書順最小の連結結果を出力する。',
            constraints='1 <= N <= 2 * 10^5\n各 S_i は英小文字からなる\n文字列長の総和は 2 * 10^5 以下',
            examples=[{'input': '3\nba\nb\nab', 'output': 'abbab'}],
            canonical_reference_solution="from functools import cmp_to_key\n\n\ndef cmp(a: str, b: str) -> int:\n    if a + b < b + a:\n        return -1\n    if a + b > b + a:\n        return 1\n    return 0\n\n\ndef solve() -> None:\n    n = int(input())\n    strings = [input().strip() for _ in range(n)]\n    strings.sort(key=cmp_to_key(cmp))\n    print(''.join(strings))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
