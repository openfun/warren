"""Rename format Experience's attribute

Revision ID: 86ec32885672
Revises: 94d0308156c1
Create Date: 2023-11-28 14:42:25.711744

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "86ec32885672"
down_revision: Union[str, None] = "94d0308156c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("experience", "format", new_column_name="technical_datatypes")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("experience", "technical_datatypes", new_column_name="format")
    # ### end Alembic commands ###
