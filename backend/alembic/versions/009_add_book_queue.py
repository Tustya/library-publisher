"""add book_queue table

Revision ID: 009
Revises: 008
Create Date: 2025-02-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: Union[str, Sequence[str], None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "book_queue",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("book_id", "user_id", name="uq_book_queue_book_user"),
    )
    op.create_index("ix_book_queue_book_id", "book_queue", ["book_id"], unique=False)
    op.create_index("ix_book_queue_user_id", "book_queue", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_book_queue_user_id", table_name="book_queue")
    op.drop_index("ix_book_queue_book_id", table_name="book_queue")
    op.drop_table("book_queue")
