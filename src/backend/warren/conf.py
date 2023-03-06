"""Warren configuration."""

import io
from functools import cached_property
from pathlib import Path
from typing import List

from elasticsearch import AsyncElasticsearch
from pydantic import BaseModel, BaseSettings


class ESClientOptions(BaseModel):
    """Pydantic model for Elasticsearch additionnal client options."""

    ca_certs: Path = None
    verify_certs: bool = None


class Settings(BaseSettings):
    """Pydantic model for Warren's global environment & configuration settings."""

    # Elasticsearch
    ES_HOSTS: List[str] | str = None
    ES_INDEX: str = "statements"
    ES_INDEX_TIMESTAMP_FIELD: str = "@timestamp"
    ES_CLIENT_OPTIONS: ESClientOptions = ESClientOptions()

    # pylint: disable=invalid-name
    @cached_property
    def ES_CLIENT(self) -> AsyncElasticsearch:
        """Get Elasticsearch client Async instance."""
        return AsyncElasticsearch(self.ES_HOSTS, **self.ES_CLIENT_OPTIONS.dict())

    class Config:
        """Pydantic Configuration."""

        case_sensitive = True
        env_file = ".env"
        env_file_encoding = getattr(io, "LOCALE_ENCODING", "utf8")
        env_nested_delimiter = "__"
        env_prefix = "WARREN_"
        keep_untouched = (
            cached_property,
        )  # https://github.com/samuelcolvin/pydantic/issues/1241


settings = Settings()
