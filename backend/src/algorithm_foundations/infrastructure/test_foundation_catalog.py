import json
from pathlib import Path

import pytest

from algorithm_foundations.infrastructure.foundation_catalog import (
    AlgorithmFoundationCatalog,
)


def test_catalog_groups_are_split_by_category() -> None:
    catalog = AlgorithmFoundationCatalog()

    data = catalog.list_catalog()

    group_ids = [group["group_id"] for group in data["groups"]]
    assert len(group_ids) == len(set(group_ids))
    assert len(data["groups"]) >= 5
    assert {group["group_title"] for group in data["groups"]} >= {
        "データ構造",
        "探索",
        "動的計画法",
    }
    assert "数え上げ・整数・確率" in {
        group["group_title"] for group in data["groups"]
    }
    assert "図形・座標" in {group["group_title"] for group in data["groups"]}


def test_pick_problem_rotates_when_recent_history_covers_all_problems() -> None:
    catalog = AlgorithmFoundationCatalog()

    assert (
        catalog.pick_problem("algo-079-integration", [])["problem_id"]
        == "algo-079-integration-p1"
    )
    assert (
        catalog.pick_problem(
            "algo-079-integration",
            ["algo-079-integration-p1"],
        )["problem_id"]
        == "algo-079-integration-p2"
    )
    assert (
        catalog.pick_problem(
            "algo-079-integration",
            [
                "algo-079-integration-p3",
                "algo-079-integration-p2",
                "algo-079-integration-p1",
            ],
        )["problem_id"]
        == "algo-079-integration-p1"
    )


def test_special_units_map_to_matching_problem_templates() -> None:
    catalog = AlgorithmFoundationCatalog()

    assert (
        catalog.get_unit("algo-093-stack-basics")["problem_bank"][0]["title"]
        == "スタックの基本操作 / 基本確認"
    )
    assert (
        catalog.get_unit("algo-093-stack-basics")["problem_bank"][1]["title"]
        == "スタックの基本操作 / 実装確認"
    )
    assert (
        catalog.get_unit("algo-079-integration")["problem_bank"][0]["title"]
        == "最大公約数・最小公倍数（GCD/LCM） の総合演習 / 2unit組み合わせ確認"
    )
    assert (
        catalog.get_unit("algo-001-basic")["concept_overview"]
        == "全探索（ブルートフォース）は、ありえる候補を順番に全部試し、条件を満たすものを見つける解き方です。まずは漏れなく列挙し、1 つずつ判定する形を身につけます。"
    )
    statement = catalog.get_unit("algo-093-stack-basics")["problem_bank"][0][
        "problem_statement"
    ]
    assert "- ねらい:" not in statement
    assert "- 補足:" not in statement
    assert "スタックは、最後に入れたものから先に取り出す入れ物です。" in statement

    assert "括弧列" in catalog.get_unit("algo-093-stack-brackets")["problem_bank"][0][
        "problem_statement"
    ]
    assert "長方形" in catalog.get_unit("algo-099-prefix-sum-2d")["problem_bank"][0][
        "problem_statement"
    ]
    assert "出現回数" in catalog.get_unit("algo-102-hashmap-count")["problem_bank"][0][
        "problem_statement"
    ]
    assert "Binary Indexed Tree" in catalog.get_unit("algo-098-basic")["concept_overview"]
    assert "前計算で問い合わせを速くする" in catalog.get_unit("algo-103-basic")[
        "concept_overview"
    ]
    assert "座標圧縮" in catalog.get_unit("algo-019-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "転倒数" in catalog.get_unit("algo-020-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "二部グラフ" in catalog.get_unit("algo-032-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "深さ優先探索" in catalog.get_unit("algo-004-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "問い合わせ s, t" in catalog.get_unit("algo-024-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "ベルマンフォード法" in catalog.get_unit("algo-023-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "長さの最小値" in catalog.get_unit("algo-009-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "順列" in catalog.get_unit("algo-007-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "下に凸" in catalog.get_unit("algo-003-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "半分全列挙" in catalog.get_unit("algo-008-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "すべてのパターン" in catalog.get_unit("algo-076-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "ローリングハッシュ" in catalog.get_unit("algo-069-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "KMP 法" in catalog.get_unit("algo-070-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "Z-algorithm" in catalog.get_unit("algo-071-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "OR 畳み込み" in catalog.get_unit("algo-122-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "XOR" in catalog.get_unit("algo-116-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "バブルソート" in catalog.get_unit("algo-011-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "クイックソート" in catalog.get_unit("algo-015-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "凸包" in catalog.get_unit("algo-107-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "トポロジカル順序" in catalog.get_unit("algo-027-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "最小全域木" in catalog.get_unit("algo-025-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "クラスカル法" in catalog.get_unit("algo-026-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "木の直径" in catalog.get_unit("algo-029-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "最小共通祖先" in catalog.get_unit("algo-030-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "強連結成分" in catalog.get_unit("algo-031-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "ちょうど 1 回ずつ通る道" in catalog.get_unit("algo-033-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "オイラーツアー" in catalog.get_unit("algo-034-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "橋の本数" in catalog.get_unit("algo-035-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "Fenwick" in catalog.get_unit("algo-098-basic")["problem_bank"][0][
        "problem_statement"
    ] or "A_i に x を加算" in catalog.get_unit("algo-098-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "スパーステーブル" in catalog.get_unit("algo-103-basic")["problem_bank"][0][
        "problem_statement"
    ] or "前処理" in catalog.get_unit("algo-103-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "併合コスト" in catalog.get_unit("algo-040-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "数字 4 を含まない" in catalog.get_unit("algo-041-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "隣接頂点を同時に選ばない" in catalog.get_unit("algo-043-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "期待手数" in catalog.get_unit("algo-047-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "1 回で 1 個または 3 個" in catalog.get_unit("algo-048-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "Suffix Array" in catalog.get_unit("algo-073-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "異なる部分文字列の個数" in catalog.get_unit("algo-077-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "Ford-Fulkerson" in catalog.get_unit("algo-123-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "Dinic" in catalog.get_unit("algo-124-basic")["problem_bank"][0][
        "problem_statement"
    ]
    assert "最小カット値" in catalog.get_unit("algo-125-basic")["problem_bank"][0][
        "problem_statement"
    ]


def test_catalog_uses_fallback_theme_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fallback = tmp_path / "algo_themes.json"
    fallback.write_text(
        json.dumps(
            [
                {
                    "id": "algo-test",
                    "category": "探索",
                    "label": "テストテーマ",
                    "display_order": 1,
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "algorithm_foundations.infrastructure.foundation_catalog._DEFAULT_THEME_PATHS",
        (Path("/opt/fixtures/algo_themes.json"), fallback),
    )

    catalog = AlgorithmFoundationCatalog.__new__(AlgorithmFoundationCatalog)
    catalog._path = tmp_path / "missing.json"  # type: ignore[attr-defined]

    candidates = catalog._candidate_theme_paths()
    themes = catalog._load_themes()

    assert candidates[0] == tmp_path / "missing.json"
    assert candidates[1] == Path("/opt/fixtures/algo_themes.json")
    assert candidates[2] == fallback
    assert themes[0].id == "algo-test"
