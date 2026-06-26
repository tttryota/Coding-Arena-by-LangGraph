from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-072-basic',
    title='トライ木 の基本',
    unit_kind='foundation',
    target_skill='トライ木 の基本',
    concept_overview='トライ木は、文字を 1 文字ずつ辺としてたどり、共通する接頭辞を木の上で共有する知識です。まずは単語を順に挿入し、接頭辞ごとの通過回数を数える基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-072-basic-p1',
            title='トライ木 の基本 / その接頭辞を持つ単語数を求める',
            problem_statement='N 個の単語と Q 個の接頭辞が与えられる。各接頭辞について、その接頭辞を持つ単語数を求めよ。',
            input_format='1 行目に N Q。\n続く N 行に単語。\n続く Q 行に接頭辞。',
            output_format='各接頭辞ごとに単語数を 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n文字列は英小文字',
            examples=[{'input': '3 2\napple\napp\nbanana\napp\nba', 'output': '2\n1'}],
            canonical_reference_solution="class Node:\n    __slots__ = ('children', 'count')\n    def __init__(self) -> None:\n        self.children = {}\n        self.count = 0\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    root = Node()\n    for _ in range(n):\n        word = input().strip()\n        node = root\n        for ch in word:\n            node = node.children.setdefault(ch, Node())\n            node.count += 1\n    out = []\n    for _ in range(q):\n        prefix = input().strip()\n        node = root\n        ok = True\n        for ch in prefix:\n            if ch not in node.children:\n                ok = False\n                break\n            node = node.children[ch]\n        out.append(str(node.count if ok else 0))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
