"""Warren configuration."""

import io
from datetime import timedelta
from pathlib import Path
from typing import List, Union

from pydantic import AnyHttpUrl, BaseModel, BaseSettings


class ESClientOptions(BaseModel):
    """Pydantic model for Elasticsearch additionnal client options."""

    ca_certs: Path = None
    verify_certs: bool = None


class Settings(BaseSettings):
    """Pydantic model for Warren's global environment & configuration settings."""

    DEBUG: bool = False

    # LRS backend
    LRS_HOSTS: Union[List[AnyHttpUrl], AnyHttpUrl]
    LRS_AUTH_BASIC_USERNAME: str
    LRS_AUTH_BASIC_PASSWORD: str

    # Warren server
    SERVER_PROTOCOL: str = "http"
    SERVER_HOST: str = "localhost"
    SERVER_PORT: int = 8100

    # API configuration
    MAX_DATETIMERANGE_SPAN: timedelta = timedelta(days=365)  # 1 year shift from since
    DEFAULT_DATETIMERANGE_SPAN: timedelta = timedelta(days=7)  # 7 days shift from until
    DATE_FORMAT: str = "YYYY-MM-DD"
    XAPI_ACTOR_IDENTIFIER_PATHS = {
        "actor.account.name",
        "actor.account.homePage",
        "actor.mbox",
        "actor.mbox_sha1sum",
        "actor.openid",
    }

    # Security
    ALLOWED_HOSTS: List[str] = [
        "http://localhost:8090",
    ]

    # Persistence
    API_DB_ENGINE: str = "postgresql"
    API_DB_HOST: str = "postgresql"
    API_DB_NAME: str = "warren-api"
    API_DB_USER: str = "fun"
    API_DB_PASSWORD: str = "pass"
    API_DB_PORT: int = 5432

    # Token
    APP_SIGNING_ALGORITHM: str
    APP_SIGNING_KEY: str

    @property
    def DATABASE_URL(self) -> str:
        """Get the database URL as required by SQLAlchemy."""
        return (
            f"{self.API_DB_ENGINE}://"
            f"{self.API_DB_USER}:{self.API_DB_PASSWORD}@"
            f"{self.API_DB_HOST}/{self.API_DB_NAME}"
        )

    # pylint: disable=invalid-name
    @property
    def SERVER_URL(self) -> str:
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
