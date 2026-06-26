from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-037-integration',
    title='最長増加部分列（LIS） の総合演習',
    unit_kind='integration',
    target_skill='最長増加部分列（LIS） の総合演習',
    concept_overview='LIS は左右から 2 回使うと、「どこを山の頂点にすると最長か」という問題にも広げられます。ここでは増加してから減少する最長部分列を求めます。',
    problem_bank=[
        problem(
            problem_id='algo-037-integration-p1',
            title='最長増加部分列（LIS） の総合演習 / 最長ビトニック部分列の長さを求める',
            problem_statement='長さ N の整数列 A が与えられる。ある位置を頂点として、左側では狭義増加、右側では狭義減少する部分列をビトニック部分列と呼ぶ。最長ビトニック部分列の長さを求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='最長ビトニック部分列の長さを出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[{'input': '7\n1 4 2 5 3 2 1', 'output': '6'}],
            canonical_reference_solution="from bisect import bisect_left\n\n\ndef lis_lengths(a: list[int]) -> list[int]:\n    tails = []\n    res = [0] * len(a)\n    for i, value in enumerate(a):\n        pos = bisect_left(tails, value)\n        if pos == len(tails):\n            tails.append(value)\n        else:\n            tails[pos] = value\n        res[i] = pos + 1\n    return res\n\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    _ = int(input())\n    a = list(map(int, input().split()))\n    left = lis_lengths(a)\n    right = lis_lengths(list(reversed(a)))\n    right.reverse()\n    ans = 0\n    for l, r in zip(left, right):\n        ans = max(ans, l + r - 1)\n    print(ans)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
