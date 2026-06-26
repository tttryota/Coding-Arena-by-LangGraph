from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-070-practice',
    title='KMP法 を素直に実装する',
    unit_kind='foundation',
    target_skill='KMP法 を素直に実装する',
    concept_overview='KMP 法では、prefix function を使って、検索中に不一致が起きたときも一致していた長さを巻き戻して再利用できます。ここでは S を左から読んだ各時点で、T の接頭辞がどこまで一致しているかを追跡します。',
    problem_bank=[
        problem(
            problem_id='algo-070-practice-p1',
            title='KMP法 を素直に実装する / 各 prefix について、T の接頭辞が suffix として何文字一致するかを求める',
            problem_statement='文字列 S と T が与えられる。各 i (1 <= i <= |S|) について、S[1..i] の suffix であり、同時に T の prefix でもある文字列のうち最長の長さを求めよ。',
            input_format='1 行目に S。\n2 行目に T。',
            output_format='|S| 個の答えを空白区切りで出力する。',
            constraints='1 <= |S| <= 2 * 10^5\n1 <= |T| <= 2 * 10^5',
            examples=[{'input': 'ababacababa\nababa', 'output': '1 2 3 4 5 0 1 2 3 4 5'}],
            canonical_reference_solution="def build_lps(pattern: str) -> list[int]:\n    lps = [0] * len(pattern)\n    length = 0\n    i = 1\n    while i < len(pattern):\n        if pattern[i] == pattern[length]:\n            length += 1\n            lps[i] = length\n            i += 1\n        elif length:\n            length = lps[length - 1]\n        else:\n            i += 1\n    return lps\n\n\ndef solve() -> None:\n    s = input().strip()\n    t = input().strip()\n    lps = build_lps(t)\n    matched = 0\n    ans = []\n    for ch in s:\n        while matched > 0 and t[matched] != ch:\n            matched = lps[matched - 1]\n        if t[matched] == ch:\n            matched += 1\n        ans.append(str(matched))\n        if matched == len(t):\n            matched = lps[matched - 1]\n    print(' '.join(ans))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
