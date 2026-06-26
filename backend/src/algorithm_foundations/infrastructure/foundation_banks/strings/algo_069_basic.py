from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-069-basic',
    title='文字列のハッシュ（ローリングハッシュ） の基本',
    unit_kind='foundation',
    target_skill='文字列のハッシュ（ローリングハッシュ） の基本',
    concept_overview='ローリングハッシュは、文字列を左から順に数値へ写し、接頭辞の情報から部分文字列のハッシュ値をすばやく取り出す知識です。まずは任意の 2 つの部分文字列が等しいかを高速に判定する基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-069-basic-p1',
            title='文字列のハッシュ（ローリングハッシュ） の基本 / 2 つの部分文字列が等しいかを判定する',
            problem_statement='文字列 S と Q 個の問い合わせが与えられる。各問い合わせでは 2 つの区間 [l1, r1], [l2, r2] が与えられるので、対応する部分文字列が等しければ Yes、そうでなければ No を出力せよ。',
            input_format='1 行目に S。\n2 行目に Q。\n続く Q 行に l1 r1 l2 r2。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='1 <= |S| <= 2 * 10^5\n1 <= Q <= 2 * 10^5\n1 <= l1 <= r1 <= |S|\n1 <= l2 <= r2 <= |S|',
            examples=[{'input': 'abacaba\n3\n1 3 5 7\n1 2 2 3\n3 4 6 7', 'output': 'Yes\nNo\nNo'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    s = input().strip()\n    q = int(input())\n    n = len(s)\n    base1, mod1 = 911382323, 972663749\n    base2, mod2 = 97266353, 1000000007\n    power1 = [1] * (n + 1)\n    power2 = [1] * (n + 1)\n    prefix1 = [0] * (n + 1)\n    prefix2 = [0] * (n + 1)\n    for i, ch in enumerate(s, start=1):\n        code = ord(ch)\n        power1[i] = power1[i - 1] * base1 % mod1\n        power2[i] = power2[i - 1] * base2 % mod2\n        prefix1[i] = (prefix1[i - 1] * base1 + code) % mod1\n        prefix2[i] = (prefix2[i - 1] * base2 + code) % mod2\n\n    def get_hash(left: int, right: int) -> tuple[int, int]:\n        h1 = (prefix1[right] - prefix1[left - 1] * power1[right - left + 1]) % mod1\n        h2 = (prefix2[right] - prefix2[left - 1] * power2[right - left + 1]) % mod2\n        return h1, h2\n\n    out = []\n    for _ in range(q):\n        l1, r1, l2, r2 = map(int, input().split())\n        if r1 - l1 != r2 - l2:\n            out.append('No')\n            continue\n        out.append('Yes' if get_hash(l1, r1) == get_hash(l2, r2) else 'No')\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
