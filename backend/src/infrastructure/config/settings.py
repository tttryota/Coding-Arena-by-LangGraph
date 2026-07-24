from __future__ import annotations

from pathlib import Path

from pydantic import Field, model_validator
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
    langfuse_tracing_enabled: bool = False
    langfuse_base_url: str = "http://localhost:3000"
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_tracing_environment: str = "local"
    langfuse_release: str = "dev"
    langfuse_sample_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    langfuse_capture_content: bool = True

    @model_validator(mode="after")
    def validate_langfuse_credentials(self) -> Settings:
        """Require both project keys when tracing is explicitly enabled."""
        if self.langfuse_tracing_enabled and (
            not self.langfuse_public_key or not self.langfuse_secret_key
        ):
            msg = (
                "LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are required "
                "when LANGFUSE_TRACING_ENABLED=true"
            )
            raise ValueError(msg)
        return self
