from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-028-integration',
    title='Union-Find（素集合データ構造） の総合演習',
    unit_kind='integration',
    target_skill='Union-Find（素集合データ構造） の総合演習',
    concept_overview='Union-Find では、辺を 1 本ずつ追加しながら「その辺が新しくつなぐのか、すでに同じ成分内なのか」を判定できます。ここでは閉路を作る余分な辺の本数を数えます。',
    problem_bank=[
        problem(
            problem_id='algo-028-integration-p1',
            title='Union-Find（素集合データ構造） の総合演習 / 閉路を作る余分な辺の本数を数える',
            problem_statement='N 頂点 M 辺の無向グラフの辺が入力順に与えられる。辺を 1 本ずつ追加していったとき、追加時点ですでに両端点が同じ連結成分に属していて閉路を作る辺の本数を求めよ。',
            input_format='1 行目に N M。\n続く M 行に辺 u v。',
            output_format='余分な辺の本数を出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n1 <= u, v <= N',
            examples=[{'input': '4 4\n1 2\n2 3\n1 3\n3 4', 'output': '1'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    parent = list(range(n + 1))\n    size = [1] * (n + 1)\n\n    def find(x: int) -> int:\n        while parent[x] != x:\n            parent[x] = parent[parent[x]]\n            x = parent[x]\n        return x\n\n    def unite(a: int, b: int) -> bool:\n        ra = find(a)\n        rb = find(b)\n        if ra == rb:\n            return False\n        if size[ra] < size[rb]:\n            ra, rb = rb, ra\n        parent[rb] = ra\n        size[ra] += size[rb]\n        return True\n\n    redundant = 0\n    for _ in range(m):\n        u, v = map(int, input().split())\n        if not unite(u, v):\n            redundant += 1\n    print(redundant)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
