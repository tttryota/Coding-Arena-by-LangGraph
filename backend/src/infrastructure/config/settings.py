from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    sqlite_path: Path = Path("data/app.db")
    score_threshold_not_started: int = 25
    score_threshold_insufficient: int = 50
    score_threshold_partial: int = 75
    session_max_questions: int = 20
