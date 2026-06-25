"""String family templates."""

from __future__ import annotations

from .common import ProblemTemplate, array_template


def build_problem_template(  # noqa: C901
    *,
    theme_id: str,
    key: str,
    category: str,
) -> ProblemTemplate | None:
    if theme_id == "algo-074":
        return array_template(
            statement="文字列 S が与えられる。回文部分文字列の最長長さを求めよ。",
            input_format="1 行目に S。",
            output_format="最長長さを出力する。",
            constraints="1 <= |S| <= 2 * 10^5",
            examples=[{"input": "abacaba", "output": "7"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    s = input().strip()\n"
                "    t = '^#' + '#'.join(s) + '#$'\n"
                "    radius = [0] * len(t)\n"
                "    center = right = 0\n"
                "    ans = 0\n"
                "    for i in range(1, len(t) - 1):\n"
                "        mirror = 2 * center - i\n"
                "        if i < right:\n"
                "            radius[i] = min(right - i, radius[mirror])\n"
                "        while t[i + radius[i] + 1] == t[i - radius[i] - 1]:\n"
                "            radius[i] += 1\n"
                "        if i + radius[i] > right:\n"
                "            center = i\n"
                "            right = i + radius[i]\n"
                "        ans = max(ans, radius[i])\n"
                "    print(ans)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-076":
        return array_template(
            statement=(
                "文字列 S と N 個のパターン P_i が与えられる。"
                " すべてのパターンについて、S の中での出現回数を求めよ。"
            ),
            input_format="1 行目に S。\n2 行目に N。\n続く N 行に P_i。",
            output_format="各パターンの出現回数を 1 行ずつ出力する。",
            constraints="1 <= |S| <= 2 * 10^5\n1 <= N <= 2 * 10^5\n各 P_i は英小文字",
            examples=[{"input": "abracadabra\n3\nabra\nra\na", "output": "2\n2\n5"}],
            reference_solution=(
                "from collections import deque\n\n"
                "class Node:\n"
                "    def __init__(self) -> None:\n"
                "        self.next = {}\n"
                "        self.fail = 0\n"
                "        self.out = []\n\n"
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    s = input().strip()\n"
                "    n = int(input())\n"
                "    trie = [Node()]\n"
                "    pats = []\n"
                "    for idx in range(n):\n"
                "        pat = input().strip()\n"
                "        pats.append(pat)\n"
                "        node = 0\n"
                "        for ch in pat:\n"
                "            node = trie[node].next.setdefault(ch, len(trie))\n"
                "            if node == len(trie):\n"
                "                trie.append(Node())\n"
                "        trie[node].out.append(idx)\n"
                "    dq = deque()\n"
                "    for ch, nxt in trie[0].next.items():\n"
                "        dq.append(nxt)\n"
                "    while dq:\n"
                "        v = dq.popleft()\n"
                "        for ch, nxt in trie[v].next.items():\n"
                "            f = trie[v].fail\n"
                "            while f and ch not in trie[f].next:\n"
                "                f = trie[f].fail\n"
                "            trie[nxt].fail = trie[f].next[ch] if ch in trie[f].next else 0\n"
                "            trie[nxt].out.extend(trie[trie[nxt].fail].out)\n"
                "            dq.append(nxt)\n"
                "    ans = [0] * n\n"
                "    node = 0\n"
                "    for ch in s:\n"
                "        while node and ch not in trie[node].next:\n"
                "            node = trie[node].fail\n"
                "        if ch in trie[node].next:\n"
                "            node = trie[node].next[ch]\n"
                "        for idx in trie[node].out:\n"
                "            ans[idx] += 1\n"
                "    print(*ans, sep='\\n')\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if "トライ" in key:
        return array_template(
            statement="N 個の単語と Q 個の接頭辞が与えられる。各接頭辞について、その接頭辞を持つ単語数を求めよ。",
            input_format="1 行目に N Q。\n続く N 行に単語。\n続く Q 行に接頭辞。",
            output_format="各接頭辞ごとに単語数を 1 行ずつ出力する。",
            constraints="1 <= N, Q <= 2 * 10^5\n文字列は英小文字",
            examples=[{"input": "3 2\napple\napp\nbanana\napp\nba", "output": "2\n1"}],
            reference_solution=(
                "class Node:\n"
                "    __slots__ = ('children', 'count')\n"
                "    def __init__(self) -> None:\n"
                "        self.children = {}\n"
                "        self.count = 0\n\n"
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n, q = map(int, input().split())\n"
                "    root = Node()\n"
                "    for _ in range(n):\n"
                "        word = input().strip()\n"
                "        node = root\n"
                "        for ch in word:\n"
                "            node = node.children.setdefault(ch, Node())\n"
                "            node.count += 1\n"
                "    out = []\n"
                "    for _ in range(q):\n"
                "        prefix = input().strip()\n"
                "        node = root\n"
                "        ok = True\n"
                "        for ch in prefix:\n"
                "            if ch not in node.children:\n"
                "                ok = False\n"
                "                break\n"
                "            node = node.children[ch]\n"
                "        out.append(str(node.count if ok else 0))\n"
                "    sys.stdout.write('\\n'.join(out))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-069":
        return array_template(
            statement="文字列 S と T が与えられる。ローリングハッシュを用いて、T が S に何回現れるかを求めよ。",
            input_format="1 行目に S。\n2 行目に T。",
            output_format="出現回数を出力する。",
            constraints="1 <= |S| <= 2 * 10^5\n1 <= |T| <= |S|",
            examples=[{"input": "aaaa\naa", "output": "3"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    s = input().strip()\n"
                "    t = input().strip()\n"
                "    base = 911382323\n"
                "    mod = 972663749\n"
                "    n = len(s)\n"
                "    m = len(t)\n"
                "    power = [1] * (n + 1)\n"
                "    prefix = [0] * (n + 1)\n"
                "    for i, ch in enumerate(s, start=1):\n"
                "        power[i] = power[i - 1] * base % mod\n"
                "        prefix[i] = (prefix[i - 1] * base + ord(ch)) % mod\n"
                "    target = 0\n"
                "    for ch in t:\n"
                "        target = (target * base + ord(ch)) % mod\n"
                "    ans = 0\n"
                "    for left in range(n - m + 1):\n"
                "        right = left + m\n"
                "        value = (prefix[right] - prefix[left] * power[m]) % mod\n"
                "        if value == target and s[left:right] == t:\n"
                "            ans += 1\n"
                "    print(ans)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-070":
        return array_template(
            statement="文字列 S と T が与えられる。KMP 法を用いて、T が S に何回現れるかを求めよ（重なりも数える）。",
            input_format="1 行目に S。\n2 行目に T。",
            output_format="出現回数を出力する。",
            constraints="1 <= |S| <= 2 * 10^5\n1 <= |T| <= |S|",
            examples=[{"input": "aaaa\naa", "output": "3"}],
            reference_solution=(
                "def build_lps(pattern: str) -> list[int]:\n"
                "    lps = [0] * len(pattern)\n"
                "    length = 0\n"
                "    i = 1\n"
                "    while i < len(pattern):\n"
                "        if pattern[i] == pattern[length]:\n"
                "            length += 1\n"
                "            lps[i] = length\n"
                "            i += 1\n"
                "        elif length:\n"
                "            length = lps[length - 1]\n"
                "        else:\n"
                "            i += 1\n"
                "    return lps\n\n"
                "def solve() -> None:\n"
                "    s = input().strip()\n"
                "    t = input().strip()\n"
                "    lps = build_lps(t)\n"
                "    i = j = ans = 0\n"
                "    while i < len(s):\n"
                "        if s[i] == t[j]:\n"
                "            i += 1\n"
                "            j += 1\n"
                "            if j == len(t):\n"
                "                ans += 1\n"
                "                j = lps[j - 1]\n"
                "        elif j:\n"
                "            j = lps[j - 1]\n"
                "        else:\n"
                "            i += 1\n"
                "    print(ans)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-071":
        return array_template(
            statement="文字列 S と T が与えられる。Z-algorithm を用いて、T が S に何回現れるかを求めよ（重なりも数える）。",
            input_format="1 行目に S。\n2 行目に T。",
            output_format="出現回数を出力する。",
            constraints="1 <= |S| <= 2 * 10^5\n1 <= |T| <= |S|",
            examples=[{"input": "aaaa\naa", "output": "3"}],
            reference_solution=(
                "def z_algorithm(text: str) -> list[int]:\n"
                "    z = [0] * len(text)\n"
                "    left = right = 0\n"
                "    for i in range(1, len(text)):\n"
                "        if i <= right:\n"
                "            z[i] = min(right - i + 1, z[i - left])\n"
                "        while i + z[i] < len(text) and text[z[i]] == text[i + z[i]]:\n"
                "            z[i] += 1\n"
                "        if i + z[i] - 1 > right:\n"
                "            left = i\n"
                "            right = i + z[i] - 1\n"
                "    z[0] = len(text)\n"
                "    return z\n\n"
                "def solve() -> None:\n"
                "    s = input().strip()\n"
                "    t = input().strip()\n"
                "    merged = t + '$' + s\n"
                "    z = z_algorithm(merged)\n"
                "    ans = 0\n"
                "    m = len(t)\n"
                "    for value in z[m + 1:]:\n"
                "        if value >= m:\n"
                "            ans += 1\n"
                "    print(ans)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-073":
        return array_template(
            statement="文字列 S が与えられる。Suffix Array を構成し、各接尾辞の開始位置を 1-indexed で出力せよ。",
            input_format="1 行目に S。",
            output_format="開始位置を空白区切りで出力する。",
            constraints="1 <= |S| <= 2000",
            examples=[{"input": "banana", "output": "6 4 2 1 5 3"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    s = input().strip()\n"
                "    order = sorted(range(len(s)), key=lambda i: s[i:])\n"
                "    print(*[i + 1 for i in order])\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-077":
        return array_template(
            statement="文字列 S が与えられる。異なる部分文字列の個数を求めよ。",
            input_format="1 行目に S。",
            output_format="異なる部分文字列の個数を出力する。",
            constraints="1 <= |S| <= 2000",
            examples=[{"input": "aba", "output": "5"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    s = input().strip()\n"
                "    seen = set()\n"
                "    for left in range(len(s)):\n"
                "        for right in range(left + 1, len(s) + 1):\n"
                "            seen.add(s[left:right])\n"
                "    print(len(seen))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if any(token in key for token in ("KMP", "Z-algorithm", "ローリングハッシュ", "Aho-Corasick", "部分文字列")):
        return array_template(
            statement="文字列 S と T が与えられる。T が S に何回現れるかを求めよ（重なりも数える）。",
            input_format="1 行目に S。\n2 行目に T。",
            output_format="出現回数を出力する。",
            constraints="1 <= |S| <= 2 * 10^5\n1 <= |T| <= |S|",
            examples=[{"input": "aaaa\naa", "output": "3"}],
            reference_solution=(
                "def build_lps(pattern: str) -> list[int]:\n"
                "    lps = [0] * len(pattern)\n"
                "    length = 0\n"
                "    i = 1\n"
                "    while i < len(pattern):\n"
                "        if pattern[i] == pattern[length]:\n"
                "            length += 1\n"
                "            lps[i] = length\n"
                "            i += 1\n"
                "        elif length:\n"
                "            length = lps[length - 1]\n"
                "        else:\n"
                "            i += 1\n"
                "    return lps\n\n"
                "def solve() -> None:\n"
                "    s = input().strip()\n"
                "    t = input().strip()\n"
                "    lps = build_lps(t)\n"
                "    i = j = ans = 0\n"
                "    while i < len(s):\n"
                "        if s[i] == t[j]:\n"
                "            i += 1\n"
                "            j += 1\n"
                "            if j == len(t):\n"
                "                ans += 1\n"
                "                j = lps[j - 1]\n"
                "        elif j:\n"
                "            j = lps[j - 1]\n"
                "        else:\n"
                "            i += 1\n"
                "    print(ans)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if "ランレングス圧縮" in key:
        return array_template(
            statement="文字列 S をランレングス圧縮し、文字と個数を交互に出力せよ。",
            input_format="1 行目に S。",
            output_format="圧縮結果を 1 行で出力する。",
            constraints="1 <= |S| <= 2 * 10^5",
            examples=[{"input": "aaabbc", "output": "a3b2c1"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    s = input().strip()\n"
                "    out = []\n"
                "    i = 0\n"
                "    while i < len(s):\n"
                "        j = i\n"
                "        while j < len(s) and s[j] == s[i]:\n"
                "            j += 1\n"
                "        out.append(f'{s[i]}{j - i}')\n"
                "        i = j\n"
                "    print(''.join(out))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if any(token in key for token in ("回文", "文字列")) or category == "文字列":
        return array_template(
            statement="文字列 S が与えられる。S が回文なら Yes、そうでなければ No を出力せよ。",
            input_format="1 行目に文字列 S。",
            output_format="Yes / No を出力する。",
            constraints="1 <= |S| <= 2 * 10^5",
            examples=[{"input": "level", "output": "Yes"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    s = input().strip()\n"
                "    print('Yes' if s == s[::-1] else 'No')\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    return None
