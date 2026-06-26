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
    concept_overview='文字列処理は、文字の並びを比較したり、部分文字列を見つけたり、規則性を前計算で利用したりする知識です。並びをそのまま走査して構造をつかむ基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-072-basic-p1',
            title='トライ木 の基本 / 1 ケースをそのまま解く',
            problem_statement='N 個の単語と Q 個の接頭辞が与えられる。各接頭辞について、その接頭辞を持つ単語数を求めよ。',
            input_format='1 行目に N Q。\n続く N 行に単語。\n続く Q 行に接頭辞。',
            output_format='各接頭辞ごとに単語数を 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n文字列は英小文字',
            examples=[
                {
                    'input': '3 2\napple\napp\nbanana\napp\nba',
                    'output': '2\n1',
                },
            ],
            canonical_reference_solution="class Node:\n    __slots__ = ('children', 'count')\n    def __init__(self) -> None:\n        self.children = {}\n        self.count = 0\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    root = Node()\n    for _ in range(n):\n        word = input().strip()\n        node = root\n        for ch in word:\n            node = node.children.setdefault(ch, Node())\n            node.count += 1\n    out = []\n    for _ in range(q):\n        prefix = input().strip()\n        node = root\n        ok = True\n        for ch in prefix:\n            if ch not in node.children:\n                ok = False\n                break\n            node = node.children[ch]\n        out.append(str(node.count if ok else 0))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-072-basic-p2',
            title='トライ木 の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、N 個の単語と Q 個の接頭辞が与えられる。各接頭辞について、その接頭辞を持つ単語数を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N Q。\n続く N 行に単語。\n続く Q 行に接頭辞。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n文字列は英小文字\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n3 2\napple\napp\nbanana\napp\nba\n3 2\napple\napp\nbanana\napp\nba',
                    'output': '2\n1\n2\n1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nclass Node:\n    __slots__ = ('children', 'count')\n    def __init__(self) -> None:\n        self.children = {}\n        self.count = 0\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    root = Node()\n    for _ in range(n):\n        word = input().strip()\n        node = root\n        for ch in word:\n            node = node.children.setdefault(ch, Node())\n            node.count += 1\n    out = []\n    for _ in range(q):\n        prefix = input().strip()\n        node = root\n        ok = True\n        for ch in prefix:\n            if ch not in node.children:\n                ok = False\n                break\n            node = node.children[ch]\n        out.append(str(node.count if ok else 0))\n    sys.stdout.write('\\n'.join(out))\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-072-basic-p3',
            title='トライ木 の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、N 個の単語と Q 個の接頭辞が与えられる。各接頭辞について、その接頭辞を持つ単語数を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N Q。\n続く N 行に単語。\n続く Q 行に接頭辞。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n文字列は英小文字\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n3 2\napple\napp\nbanana\napp\nba\n3 2\napple\napp\nbanana\napp\nba\n3 2\napple\napp\nbanana\napp\nba',
                    'output': '2\n1\n2\n1\n2\n1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nclass Node:\n    __slots__ = ('children', 'count')\n    def __init__(self) -> None:\n        self.children = {}\n        self.count = 0\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    root = Node()\n    for _ in range(n):\n        word = input().strip()\n        node = root\n        for ch in word:\n            node = node.children.setdefault(ch, Node())\n            node.count += 1\n    out = []\n    for _ in range(q):\n        prefix = input().strip()\n        node = root\n        ok = True\n        for ch in prefix:\n            if ch not in node.children:\n                ok = False\n                break\n            node = node.children[ch]\n        out.append(str(node.count if ok else 0))\n    sys.stdout.write('\\n'.join(out))\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
