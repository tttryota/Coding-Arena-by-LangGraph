from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-075-practice',
    title='ランレングス圧縮 を素直に実装する',
    unit_kind='foundation',
    target_skill='ランレングス圧縮 を素直に実装する',
    concept_overview='ランレングス圧縮では、連続区間を文字と個数へ直すだけでなく、その逆に圧縮表現を読み解いて元の文字列へ戻すことも重要です。ここでは文字と、その直後に続く複数桁の個数を読み分ける状態管理を確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-075-practice-p1',
            title='ランレングス圧縮 を素直に実装する / 圧縮表現を復元する',
            problem_statement='英小文字 1 文字と正の整数を交互に並べたランレングス圧縮表現 T が与えられる。T を元の文字列へ復元して出力せよ。',
            input_format='1 行目に T。',
            output_format='復元した文字列を 1 行で出力する。',
            constraints='1 <= |T| <= 2 * 10^5\nT は英小文字 1 文字の直後に 1 以上の整数が続く並びとして妥当である\n復元後の文字列長は 2 * 10^5 以下',
            examples=[{'input': 'a3b12c1', 'output': 'aaabbbbbbbbbbbbc'}],
            canonical_reference_solution="def solve() -> None:\n    t = input().strip()\n    out = []\n    i = 0\n    while i < len(t):\n        ch = t[i]\n        i += 1\n        j = i\n        while j < len(t) and t[j].isdigit():\n            j += 1\n        count = int(t[i:j])\n        out.append(ch * count)\n        i = j\n    print(''.join(out))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
