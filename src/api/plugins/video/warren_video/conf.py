"""Warren configuration."""

import io

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Pydantic model for Warren's video configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding=getattr(io, "LOCALE_ENCODING", "utf8"),
        env_prefix="WARREN_VIDEO_",
        env_nested_delimiter="__",
        case_sensitive=True,
    )

    VIEWS_COUNT_TIME_THRESHOLD: int = 30  # seconds


settings = Settings()
