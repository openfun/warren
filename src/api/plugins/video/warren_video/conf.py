"""Warren configuration."""

import io

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Pydantic model for Warren's video configuration settings."""

    VIEWS_COUNT_TIME_THRESHOLD: int = 30  # seconds

    class Config:
        """Pydantic Configuration."""

        case_sensitive = True
        env_file = ".env"
        env_file_encoding = getattr(io, "LOCALE_ENCODING", "utf8")
        env_nested_delimiter = "__"
        env_prefix = "WARREN_VIDEO_"


settings = Settings()
