from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-087-practice',
    title='包除原理 を素直に実装する',
    unit_kind='foundation',
    target_skill='包除原理 を素直に実装する',
    concept_overview='2 集合の包除が分かったら、3 集合では pairwise の共通部分を引き、3 者共通を足し戻します。lcm を重ねて重複補正を広げる形を確認します。',
    problem_bank=[
        problem(
            problem_id='algo-087-practice-p1',
            title='包除原理 を素直に実装する / 1 以上 N 以下で A, B, C のいずれかの倍数である個数を求める',
            problem_statement='整数 N, A, B, C が与えられる。1 以上 N 以下で A, B, C のいずれかの倍数である整数の個数を求めよ。',
            input_format='1 行目に N A B C。',
            output_format='条件を満たす個数を出力する。',
            constraints='1 <= N, A, B, C <= 10^18',
            examples=[{'input': '30 4 6 10', 'output': '11'}],
            canonical_reference_solution="from math import gcd\n\n\ndef lcm(a: int, b: int) -> int:\n    return a // gcd(a, b) * b\n\n\ndef solve() -> None:\n    n, a, b, c = map(int, input().split())\n    ab = lcm(a, b)\n    ac = lcm(a, c)\n    bc = lcm(b, c)\n    abc = lcm(ab, c)\n    ans = n // a + n // b + n // c\n    ans -= n // ab + n // ac + n // bc\n    ans += n // abc\n    print(ans)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
