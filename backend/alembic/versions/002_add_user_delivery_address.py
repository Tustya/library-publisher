"""add user delivery_address

Revision ID: 002
Revises: 001
Create Date: 2025-02-19

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, Sequence[str], None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("delivery_address", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "delivery_address")
