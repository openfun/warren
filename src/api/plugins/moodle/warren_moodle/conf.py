"""Warren configuration."""

import io

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Pydantic model for Warren's moodle configuration settings."""

    # Experience Index
    BASE_XI_URL: str = "http://localhost:8100/api/v1"

    class Config:
        """Pydantic Configuration."""

        case_sensitive = True
        env_file = ".env"
        env_file_encoding = getattr(io, "LOCALE_ENCODING", "utf8")
        env_nested_delimiter = "__"
        env_prefix = "WARREN_MOODLE_"


settings = Settings()
