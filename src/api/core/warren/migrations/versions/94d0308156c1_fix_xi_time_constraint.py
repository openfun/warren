"""Fix xi time constraint

Revision ID: 94d0308156c1
Revises: a113f2ab4dc9
Create Date: 2023-11-28 14:13:27.739680

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "94d0308156c1"
down_revision: Union[str, None] = "a113f2ab4dc9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_check_constraint(
        "pre-creation-update", "relation", "created_at <= updated_at"
    )
    op.create_check_constraint(
        "pre-creation-update", "experience", "created_at <= updated_at"
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("pre-creation-update", "relation", type_="check")
    op.drop_constraint("pre-creation-update", "experience", type_="check")
    # ### end Alembic commands ###
