"""Hashmap family definitions for algorithm foundations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from .common import SpecialThemeUnitDef

SPECIAL_THEME_UNITS: Final[tuple[SpecialThemeUnitDef, ...]] = (
    ("algo-102", 0, "hashmap-exists", "存在判定をハッシュで高速化", "foundation"),
    ("algo-102", 1, "hashmap-duplicate", "既出状態をハッシュで追跡する", "foundation"),
    ("algo-102", 2, "hashmap-count", "出現回数カウント", "foundation"),
    ("algo-102", 3, "hashmap-index", "値から位置を引く対応表", "foundation"),
    ("algo-102", 4, "hashmap-match", "2配列の照合をハッシュで処理", "integration"),
)

SPECIAL_UNIT_CONCEPT_OVERVIEWS: Final[dict[str, str]] = {
    "algo-102-hashmap-exists": "値を見たかどうかをハッシュ集合に記録し、あとで同じ値があるかをすぐ調べる考え方です。探索を繰り返さず membership 判定で済ませる形を身につけます。",
    "algo-102-hashmap-duplicate": "左から順に見ながら「この値は初登場か」「前にも出たならいつだったか」を表で管理する考え方です。単なる存在判定ではなく、流れてくる列に対して seen 状態を更新し続ける感覚を身につけます。",
    "algo-102-hashmap-count": "値ごとの出現回数を連想配列にため、あとで必要な回数をすぐ取り出せるようにする考え方です。数え上げを map の更新に置き換える形を身につけます。",
    "algo-102-hashmap-index": "値をキーにして位置や番号を保存しておき、必要になったときに逆引きする考え方です。『探す』を『表から引く』に変える練習をします。",
    "algo-102-hashmap-match": "片方の情報をハッシュにまとめ、もう片方を見ながら一致や不足を判定する考え方です。照合を全組合せではなく表引きで処理する形を学びます。",
}
