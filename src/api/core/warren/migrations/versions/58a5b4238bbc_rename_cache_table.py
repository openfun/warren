"""rename-cache-table

Revision ID: 58a5b4238bbc
Revises: 2aaa9e8fc591
Create Date: 2023-09-26 07:55:28.887657

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "58a5b4238bbc"
down_revision: Union[str, None] = "2aaa9e8fc591"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("cache", "cacheentry")


def downgrade() -> None:
    op.rename_table("cacheentry", "cache")
