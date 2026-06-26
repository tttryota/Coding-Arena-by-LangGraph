from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-077-basic',
    title='部分文字列の列挙 の基本',
    unit_kind='foundation',
    target_skill='部分文字列の列挙 の基本',
    concept_overview='部分文字列の列挙は、開始位置と終了位置を動かして文字列のすべての区間を取り出す知識です。まずは全区間を集合へ入れ、異なる部分文字列の総数だけを求める最も素直な使い方を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-077-basic-p1',
            title='部分文字列の列挙 の基本 / 異なる部分文字列の個数を求める',
            problem_statement='文字列 S が与えられる。異なる部分文字列の個数を求めよ。',
            input_format='1 行目に S。',
            output_format='異なる部分文字列の個数を出力する。',
            constraints='1 <= |S| <= 2000',
            examples=[{'input': 'aba', 'output': '5'}],
            canonical_reference_solution="MOD1 = 1_000_000_007\nMOD2 = 1_000_000_009\nBASE = 911382323\n\n\ndef solve() -> None:\n    s = input().strip()\n    n = len(s)\n    pow1 = [1] * (n + 1)\n    pow2 = [1] * (n + 1)\n    pref1 = [0] * (n + 1)\n    pref2 = [0] * (n + 1)\n    for i, ch in enumerate(s, start=1):\n        code = ord(ch)\n        pow1[i] = pow1[i - 1] * BASE % MOD1\n        pow2[i] = pow2[i - 1] * BASE % MOD2\n        pref1[i] = (pref1[i - 1] * BASE + code) % MOD1\n        pref2[i] = (pref2[i - 1] * BASE + code) % MOD2\n\n    def get_hash(left: int, right: int) -> tuple[int, int, int]:\n        h1 = (pref1[right] - pref1[left] * pow1[right - left]) % MOD1\n        h2 = (pref2[right] - pref2[left] * pow2[right - left]) % MOD2\n        return (right - left, h1, h2)\n\n    seen = set()\n    for left in range(n):\n        for right in range(left + 1, n + 1):\n            seen.add(get_hash(left, right))\n    print(len(seen))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
