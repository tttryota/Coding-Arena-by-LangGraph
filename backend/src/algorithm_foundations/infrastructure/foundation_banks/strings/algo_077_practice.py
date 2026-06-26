from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-077-practice',
    title='部分文字列の列挙 を素直に実装する',
    unit_kind='foundation',
    target_skill='部分文字列の列挙 を素直に実装する',
    concept_overview='部分文字列の列挙では、同じ区間生成を使っても集計先を変えると見える情報が変わります。ここでは異なる部分文字列を長さごとに集計し、区間生成と長さ別状態管理を結び付けます。',
    problem_bank=[
        problem(
            problem_id='algo-077-practice-p1',
            title='部分文字列の列挙 を素直に実装する / 長さごとの異なる部分文字列数を求める',
            problem_statement='文字列 S が与えられる。各長さ L = 1, 2, ..., |S| について、長さ L の異なる部分文字列の個数を求めよ。',
            input_format='1 行目に S。',
            output_format='1 行目から順に、長さ 1, 2, ..., |S| の答えを 1 行ずつ出力する。',
            constraints='1 <= |S| <= 2000',
            examples=[{'input': 'aba', 'output': '2\n2\n1'}],
            canonical_reference_solution="MOD1 = 1_000_000_007\nMOD2 = 1_000_000_009\nBASE = 911382323\n\n\ndef solve() -> None:\n    s = input().strip()\n    n = len(s)\n    pow1 = [1] * (n + 1)\n    pow2 = [1] * (n + 1)\n    pref1 = [0] * (n + 1)\n    pref2 = [0] * (n + 1)\n    for i, ch in enumerate(s, start=1):\n        code = ord(ch)\n        pow1[i] = pow1[i - 1] * BASE % MOD1\n        pow2[i] = pow2[i - 1] * BASE % MOD2\n        pref1[i] = (pref1[i - 1] * BASE + code) % MOD1\n        pref2[i] = (pref2[i - 1] * BASE + code) % MOD2\n\n    def get_hash(left: int, right: int) -> tuple[int, int]:\n        h1 = (pref1[right] - pref1[left] * pow1[right - left]) % MOD1\n        h2 = (pref2[right] - pref2[left] * pow2[right - left]) % MOD2\n        return (h1, h2)\n\n    buckets = [set() for _ in range(n + 1)]\n    for left in range(n):\n        for right in range(left + 1, n + 1):\n            buckets[right - left].add(get_hash(left, right))\n    for length in range(1, n + 1):\n        print(len(buckets[length]))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
