from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-028-basic',
    title='Union-Find（素集合データ構造） の基本',
    unit_kind='foundation',
    target_skill='Union-Find（素集合データ構造） の基本',
    concept_overview='Union-Find は、要素どうしが同じグループかを管理し、グループをくっつける操作を高速に行う考え方です。まずは併合と同一グループ判定の基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-028-basic-p1',
            title='Union-Find（素集合データ構造） の基本 / 同じ連結成分かを判定する',
            problem_statement='N 個の頂点と Q 個の操作が与えられる。 `1 a b` は a と b を連結し、`2 a b` は同じ連結成分なら Yes そうでなければ No を出力せよ。',
            input_format='1 行目に N Q。\n続く Q 行に type a b。',
            output_format='type=2 の操作ごとに Yes / No を出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n1 <= a, b <= N',
            examples=[{'input': '4 5\n1 1 2\n2 1 2\n2 1 3\n1 2 3\n2 1 3', 'output': 'Yes\nNo\nYes'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    parent = list(range(n + 1))\n    size = [1] * (n + 1)\n    def find(x: int) -> int:\n        while parent[x] != x:\n            parent[x] = parent[parent[x]]\n            x = parent[x]\n        return x\n    def unite(a: int, b: int) -> None:\n        ra = find(a)\n        rb = find(b)\n        if ra == rb:\n            return\n        if size[ra] < size[rb]:\n            ra, rb = rb, ra\n        parent[rb] = ra\n        size[ra] += size[rb]\n    out = []\n    for _ in range(q):\n        t, a, b = map(int, input().split())\n        if t == 1:\n            unite(a, b)\n        else:\n            out.append('Yes' if find(a) == find(b) else 'No')\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
