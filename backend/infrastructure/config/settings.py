from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    vault_path: Path
    sqlite_path: Path = Path("data/app.db")
    chromadb_host: str = "localhost"
    chromadb_port: int = 8000
    codex_api_url: str
    batch_interval_minutes: int = 15
    score_threshold_not_started: int = 25
    score_threshold_insufficient: int = 50
    score_threshold_partial: int = 75
    session_max_questions: int = 20
