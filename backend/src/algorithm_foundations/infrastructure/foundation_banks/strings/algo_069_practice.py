from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-069-practice',
    title='文字列のハッシュ（ローリングハッシュ） を素直に実装する',
    unit_kind='foundation',
    target_skill='文字列のハッシュ（ローリングハッシュ） を素直に実装する',
    concept_overview='ローリングハッシュでは、任意区間の等値判定を何度も高速に行えるので、部分文字列の一致長も二分探索つきで求められます。ここでは 2 つの接尾辞の最長共通接頭辞を求めます。',
    problem_bank=[
        problem(
            problem_id='algo-069-practice-p1',
            title='文字列のハッシュ（ローリングハッシュ） を素直に実装する / 2 つの接尾辞の最長共通接頭辞を求める',
            problem_statement='文字列 S と Q 個の問い合わせが与えられる。各問い合わせでは開始位置 a, b が与えられるので、接尾辞 S[a..] と S[b..] の最長共通接頭辞の長さを求めよ。',
            input_format='1 行目に S。\n2 行目に Q。\n続く Q 行に a b。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='1 <= |S| <= 2 * 10^5\n1 <= Q <= 2 * 10^5\n1 <= a, b <= |S|',
            examples=[{'input': 'abacaba\n3\n1 5\n2 4\n3 7', 'output': '3\n0\n1'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n\n    input = sys.stdin.readline\n    s = input().strip()\n    q = int(input())\n    n = len(s)\n    base1, mod1 = 911382323, 972663749\n    base2, mod2 = 97266353, 1000000007\n    power1 = [1] * (n + 1)\n    power2 = [1] * (n + 1)\n    prefix1 = [0] * (n + 1)\n    prefix2 = [0] * (n + 1)\n    for i, ch in enumerate(s, start=1):\n        code = ord(ch)\n        power1[i] = power1[i - 1] * base1 % mod1\n        power2[i] = power2[i - 1] * base2 % mod2\n        prefix1[i] = (prefix1[i - 1] * base1 + code) % mod1\n        prefix2[i] = (prefix2[i - 1] * base2 + code) % mod2\n\n    def get_hash(left: int, right: int) -> tuple[int, int]:\n        h1 = (prefix1[right] - prefix1[left - 1] * power1[right - left + 1]) % mod1\n        h2 = (prefix2[right] - prefix2[left - 1] * power2[right - left + 1]) % mod2\n        return h1, h2\n\n    out = []\n    for _ in range(q):\n        a, b = map(int, input().split())\n        limit = n - max(a, b) + 1\n        low, high = 0, limit\n        while low < high:\n            mid = (low + high + 1) // 2\n            if get_hash(a, a + mid - 1) == get_hash(b, b + mid - 1):\n                low = mid\n            else:\n                high = mid - 1\n        out.append(str(low))\n    sys.stdout.write('\\n'.join(out))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
