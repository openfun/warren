"""Warren configuration."""

import io
from pathlib import Path
from typing import List, Union

from pydantic import BaseModel, BaseSettings


class ESClientOptions(BaseModel):
    """Pydantic model for Elasticsearch additionnal client options."""

    ca_certs: Path = None
    verify_certs: bool = None


class Settings(BaseSettings):
    """Pydantic model for Warren's global environment & configuration settings."""

    # Elasticsearch
    ES_HOSTS: Union[List[str], str] = None
    ES_INDEX: str = "statements"
    ES_INDEX_TIMESTAMP_FIELD: str = "timestamp"
    ES_CLIENT_OPTIONS: ESClientOptions = ESClientOptions()

    # Warren server
    SERVER_PROTOCOL: str = "http"
    SERVER_HOST: str = "localhost"
    SERVER_PORT: int = 8100

    # pylint: disable=invalid-name
    @property
    def SERVER_URL(self):
        """Get the full server URL."""
        return f"{self.SERVER_PROTOCOL}://{self.SERVER_HOST}:{self.SERVER_PORT}"

    class Config:
        """Pydantic Configuration."""

        case_sensitive = True
        env_file = ".env"
        env_file_encoding = getattr(io, "LOCALE_ENCODING", "utf8")
        env_nested_delimiter = "__"
        env_prefix = "WARREN_"


settings = Settings()
