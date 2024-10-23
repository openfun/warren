"""Warren configuration."""

import io

from pydantic import BaseSettings


class Settings(BaseSettings):
    """Pydantic model for Warren's document configuration settings."""

    class Config:
        """Pydantic Configuration."""

        case_sensitive = True
        env_file = ".env"
        env_file_encoding = getattr(io, "LOCALE_ENCODING", "utf8")
        env_nested_delimiter = "__"
        env_prefix = "WARREN_DOCUMENT_"


settings = Settings()
