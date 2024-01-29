"""fix duration strictly positive constraint

Revision ID: 77a0f0fbb8ab
Revises: 86ec32885672
Create Date: 2023-12-07 14:41:56.720633

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "77a0f0fbb8ab"
down_revision: Union[str, None] = "86ec32885672"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("positive-duration", "experience", type_="check")
    op.create_check_constraint("positive-duration", "experience", "duration > 0")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("positive-duration", "experience", type_="check")
    op.create_check_constraint("positive-duration", "experience", "duration >= 0")
    # ### end Alembic commands ###
