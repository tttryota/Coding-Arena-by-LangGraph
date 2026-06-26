"""Number-theory family templates."""

from __future__ import annotations

from .common import ProblemTemplate, array_template


def build_problem_template(  # noqa: C901
    *,
    theme_id: str,
    key: str,
    category: str,
) -> ProblemTemplate | None:
    del theme_id, category
    if "エラトステネス" in key:
        return array_template(
            statement="整数 N が与えられる。1 以上 N 以下の素数の個数を求めよ。",
            input_format="1 行目に N。",
            output_format="素数の個数を出力する。",
            constraints="2 <= N <= 10^7",
            examples=[{"input": "10", "output": "4"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    n = int(input())\n"
                "    is_prime = [True] * (n + 1)\n"
                "    if n >= 0:\n"
                "        is_prime[0] = False\n"
                "    if n >= 1:\n"
                "        is_prime[1] = False\n"
                "    p = 2\n"
                "    while p * p <= n:\n"
                "        if is_prime[p]:\n"
                "            step = p * p\n"
                "            for multiple in range(step, n + 1, p):\n"
                "                is_prime[multiple] = False\n"
                "        p += 1\n"
                "    print(sum(is_prime))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if "素因数分解" in key:
        return array_template(
            statement="整数 N が与えられる。素因数分解し、`素因数 指数` を素因数の昇順で出力せよ。",
            input_format="1 行目に N。",
            output_format="各行に `p e` を出力する。",
            constraints="2 <= N <= 10^12",
            examples=[{"input": "72", "output": "2 3\n3 2"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    n = int(input())\n"
                "    out = []\n"
                "    d = 2\n"
                "    while d * d <= n:\n"
                "        if n % d == 0:\n"
                "            cnt = 0\n"
                "            while n % d == 0:\n"
                "                n //= d\n"
                "                cnt += 1\n"
                "            out.append(f'{d} {cnt}')\n"
                "        d += 1\n"
                "    if n > 1:\n"
                "        out.append(f'{n} 1')\n"
                "    print('\\n'.join(out))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if "拡張ユークリッド" in key:
        return array_template(
            statement="整数 a, b が与えられる。`ax + by = gcd(a, b)` を満たす整数 x, y の一組と `gcd(a, b)` を出力せよ。",
            input_format="1 行目に a b。",
            output_format="1 行に `g x y` を出力する。",
            constraints="1 <= a, b <= 10^18",
            examples=[{"input": "30 18", "output": "6 -1 2"}],
            reference_solution=(
                "def extgcd(a: int, b: int) -> tuple[int, int, int]:\n"
                "    if b == 0:\n"
                "        return a, 1, 0\n"
                "    g, x1, y1 = extgcd(b, a % b)\n"
                "    x = y1\n"
                "    y = x1 - (a // b) * y1\n"
                "    return g, x, y\n\n"
                "def solve() -> None:\n"
                "    a, b = map(int, input().split())\n"
                "    g, x, y = extgcd(a, b)\n"
                "    print(g, x, y)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if "モジュラ逆元" in key:
        return array_template(
            statement="整数 a, m が与えられる。a の mod m における逆元が存在すれば最小の非負整数で出力し、存在しなければ -1 を出力せよ。",
            input_format="1 行目に a m。",
            output_format="逆元、存在しなければ -1 を出力する。",
            constraints="1 <= a, m <= 10^18",
            examples=[{"input": "3 11", "output": "4"}],
            reference_solution=(
                "def extgcd(a: int, b: int) -> tuple[int, int, int]:\n"
                "    if b == 0:\n"
                "        return a, 1, 0\n"
                "    g, x1, y1 = extgcd(b, a % b)\n"
                "    return g, y1, x1 - (a // b) * y1\n\n"
                "def solve() -> None:\n"
                "    a, m = map(int, input().split())\n"
                "    g, x, _ = extgcd(a, m)\n"
                "    if g != 1:\n"
                "        print(-1)\n"
                "        return\n"
                "    print(x % m)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if "二項係数" in key:
        return array_template(
            statement="整数 n, r, p が与えられる。p を法として nCr mod p を求めよ。p は素数とする。",
            input_format="1 行目に n r p。",
            output_format="nCr mod p を出力する。",
            constraints="0 <= r <= n <= 2 * 10^5\n2 <= p <= 10^9 + 7\np は素数",
            examples=[{"input": "5 2 1000000007", "output": "10"}],
            reference_solution=(
                "def mod_pow(a: int, e: int, mod: int) -> int:\n"
                "    ans = 1\n"
                "    while e > 0:\n"
                "        if e & 1:\n"
                "            ans = ans * a % mod\n"
                "        a = a * a % mod\n"
                "        e >>= 1\n"
                "    return ans\n\n"
                "def solve() -> None:\n"
                "    n, r, mod = map(int, input().split())\n"
                "    if r < 0 or r > n:\n"
                "        print(0)\n"
                "        return\n"
                "    fact = [1] * (n + 1)\n"
                "    for i in range(1, n + 1):\n"
                "        fact[i] = fact[i - 1] * i % mod\n"
                "    inv_r = mod_pow(fact[r], mod - 2, mod)\n"
                "    inv_nr = mod_pow(fact[n - r], mod - 2, mod)\n"
                "    print(fact[n] * inv_r % mod * inv_nr % mod)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if "包除原理" in key:
        return array_template(
            statement="整数 N, A, B が与えられる。1 以上 N 以下で A または B の倍数である整数の個数を求めよ。",
            input_format="1 行目に N A B。",
            output_format="条件を満たす個数を出力する。",
            constraints="1 <= N, A, B <= 10^18",
            examples=[{"input": "20 4 6", "output": "6"}],
            reference_solution=(
                "from math import gcd\n\n"
                "def solve() -> None:\n"
                "    n, a, b = map(int, input().split())\n"
                "    lcm = a // gcd(a, b) * b\n"
                "    ans = n // a + n // b - n // lcm\n"
                "    print(ans)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if "中国剰余定理" in key or "CRT" in key:
        return array_template(
            statement=(
                "整数 a, m, b, n が与えられる。`x ≡ a (mod m)` かつ `x ≡ b (mod n)` を満たす最小の非負整数 x を求めよ。"
                " 存在しない場合は -1 を出力せよ。"
            ),
            input_format="1 行目に a m b n。",
            output_format="解があれば最小の非負整数 x、なければ -1 を出力する。",
            constraints="0 <= a < m <= 10^18\n0 <= b < n <= 10^18",
            examples=[{"input": "2 3 3 5", "output": "8"}],
            reference_solution=(
                "def extgcd(a: int, b: int) -> tuple[int, int, int]:\n"
                "    if b == 0:\n"
                "        return a, 1, 0\n"
                "    g, x1, y1 = extgcd(b, a % b)\n"
                "    return g, y1, x1 - (a // b) * y1\n\n"
                "def solve() -> None:\n"
                "    a, m, b, n = map(int, input().split())\n"
                "    g, x, _ = extgcd(m, n)\n"
                "    diff = b - a\n"
                "    if diff % g != 0:\n"
                "        print(-1)\n"
                "        return\n"
                "    mod = n // g\n"
                "    t = (diff // g * x) % mod\n"
                "    lcm = m // g * n\n"
                "    ans = (a + m * t) % lcm\n"
                "    print(ans)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if "行列累乗" in key:
        return array_template(
            statement="整数 N が与えられる。フィボナッチ数列の N 項目 F_N を 10^9+7 で割った余りで求めよ。F_0=0, F_1=1 とする。",
            input_format="1 行目に N。",
            output_format="F_N mod 1000000007 を出力する。",
            constraints="0 <= N <= 10^18",
            examples=[{"input": "10", "output": "55"}],
            reference_solution=(
                "MOD = 10 ** 9 + 7\n\n"
                "def mul(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:\n"
                "    return [\n"
                "        [\n"
                "            (a[i][0] * b[0][j] + a[i][1] * b[1][j]) % MOD\n"
                "            for j in range(2)\n"
                "        ]\n"
                "        for i in range(2)\n"
                "    ]\n\n"
                "def solve() -> None:\n"
                "    n = int(input())\n"
                "    result = [[1, 0], [0, 1]]\n"
                "    base = [[1, 1], [1, 0]]\n"
                "    while n > 0:\n"
                "        if n & 1:\n"
                "            result = mul(result, base)\n"
                "        base = mul(base, base)\n"
                "        n >>= 1\n"
                "    print(result[0][1])\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if "約数列挙" in key:
        return array_template(
            statement="整数 N が与えられる。N の正の約数を小さい順にすべて出力せよ。",
            input_format="1 行目に N。",
            output_format="正の約数を空白区切りで出力する。",
            constraints="1 <= N <= 10^12",
            examples=[{"input": "12", "output": "1 2 3 4 6 12"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    n = int(input())\n"
                "    small = []\n"
                "    large = []\n"
                "    d = 1\n"
                "    while d * d <= n:\n"
                "        if n % d == 0:\n"
                "            small.append(d)\n"
                "            if d * d != n:\n"
                "                large.append(n // d)\n"
                "        d += 1\n"
                "    print(*(small + large[::-1]))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if "オイラー" in key or "トーシェント" in key:
        return array_template(
            statement="整数 N が与えられる。オイラーの φ 関数 φ(N) を求めよ。",
            input_format="1 行目に N。",
            output_format="φ(N) を出力する。",
            constraints="1 <= N <= 10^12",
            examples=[{"input": "12", "output": "4"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    n = int(input())\n"
                "    x = n\n"
                "    ans = n\n"
                "    p = 2\n"
                "    while p * p <= x:\n"
                "        if x % p == 0:\n"
                "            while x % p == 0:\n"
                "                x //= p\n"
                "            ans -= ans // p\n"
                "        p += 1\n"
                "    if x > 1:\n"
                "        ans -= ans // x\n"
                "    print(ans)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if "メビウス" in key:
        return array_template(
            statement="整数 N が与えられる。メビウス関数 μ(N) を求めよ。",
            input_format="1 行目に N。",
            output_format="μ(N) を出力する。",
            constraints="1 <= N <= 10^12",
            examples=[{"input": "30", "output": "-1"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    n = int(input())\n"
                "    x = n\n"
                "    cnt = 0\n"
                "    p = 2\n"
                "    while p * p <= x:\n"
                "        if x % p == 0:\n"
                "            exp = 0\n"
                "            while x % p == 0:\n"
                "                x //= p\n"
                "                exp += 1\n"
                "            if exp >= 2:\n"
                "                print(0)\n"
                "                return\n"
                "            cnt += 1\n"
                "        p += 1\n"
                "    if x > 1:\n"
                "        cnt += 1\n"
                "    print(-1 if cnt % 2 else 1)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if "繰り返し二乗法" in key:
        return array_template(
            statement="整数 a, b, m が与えられる。a^b mod m を求めよ。",
            input_format="1 行目に a b m。",
            output_format="a^b mod m を出力する。",
            constraints="0 <= a, b <= 10^18\n1 <= m <= 10^9 + 7",
            examples=[{"input": "2 10 1000", "output": "24"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    a, b, m = map(int, input().split())\n"
                "    ans = 1\n"
                "    a %= m\n"
                "    while b > 0:\n"
                "        if b & 1:\n"
                "            ans = ans * a % m\n"
                "        a = a * a % m\n"
                "        b >>= 1\n"
                "    print(ans)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if any(token in key for token in ("GCD", "LCM", "素数", "約数", "CRT", "トーシェント", "メビウス")):
        return array_template(
            statement="長さ N の整数列 A が与えられる。全要素の最大公約数を求めよ。",
            input_format="1 行目に N。\n2 行目に A1..AN。",
            output_format="最大公約数を出力する。",
            constraints="1 <= N <= 2 * 10^5\n1 <= Ai <= 10^9",
            examples=[{"input": "3\n12 18 30", "output": "6"}],
            reference_solution=(
                "from math import gcd\n\n"
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    _ = int(input())\n"
                "    a = list(map(int, input().split()))\n"
                "    ans = 0\n"
                "    for value in a:\n"
                "        ans = gcd(ans, value)\n"
                "    print(ans)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    return None
