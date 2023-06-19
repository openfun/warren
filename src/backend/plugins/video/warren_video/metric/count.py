"""Count metric for counting statements."""

from pydantic import BaseModel


class Count(BaseModel):
    """A simple count literal metric."""

    total: int

    class Config:
        """Count model configuration."""

        extra = "forbid"
