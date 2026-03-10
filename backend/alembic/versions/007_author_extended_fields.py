"""author: first_name, last_name, middle_name, pseudonym, dates, photo, short_info, biography

Revision ID: 007
Revises: 006
Create Date: 2025-02-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, Sequence[str], None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "authors",
        sa.Column("first_name", sa.String(200), nullable=True),
    )
    op.add_column(
        "authors",
        sa.Column("last_name", sa.String(200), nullable=True),
    )
    op.add_column(
        "authors",
        sa.Column("middle_name", sa.String(200), nullable=True),
    )
    op.add_column(
        "authors",
        sa.Column("pseudonym", sa.String(500), nullable=True),
    )
    op.add_column(
        "authors",
        sa.Column("birth_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "authors",
        sa.Column("death_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "authors",
        sa.Column("photo_url", sa.String(1000), nullable=True),
    )
    op.add_column(
        "authors",
        sa.Column("short_info", sa.Text(), nullable=True),
    )
    op.add_column(
        "authors",
        sa.Column("biography", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("authors", "biography")
    op.drop_column("authors", "short_info")
    op.drop_column("authors", "photo_url")
    op.drop_column("authors", "death_date")
    op.drop_column("authors", "birth_date")
    op.drop_column("authors", "pseudonym")
    op.drop_column("authors", "middle_name")
    op.drop_column("authors", "last_name")
    op.drop_column("authors", "first_name")
