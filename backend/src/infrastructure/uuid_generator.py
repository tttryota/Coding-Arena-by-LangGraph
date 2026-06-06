"""全 *IdGenerator Protocol の共通 concrete 実装。"""

from __future__ import annotations

import uuid


class UuidGenerator:
    def generate(self) -> uuid.UUID:
        return uuid.uuid4()


__all__ = ["UuidGenerator"]
