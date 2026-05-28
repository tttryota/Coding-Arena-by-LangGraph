import json
from io import StringIO
from unittest.mock import patch

from infrastructure.logging.setup import get_logger, setup_logging


class TestLoggingSetup:
    def test_json_output(self) -> None:
        """テスト対象: setup_logging 関数。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        setup_logging()
        output = StringIO()
        with patch("sys.stdout", output):
            logger = get_logger()
            logger.info("test_event")

        line = output.getvalue().strip()
        parsed = json.loads(line)
        assert parsed["event"] == "test_event"

    def test_timestamp_present(self) -> None:
        """テスト対象: setup_logging 関数。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        setup_logging()
        output = StringIO()
        with patch("sys.stdout", output):
            logger = get_logger()
            logger.info("test_event")

        parsed = json.loads(output.getvalue().strip())
        assert "timestamp" in parsed

    def test_log_level_present(self) -> None:
        """テスト対象: setup_logging 関数。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        setup_logging()
        output = StringIO()
        with patch("sys.stdout", output):
            logger = get_logger()
            logger.warning("warn_event")

        parsed = json.loads(output.getvalue().strip())
        assert parsed["level"] == "warning"

    def test_context_info_included(self) -> None:
        """テスト対象: setup_logging 関数。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        setup_logging()
        output = StringIO()
        with patch("sys.stdout", output):
            logger = get_logger()
            logger.info("chunk_created", source_path="study/ts/generics.md", chunks=3)

        parsed = json.loads(output.getvalue().strip())
        assert parsed["source_path"] == "study/ts/generics.md"
        assert parsed["chunks"] == 3

    def test_error_traceback_included(self) -> None:
        """テスト対象: setup_logging 関数。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        setup_logging()
        output = StringIO()
        with patch("sys.stdout", output):
            logger = get_logger()
            try:
                msg = "test error"
                raise ValueError(msg)
            except ValueError:
                logger.exception("error_event")

        parsed = json.loads(output.getvalue().strip())
        assert parsed["event"] == "error_event"
        raw = output.getvalue()
        assert "ValueError" in raw
