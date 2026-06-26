from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-075-integration',
    title='ランレングス圧縮 の総合演習',
    unit_kind='integration',
    target_skill='ランレングス圧縮 の総合演習',
    concept_overview='ランレングス圧縮で文字列を run の列へ直すと、1 文字削除のような操作も run 単位で場合分けできます。ここでは各 run の長さと隣接 run の文字を見て、削除後の run 数がどう変わるかを整理する軽い総合問題を扱います。',
    problem_bank=[
        problem(
            problem_id='algo-075-integration-p1',
            title='ランレングス圧縮 の総合演習 / 1 文字削除後の run 数の最小値を求める',
            problem_statement='文字列 S からちょうど 1 文字削除する。削除後の文字列をランレングス圧縮したときの run 数の最小値を求めよ。run 数とは、同じ文字が連続する区間の個数である。',
            input_format='1 行目に S。',
            output_format='最小の run 数を出力する。',
            constraints='1 <= |S| <= 2 * 10^5',
            examples=[{'input': 'aabaa', 'output': '1'}],
            canonical_reference_solution="def solve() -> None:\n    s = input().strip()\n    runs = []\n    i = 0\n    while i < len(s):\n        j = i\n        while j < len(s) and s[j] == s[i]:\n            j += 1\n        runs.append((s[i], j - i))\n        i = j\n\n    m = len(runs)\n    if len(s) == 1:\n        print(0)\n        return\n\n    ans = m\n    for idx, (ch, length) in enumerate(runs):\n        if length >= 2:\n            continue\n        if 0 < idx < m - 1 and runs[idx - 1][0] == runs[idx + 1][0]:\n            ans = min(ans, m - 2)\n        else:\n            ans = min(ans, m - 1)\n    print(ans)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
