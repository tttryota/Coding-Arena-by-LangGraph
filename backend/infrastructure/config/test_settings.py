from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from infrastructure.config.settings import Settings


class TestSettingsDefaults:
    def test_default_values_applied(self) -> None:
        with patch.dict(
            "os.environ",
            {"VAULT_PATH": "/test/vault"},
            clear=True,
        ):
            settings = Settings(_env_file=None)

        assert settings.sqlite_path == Path("data/app.db")
        assert settings.chromadb_host == "localhost"
        assert settings.chromadb_port == 8000
        assert settings.batch_interval_minutes == 15
        assert settings.score_threshold_not_started == 25
        assert settings.score_threshold_insufficient == 50
        assert settings.score_threshold_partial == 75
        assert settings.session_max_questions == 20

    def test_required_fields_raise_on_missing(self) -> None:
        with (
            patch.dict("os.environ", {}, clear=True),
            pytest.raises(
                ValidationError,
            ),
        ):
            Settings(_env_file=None)

    def test_vault_path_missing_raises(self) -> None:
        with (
            patch.dict("os.environ", {}, clear=True),
            pytest.raises(ValidationError),
        ):
            Settings(_env_file=None)


class TestSettingsEnvOverride:
    def test_env_vars_loaded(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "VAULT_PATH": "/my/vault",
                "BATCH_INTERVAL_MINUTES": "10",
            },
            clear=True,
        ):
            settings = Settings(_env_file=None)

        assert settings.vault_path == Path("/my/vault")
        assert settings.batch_interval_minutes == 10

    def test_env_file_loaded(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("VAULT_PATH=/env/vault\n")
        with patch.dict("os.environ", {}, clear=True):
            settings = Settings(_env_file=str(env_file))

        assert settings.vault_path == Path("/env/vault")

    def test_env_var_overrides_env_file(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("VAULT_PATH=/env/vault\n")
        with patch.dict(
            "os.environ",
            {"VAULT_PATH": "/override/vault"},
            clear=True,
        ):
            settings = Settings(_env_file=str(env_file))

        assert settings.vault_path == Path("/override/vault")


class TestSettingsScoreThresholds:
    def test_custom_thresholds(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "VAULT_PATH": "/test/vault",
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
