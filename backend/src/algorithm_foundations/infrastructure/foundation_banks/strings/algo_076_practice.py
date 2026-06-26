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
    concept_overview='Aho-Corasick法では、トライ木に失敗遷移を張って「次にどこへ戻るか」を前計算します。ここでは各状態に終端パターンの番号を持たせ、本文 1 回の走査からパターンごとの出現回数へ配り分ける状態管理を確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-076-practice-p1',
            title='Aho-Corasick法 を素直に実装する / すべてのパターンについて、S の中での出現回数を求める',
            problem_statement='文字列 S と N 個のパターン P_i が与えられる。すべてのパターンについて、S の中での出現回数を求めよ。',
            input_format='1 行目に S。\n2 行目に N。\n続く N 行に P_i。',
            output_format='各パターンの出現回数を 1 行ずつ出力する。',
            constraints='1 <= |S| <= 2 * 10^5\n1 <= N <= 2 * 10^5\n各 P_i は空でない英小文字列\nパターン長の総和は 2 * 10^5 以下',
            examples=[{'input': 'abracadabra\n3\nabra\nra\na', 'output': '2\n2\n5'}],
            canonical_reference_solution="from collections import deque\n\nclass Node:\n    def __init__(self) -> None:\n        self.next = {}\n        self.fail = 0\n        self.out = []\n\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n\n    s = input().strip()\n    n = int(input())\n    trie = [Node()]\n\n    for idx in range(n):\n        pat = input().strip()\n        node = 0\n        for ch in pat:\n            nxt = trie[node].next.get(ch)\n            if nxt is None:\n                nxt = len(trie)\n                trie[node].next[ch] = nxt\n                trie.append(Node())\n            node = nxt\n        trie[node].out.append(idx)\n\n    order = []\n    dq = deque(trie[0].next.values())\n    while dq:\n        v = dq.popleft()\n        order.append(v)\n        for ch, nxt in trie[v].next.items():\n            f = trie[v].fail\n            while f and ch not in trie[f].next:\n                f = trie[f].fail\n            trie[nxt].fail = trie[f].next[ch] if ch in trie[f].next else 0\n            dq.append(nxt)\n\n    visits = [0] * len(trie)\n    node = 0\n    for ch in s:\n        while node and ch not in trie[node].next:\n            node = trie[node].fail\n        if ch in trie[node].next:\n            node = trie[node].next[ch]\n        visits[node] += 1\n\n    for v in reversed(order):\n        visits[trie[v].fail] += visits[v]\n\n    ans = [0] * n\n    for node_id, entry in enumerate(trie):\n        for idx in entry.out:\n            ans[idx] = visits[node_id]\n    print(*ans, sep='\\n')\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
