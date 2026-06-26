from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-076-practice',
    title='Aho-Corasick法 を素直に実装する',
    unit_kind='foundation',
    target_skill='Aho-Corasick法 を素直に実装する',
    concept_overview='文字列処理は、文字の並びを比較したり、部分文字列を見つけたり、規則性を前計算で利用したりする知識です。並びをそのまま走査して構造をつかむ基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-076-practice-p1',
            title='Aho-Corasick法 を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='文字列 S と N 個のパターン P_i が与えられる。 すべてのパターンについて、S の中での出現回数を求めよ。',
            input_format='1 行目に S。\n2 行目に N。\n続く N 行に P_i。',
            output_format='各パターンの出現回数を 1 行ずつ出力する。',
            constraints='1 <= |S| <= 2 * 10^5\n1 <= N <= 2 * 10^5\n各 P_i は英小文字',
            examples=[
                {
                    'input': 'abracadabra\n3\nabra\nra\na',
                    'output': '2\n2\n5',
                },
            ],
            canonical_reference_solution="from collections import deque\n\nclass Node:\n    def __init__(self) -> None:\n        self.next = {}\n        self.fail = 0\n        self.out = []\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    s = input().strip()\n    n = int(input())\n    trie = [Node()]\n    pats = []\n    for idx in range(n):\n        pat = input().strip()\n        pats.append(pat)\n        node = 0\n        for ch in pat:\n            node = trie[node].next.setdefault(ch, len(trie))\n            if node == len(trie):\n                trie.append(Node())\n        trie[node].out.append(idx)\n    dq = deque()\n    for ch, nxt in trie[0].next.items():\n        dq.append(nxt)\n    while dq:\n        v = dq.popleft()\n        for ch, nxt in trie[v].next.items():\n            f = trie[v].fail\n            while f and ch not in trie[f].next:\n                f = trie[f].fail\n            trie[nxt].fail = trie[f].next[ch] if ch in trie[f].next else 0\n            trie[nxt].out.extend(trie[trie[nxt].fail].out)\n            dq.append(nxt)\n    ans = [0] * n\n    node = 0\n    for ch in s:\n        while node and ch not in trie[node].next:\n            node = trie[node].fail\n        if ch in trie[node].next:\n            node = trie[node].next[ch]\n        for idx in trie[node].out:\n            ans[idx] += 1\n    print(*ans, sep='\\n')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-076-practice-p2',
            title='Aho-Corasick法 を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、文字列 S と N 個のパターン P_i が与えられる。 すべてのパターンについて、S の中での出現回数を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に S。\n2 行目に N。\n続く N 行に P_i。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= |S| <= 2 * 10^5\n1 <= N <= 2 * 10^5\n各 P_i は英小文字\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\nabracadabra\n3\nabra\nra\na\nabracadabra\n3\nabra\nra\na',
                    'output': '2\n2\n5\n2\n2\n5',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom collections import deque\n\nclass Node:\n    def __init__(self) -> None:\n        self.next = {}\n        self.fail = 0\n        self.out = []\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    s = input().strip()\n    n = int(input())\n    trie = [Node()]\n    pats = []\n    for idx in range(n):\n        pat = input().strip()\n        pats.append(pat)\n        node = 0\n        for ch in pat:\n            node = trie[node].next.setdefault(ch, len(trie))\n            if node == len(trie):\n                trie.append(Node())\n        trie[node].out.append(idx)\n    dq = deque()\n    for ch, nxt in trie[0].next.items():\n        dq.append(nxt)\n    while dq:\n        v = dq.popleft()\n        for ch, nxt in trie[v].next.items():\n            f = trie[v].fail\n            while f and ch not in trie[f].next:\n                f = trie[f].fail\n            trie[nxt].fail = trie[f].next[ch] if ch in trie[f].next else 0\n            trie[nxt].out.extend(trie[trie[nxt].fail].out)\n            dq.append(nxt)\n    ans = [0] * n\n    node = 0\n    for ch in s:\n        while node and ch not in trie[node].next:\n            node = trie[node].fail\n        if ch in trie[node].next:\n            node = trie[node].next[ch]\n        for idx in trie[node].out:\n            ans[idx] += 1\n    print(*ans, sep='\\n')\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-076-practice-p3',
            title='Aho-Corasick法 を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、文字列 S と N 個のパターン P_i が与えられる。 すべてのパターンについて、S の中での出現回数を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に S。\n2 行目に N。\n続く N 行に P_i。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= |S| <= 2 * 10^5\n1 <= N <= 2 * 10^5\n各 P_i は英小文字\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\nabracadabra\n3\nabra\nra\na\nabracadabra\n3\nabra\nra\na\nabracadabra\n3\nabra\nra\na',
                    'output': '2\n2\n5\n2\n2\n5\n2\n2\n5',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom collections import deque\n\nclass Node:\n    def __init__(self) -> None:\n        self.next = {}\n        self.fail = 0\n        self.out = []\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    s = input().strip()\n    n = int(input())\n    trie = [Node()]\n    pats = []\n    for idx in range(n):\n        pat = input().strip()\n        pats.append(pat)\n        node = 0\n        for ch in pat:\n            node = trie[node].next.setdefault(ch, len(trie))\n            if node == len(trie):\n                trie.append(Node())\n        trie[node].out.append(idx)\n    dq = deque()\n    for ch, nxt in trie[0].next.items():\n        dq.append(nxt)\n    while dq:\n        v = dq.popleft()\n        for ch, nxt in trie[v].next.items():\n            f = trie[v].fail\n            while f and ch not in trie[f].next:\n                f = trie[f].fail\n            trie[nxt].fail = trie[f].next[ch] if ch in trie[f].next else 0\n            trie[nxt].out.extend(trie[trie[nxt].fail].out)\n            dq.append(nxt)\n    ans = [0] * n\n    node = 0\n    for ch in s:\n        while node and ch not in trie[node].next:\n            node = trie[node].fail\n        if ch in trie[node].next:\n            node = trie[node].next[ch]\n        for idx in trie[node].out:\n            ans[idx] += 1\n    print(*ans, sep='\\n')\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
