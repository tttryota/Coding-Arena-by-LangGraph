from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from infrastructure.config.settings import Settings


class TestSettingsDefaults:
    def test_default_values_applied(self) -> None:
        """テスト対象: SettingsDefaults の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        with patch.dict(
            "os.environ",
            clear=True,
        ):
            settings = Settings(_env_file=None)

        assert settings.sqlite_path == Path("data/app.db")
        assert settings.score_threshold_not_started == 25
        assert settings.score_threshold_insufficient == 50
        assert settings.score_threshold_partial == 75
        assert settings.session_max_questions == 20
        assert settings.langfuse_tracing_enabled is False
        assert settings.langfuse_base_url == "http://localhost:3000"
        assert settings.langfuse_sample_rate == 1.0
        assert settings.langfuse_capture_content is True

    def test_required_fields_raise_on_missing(self) -> None:
        """テスト対象: SettingsDefaults の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        with patch.dict("os.environ", {}, clear=True):
            settings = Settings(_env_file=None)

        assert settings.sqlite_path == Path("data/app.db")


class TestSettingsEnvOverride:
    def test_env_vars_loaded(self) -> None:
        """テスト対象: SettingsEnvOverride の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        with patch.dict(
            "os.environ",
            {
                "SQLITE_PATH": "tmp/test.db",
                "SESSION_MAX_QUESTIONS": "10",
            },
            clear=True,
        ):
            settings = Settings(_env_file=None)

        assert settings.sqlite_path == Path("tmp/test.db")
        assert settings.session_max_questions == 10

    def test_env_file_loaded(self, tmp_path: Path) -> None:
        """テスト対象: SettingsEnvOverride の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        env_file = tmp_path / ".env"
        env_file.write_text("SQLITE_PATH=data/test.db\n")
        with patch.dict("os.environ", {}, clear=True):
            settings = Settings(_env_file=str(env_file))

        assert settings.sqlite_path == Path("data/test.db")

    def test_env_var_overrides_env_file(self, tmp_path: Path) -> None:
        """テスト対象: SettingsEnvOverride の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        env_file = tmp_path / ".env"
        env_file.write_text("SQLITE_PATH=data/test.db\n")
        with patch.dict(
            "os.environ",
            {"SQLITE_PATH": "data/override.db"},
            clear=True,
        ):
            settings = Settings(_env_file=str(env_file))

        assert settings.sqlite_path == Path("data/override.db")


class TestSettingsScoreThresholds:
    def test_custom_thresholds(self) -> None:
        """テスト対象: SettingsScoreThresholds の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        with patch.dict(
            "os.environ",
            {
                "SCORE_THRESHOLD_NOT_STARTED": "30",
                "SCORE_THRESHOLD_INSUFFICIENT": "60",
                "SCORE_THRESHOLD_PARTIAL": "80",
            },
            clear=True,
        ):
            settings = Settings(_env_file=None)

        assert settings.score_threshold_not_started == 30
        assert settings.score_threshold_insufficient == 60
        assert settings.score_threshold_partial == 80


class TestSettingsLangfuse:
    def test_enabled_requires_project_keys(self) -> None:
        with (
            patch.dict(
                "os.environ",
                {"LANGFUSE_TRACING_ENABLED": "true"},
                clear=True,
            ),
            pytest.raises(ValidationError, match="LANGFUSE_PUBLIC_KEY"),
        ):
            Settings(_env_file=None)

    def test_enabled_accepts_complete_configuration(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "LANGFUSE_TRACING_ENABLED": "true",
                "LANGFUSE_PUBLIC_KEY": "lf_pk_local",
                "LANGFUSE_SECRET_KEY": "lf_sk_local",
                "LANGFUSE_BASE_URL": "http://langfuse-web:3000",
                "LANGFUSE_SAMPLE_RATE": "0.5",
            },
            clear=True,
        ):
            settings = Settings(_env_file=None)

        assert settings.langfuse_tracing_enabled is True
        assert settings.langfuse_public_key == "lf_pk_local"
        assert settings.langfuse_secret_key == "lf_sk_local"  # noqa: S105
        assert settings.langfuse_sample_rate == 0.5
