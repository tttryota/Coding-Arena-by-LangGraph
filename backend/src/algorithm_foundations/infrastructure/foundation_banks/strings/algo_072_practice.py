from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-072-practice',
    title='トライ木 を素直に実装する',
    unit_kind='foundation',
    target_skill='トライ木 を素直に実装する',
    concept_overview='トライ木では、各文字で子ノードへ進む構造は同じでも、接頭辞数を見る代わりに「そのノードで単語が終わるか」を管理することがあります。ここでは終端回数を持たせ、完全一致する単語が何回挿入されたかを返す実装を確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-072-practice-p1',
            title='トライ木 を素直に実装する / 完全一致する単語の出現回数を求める',
            problem_statement='N 個の単語を順にトライ木へ挿入する。その後 Q 個の問い合わせが与えられるので、各問い合わせ文字列と完全一致する単語が何回挿入されたかを求めよ。同じ単語が複数回与えられることがある。',
            input_format='1 行目に N Q。\n続く N 行に単語。\n続く Q 行に問い合わせ文字列。',
            output_format='各問い合わせごとに出現回数を 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n文字列は英小文字',
            examples=[{'input': '5 4\napple\napp\napple\nbanana\napp\napp\napple\nap\nbanana', 'output': '2\n2\n0\n1'}],
            canonical_reference_solution="class Node:\n    __slots__ = ('children', 'end_count')\n\n    def __init__(self) -> None:\n        self.children = {}\n        self.end_count = 0\n\n\ndef solve() -> None:\n    import sys\n\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    root = Node()\n    for _ in range(n):\n        word = input().strip()\n        node = root\n        for ch in word:\n            node = node.children.setdefault(ch, Node())\n        node.end_count += 1\n\n    out = []\n    for _ in range(q):\n        word = input().strip()\n        node = root\n        for ch in word:\n            if ch not in node.children:\n                out.append('0')\n                break\n            node = node.children[ch]\n        else:\n            out.append(str(node.end_count))\n    sys.stdout.write('\\n'.join(out))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
