import sys

from . import chunk_splitter as _chunk_splitter

sys.modules.setdefault("core.ingestion.chunk_splitter", _chunk_splitter)
