from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-076-basic',
    title='Aho-Corasick法 の基本',
    unit_kind='foundation',
    target_skill='Aho-Corasick法 の基本',
    concept_overview='Aho-Corasick法は、複数のパターンを 1 本のトライ木にまとめ、失敗遷移を使って本文を 1 回走査する知識です。まずは各状態に「ここで何個のパターンが終わるか」だけを持たせ、全一致数をまとめて数える最も素直な使い方を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-076-basic-p1',
            title='Aho-Corasick法 の基本 / すべてのパターンの総出現回数を求める',
            problem_statement='文字列 S と N 個のパターン P_i が与えられる。S の中に現れるパターンの出現回数の総和を求めよ。同じ位置で複数のパターンが終わるなら、その個数ぶん数える。',
            input_format='1 行目に S。\n2 行目に N。\n続く N 行に P_i。',
            output_format='総出現回数を 1 行で出力する。',
            constraints='1 <= |S| <= 2 * 10^5\n1 <= N <= 2 * 10^5\n各 P_i は空でない英小文字列\nパターン長の総和は 2 * 10^5 以下',
            examples=[{'input': 'abracadabra\n3\nabra\nra\na', 'output': '9'}],
            canonical_reference_solution="from collections import deque\n\nclass Node:\n    def __init__(self) -> None:\n        self.next = {}\n        self.fail = 0\n        self.out_count = 0\n\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n\n    s = input().strip()\n    n = int(input())\n    trie = [Node()]\n\n    for _ in range(n):\n        pat = input().strip()\n        node = 0\n        for ch in pat:\n            nxt = trie[node].next.get(ch)\n            if nxt is None:\n                nxt = len(trie)\n                trie[node].next[ch] = nxt\n                trie.append(Node())\n            node = nxt\n        trie[node].out_count += 1\n\n    dq = deque(trie[0].next.values())\n    while dq:\n        v = dq.popleft()\n        for ch, nxt in trie[v].next.items():\n            f = trie[v].fail\n            while f and ch not in trie[f].next:\n                f = trie[f].fail\n            trie[nxt].fail = trie[f].next[ch] if ch in trie[f].next else 0\n            trie[nxt].out_count += trie[trie[nxt].fail].out_count\n            dq.append(nxt)\n\n    ans = 0\n    node = 0\n    for ch in s:\n        while node and ch not in trie[node].next:\n            node = trie[node].fail\n        if ch in trie[node].next:\n            node = trie[node].next[ch]\n        ans += trie[node].out_count\n    print(ans)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
