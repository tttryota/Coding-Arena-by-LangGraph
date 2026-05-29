"""lecture_generation ノードの Protocol 定義。"""

from __future__ import annotations

from typing import Protocol


class LectureGenerationResult(Protocol):
    @property
    def lecture_content(self) -> str: ...


class LectureGenerationLlmClient(Protocol):
    def generate_lecture(
        self, title: str, description: str,
    ) -> LectureGenerationResult: ...


__all__ = ["LectureGenerationLlmClient", "LectureGenerationResult"]
