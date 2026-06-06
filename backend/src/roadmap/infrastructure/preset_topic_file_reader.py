"""TopicPresetReader Protocol の ファイルベース concrete 実装。"""

from __future__ import annotations

import json
from pathlib import Path

from roadmap.domain.topic_listing_types import PresetTopicRecord


class PresetTopicFileReader:
    def __init__(self, preset_file_path: str | Path) -> None:
        self._path = Path(preset_file_path)

    def list_preset_topics(self) -> list[PresetTopicRecord]:
        if not self._path.exists():
            return []
        data = json.loads(self._path.read_text(encoding="utf-8"))
        return [
            PresetTopicRecord(
                name=item["name"],
                canonical_name=item["canonical_name"],
            )
            for item in data
        ]


__all__ = ["PresetTopicFileReader"]
